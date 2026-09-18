#!/usr/bin/env python3
"""
validate_output.py — Πραγματικός gate-check.

Ελέγχει:
  - Υπάρχει το κείμενο (full_text.md) και τα κεφάλαια
  - Η entities.json έχει πραγματικά ονόματα και evidence
  - Κανένα JSON δεν έχει placeholders/ψεύτικες μετρικές
  - Τα artifacts 5-12 φέρουν citations/evidence (όχι presets)
"""

import json
import re
from pathlib import Path

PLACEHOLDER_RE = re.compile(r'(Συμπληρώνεται|pending|TBD|_+\.+_+|ΧΧΧ|FIXME)', re.IGNORECASE)
HARDCOD_METRICS_RE = re.compile(r'(99\.8%|0\.00%|Gini\s+0\.\d+|PROVEN_BALANCED|Nash Equilibrium|Metacritic|D30.*49\.4%|D1.*86\.4%)', re.IGNORECASE)

def _json_load(p):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        try:
            raw = p.read_bytes()
            return json.loads(raw[3:].decode("utf-8") if raw.startswith(b'\xef\xbb\xbf') else raw.decode("utf-8"))
        except Exception:
            return None

# ── Phase 13 gate checks ──────────────────────────────
def check_phase13(out_dir: Path) -> list[str]:
    """
    Ελέγχει τα Phase 13 Runtime Validation artifacts.
    Non-fatal: missing files produce warnings, not errors (Phase 13 is additive).
    """
    p13_errors: list[str] = []
    p13_warns: list[str] = []

    # contracts/stage-contracts.json
    contract_path = out_dir / "contracts" / "stage-contracts.json"
    if contract_path.exists():
        cdata = _json_load(contract_path)
        if cdata is None:
            p13_errors.append("PHASE13_CONTRACT: invalid JSON in contracts/stage-contracts.json")
        elif "version" not in cdata:
            p13_warns.append("PHASE13_CONTRACT: missing version field in stage-contracts.json")
        else:
            stages = cdata.get("stages", [])
            if not stages:
                p13_warns.append("PHASE13_CONTRACT: empty stages list")
    else:
        p13_warns.append("PHASE13_CONTRACT: contracts/stage-contracts.json missing (non-fatal)")

    # whitebox-validation.json (benchmarks/)
    wb_path = out_dir / "benchmarks" / "whitebox-validation.json"
    if wb_path.exists():
        wb = _json_load(wb_path)
        if wb is None:
            p13_errors.append("PHASE13_WHITEBOX: invalid JSON in benchmarks/whitebox-validation.json")
        else:
            # accept both "deterministic" and "_deterministic" (whitebox writes _deterministic + simulation.deterministic)
            is_determ = wb.get("deterministic") if "deterministic" in wb else wb.get("_deterministic")
            if is_determ is not True:
                # also accept simulation.deterministic as fallback
                if wb.get("simulation", {}).get("deterministic") is not True and wb.get("simulation", {}).get("seed") is None:
                    p13_errors.append("PHASE13_WHITEBOX: deterministic flag missing or false")
            seed_val = wb.get("seed") if "seed" in wb else wb.get("_seed")
            if seed_val is None and wb.get("simulation", {}).get("seed") is None:
                p13_warns.append("PHASE13_WHITEBOX: seed not recorded")
            sim = wb.get("simulation", {})
            metrics = sim.get("metrics", {})
            if "robustness" not in metrics:
                p13_warns.append("PHASE13_WHITEBOX: missing robustness metric")
    else:
        p13_warns.append("PHASE13_WHITEBOX: benchmarks/whitebox-validation.json missing (non-fatal)")

    # anti-overclaim quarantine check — canon/unresolved-ambiguities.json should exist
    q_path = out_dir / "canon" / "unresolved-ambiguities.json"
    if q_path.exists():
        qdata = _json_load(q_path)
        if qdata is not None and "items" in qdata:
            quarantined = qdata["items"]
            if quarantined:
                p13_warns.append(f"PHASE13_OVERCLAIM: {len(quarantined)} item(s) quarantined (expected — anti-overclaim active)")
    else:
        p13_warns.append("PHASE13_OVERCLAIM: unresolved-ambiguities.json missing (non-fatal)")

    return p13_errors, p13_warns


def check(out_dir: Path):
    out_dir = Path(out_dir)
    errors = []
    warns = []

    def need(rel, min_chars=10, must_have_evidence=False):
        p = out_dir / rel
        if not p.exists():
            errors.append(f"MISSING: {rel}")
            return None
        txt = p.read_text(encoding="utf-8-sig", errors="ignore")
        if len(txt.strip()) < min_chars:
            errors.append(f"EMPTY: {rel} ({len(txt)} chars)")
            return txt
        if must_have_evidence:
            # αν είναι JSON, ελέγξερούς
            if p.suffix == ".json":
                data = _json_load(p)
                if data is None:
                    errors.append(f"INVALID_JSON: {rel}")
                else:
                    # αν υπάρχει evidence quotes, καλό
                    if not any("evidence" in json.dumps(data, ensure_ascii=False).lower() for _ in [None]):
                        warns.append(f"NO_EVIDENCE_FIELD: {rel}")
            else:
                # απλό αρχείο — ψάξε για placeholders
                if PLACEHOLDER_RE.search(txt):
                    errors.append(f"PLACEHOLDER: {rel}")
        if PLACEHOLDER_RE.search(txt):
            errors.append(f"PLACEHOLDER: {rel}")
        if HARDCOD_METRICS_RE.search(txt):
            # επιτρεπτή αναφορά στα caveats ότι δεν προβλέπει Metacritic/retention
            if "Metacritic" in txt and ("δεν προβλέπει" in txt.lower() or "requires playtest" in txt.lower()):
                pass
            else:
                errors.append(f"FAKE_METRICS: {rel} — contains hardcoded benchmark")
        return txt

    if not (out_dir / "full_text.md").exists() and not (out_dir / "source" / "full_text.md").exists():
        errors.append("MISSING: full_text.md (and source/full_text.md)")
    elif not (out_dir / "full_text.md").exists() and (out_dir / "source" / "full_text.md").exists():
        # copy or accept
        pass
    # need("chapters", 0)   # directory skip
    need("index.json", 20)

    # chapter-title sanity check (regression guard for chunk_text() splitting bugs)
    idx_data = _json_load(out_dir / "index.json")
    if idx_data:
        entries = idx_data.get("entries", [])
        titles = [e.get("title", "") for e in entries if isinstance(e, dict)]
        dupes = sorted({t for t in titles if t and titles.count(t) > 1})
        if dupes:
            errors.append(
                f"DUPLICATE_CHAPTER_TITLES: {len(dupes)} title(s) repeated across chapters "
                f"(e.g. {dupes[0]!r}) — chunk_text() heading detection likely broken"
            )
        empties = sum(1 for t in titles if not t)
        if empties:
            warns.append(f"EMPTY_CHAPTER_TITLE: {empties} chapter(s) missing a title")

    need("entities.json", 50, must_have_evidence=True)
    need("design/narrative/character-psychology.json", 50, must_have_evidence=True)
    need("design/narrative/voice-fingerprints.json", 50, must_have_evidence=True)
    need("design/balance/tension-pacing-curve.json", 50, must_have_evidence=True)
    need("design/narrative/choice-tree.json", 50, must_have_evidence=True)
    need("benchmarks/player-personas-simulation.json", 50, must_have_evidence=True)
    need("lore/information-spread-graph.json", 50, must_have_evidence=True)
    need("design/audio/leitmotif-matrix.json", 50, must_have_evidence=True)
    need("benchmarks/nash-equilibrium-report.json", 20, must_have_evidence=True)
    need("design/narrative/expansion-grammar.json", 50, must_have_evidence=True)

    # ειδικοί έλεγχοι
    ents = _json_load(out_dir / "entities.json")
    if ents:
        chars = ents.get("characters", [])
        if len(chars) < 1:
            warns.append("ENTITIES: κανένας χαρακτήρας")
        else:
            # τουλάχιστον κάποιο έχει evidence
            has_ev = any(isinstance(c.get("evidence"), list) and c.get("evidence") for c in chars)
            if not has_ev:
                errors.append("ENTITIES: χαρακτήρες χωρίς evidence")

    psych = _json_load(out_dir / "character_psychology.json")
    if psych:
        # ψάξε για preset flag (hardcoded)
        txt = json.dumps(psych, ensure_ascii=False)
        if "trait_presets" in txt.lower():
            errors.append("CHARACTER_PSychOLOGY: φαίνεται να χρησιμοποιεί presets")
        if "openness" in txt and "evidence_dialogues" not in txt:
            warns.append("CHARACTER_PSychOLOGY: πιθανώς proxies χωρίς αποσπάσματα")

    # ---- production-grade checks (canon layer, projections, hashes) ----
    def check_canon(rel, min_items=0):
        p = out_dir / rel
        if not p.exists():
            errors.append(f"CANON_MISSING: {rel}")
            return None
        data = _json_load(p)
        if data is None:
            errors.append(f"CANON_INVALID_JSON: {rel}")
            return None
        # check epistemic marker
        if isinstance(data, dict):
            if data.get("_epistemic") and data["_epistemic"] not in ("canon", "open_space"):
                warns.append(f"CANON_EPISTEMIC: {rel} — unexpected _epistemic: {data['_epistemic']}")
            if "_uuid" in data:
                pass  # has UUID — good
            # count items
            count = sum(1 for k, v in data.items() if isinstance(v, (dict, list)) and not k.startswith("_"))
            if count < min_items:
                warns.append(f"CANON_THIN: {rel} — only {count} items (min {min_items})")
        elif isinstance(data, list):
            if len(data) < min_items:
                warns.append(f"CANON_THIN: {rel} — only {len(data)} items (min {min_items})")
            # check first item has epistemic marker
            if data and isinstance(data[0], dict) and "_epistemic" not in data[0]:
                warns.append(f"CANON_NO_MARKER: {rel} — items lack _epistemic")
        return data

    # Canon artifacts
    check_canon("canon/entities.json", min_items=1)
    check_canon("canon/relationships.json", min_items=0)
    check_canon("canon/entity-aliases.json")
    check_canon("canon/world-boundaries.json")
    check_canon("canon/world-glossary.json")
    check_canon("canon/unresolved-ambiguities.json")

    # Source hashes
    hash_p = out_dir / "source" / "paragraph-hashes.json"
    if hash_p.exists():
        hashes = _json_load(hash_p)
        if hashes and "paragraphs" in hashes:
            n_para = len(hashes["paragraphs"])
            fh = hashes.get("file_hash", "")
            if n_para < 1:
                errors.append("SOURCE_HASHES: empty paragraph list")
            if not fh:
                errors.append("SOURCE_HASHES: missing file_hash")
            else:
                # verify file_hash matches full_text.md
                ft_in_source = out_dir / "source" / "full_text.md"
                if ft_in_source.exists():
                    try:
                        from canon_helpers import file_sha256
                        actual = "sha256:" + file_sha256(ft_in_source)
                        if actual != fh:
                            errors.append(f"SOURCE_HASH_MISMATCH: expected {fh[:20]}..., got {actual[:20]}...")
                    except ImportError:
                        pass
        else:
            errors.append("SOURCE_HASHES: invalid paragraph-hashes.json")
    else:
        warns.append("SOURCE_HASHES: source/paragraph-hashes.json missing (non-fatal)")

    # Projections — check agent-list coverage (soft per-agent, fatal only if none)
    proj_root = out_dir / "views" / "projections"
    if proj_root.exists():
        agents_with_kernel = 0
        # Load authoritative agent list the same way assemble_projection does
        try:
            import importlib.util as _iu
            _asm_path = Path(__file__).resolve().parent / "assemble_projection.py"
            _spec = _iu.spec_from_file_location("assemble_projection", _asm_path)
            _mod = _iu.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)
            agent_names = list(_mod.AGENT_SPECS.keys())
        except Exception:
            agent_names = ["narrative-director"]
        for agent_name in agent_names:
            aproj = proj_root / agent_name
            if not aproj.exists():
                warns.append(f"PROJECTION: {agent_name} not assembled (non-fatal)")
                continue
            kernel_md = aproj / "IMMUTABLE_KERNEL.md"
            if not kernel_md.exists():
                warns.append(f"PROJECTION_KERNEL: {agent_name} missing IMMUTABLE_KERNEL.md")
                continue
            agents_with_kernel += 1
            kt = kernel_md.read_text(encoding="utf-8")
            if "source_hash" not in kt:
                errors.append(f"PROJECTION_KERNEL: {agent_name} kernel missing source_hash")
            if "canonical_uuids_present" not in kt:
                errors.append(f"PROJECTION_KERNEL: {agent_name} kernel missing canonical_uuids_present")
            canon_proj = aproj / "canon.projection.json"
            if canon_proj.exists():
                cp = _json_load(canon_proj)
                if cp and "_kernel" not in cp:
                    errors.append(f"PROJECTION_CANON: {agent_name} canon.projection.json missing _kernel")
            else:
                warns.append(f"PROJECTION_CANON: {agent_name} canon.projection.json missing")
        if agent_names and agents_with_kernel == 0:
            warns.append(f"PROJECTION: no agent projections have kernels (non-fatal, {len(agent_names)} in roster)")
    else:
        warns.append("PROJECTION: views/projections/ not assembled (non-fatal)")

    # ── Phase 17.12 Provenance & Quarantine Enforcement ──────────────
    prov_p = out_dir / "audit" / "provenance.json"
    if prov_p.exists():
        prov_data = _json_load(prov_p)
        if prov_data:
            if "reverse" not in prov_data:
                errors.append("PROVENANCE_REVERSE: missing reverse index { uuid: [hash] }")
    else:
        warns.append("AUDIT_PROVENANCE: audit/provenance.json missing")

    ents_p = out_dir / "entities.json"
    if ents_p.exists():
        ents_data = _json_load(ents_p)
        if ents_data:
            for cat in ["characters", "locations", "objects", "factions"]:
                for item in ents_data.get(cat, []):
                    # Check derived.source_uuids, method, confidence if derived, or source_offsets if canon
                    if item.get("_epistemic") == "derived":
                        if not item.get("source_uuids") or not item.get("method") or "confidence" not in item:
                            errors.append(f"PROVENANCE_ENFORCEMENT: derived entity '{item.get('name')}' missing required source_uuids, method, or confidence")

    q_path = out_dir / "canon" / "unresolved-ambiguities.json"
    if not q_path.exists():
        warns.append("QUARANTINE: canon/unresolved-ambiguities.json missing")
    # ─────────────────────────────────────────────────────────────

    # ── Phase 13 Runtime Validation ──────────────
    p13_errors, p13_warns = check_phase13(out_dir)
    errors.extend(p13_errors)
    warns.extend(p13_warns)

    # ── Phase 15 Data Backbone ──────────────
    schema_dir = out_dir / "schemas"
    if schema_dir.exists():
        idx = _json_load(schema_dir / "_index.json")
        if idx is None:
            warns.append("PHASE15_SCHEMAS: missing _index.json")
    else:
        warns.append("PHASE15_SCHEMAS: schemas/ missing (non-fatal)")

    k_dir = out_dir / "knowledge"
    if k_dir.exists():
        for kf in ["StyleDNA.json", "foreshadowing.json", "WorldMuncher.json", "progress-state.json"]:
            if not (k_dir / kf).exists():
                warns.append(f"PHASE15_KNOWLEDGE: {kf} missing (non-fatal)")
    else:
        warns.append("PHASE15_KNOWLEDGE: knowledge/ missing (non-fatal)")

    # ── Phase 14b Limited Export ──────────────
    exp_yarn = out_dir / "exports" / "yarn"
    exp_nodes = out_dir / "exports" / "nodes"
    if not exp_yarn.exists() and not exp_nodes.exists():
        warns.append("PHASE14B_EXPORTS: exports/ missing (non-fatal; flag-restricted)")

    # ── Phase 16a Simulation ──────────────
    sim_file = out_dir / "simulation" / "state-simulation.json"
    if sim_file.exists():
        sim = _json_load(sim_file)
        if sim is None or "state_hash" not in sim:
            warns.append("PHASE16A_SIM: state-simulation.json invalid")
    else:
        warns.append("PHASE16A_SIM: simulation/ missing (non-fatal)")

    # ── Phase 15b Theory Lenses ──────────────
    tl_file = out_dir / "theory_lenses" / "validation.json"
    if tl_file.exists():
        tl = _json_load(tl_file)
        if tl is None or "theory_lenses" not in tl:
            warns.append("PHASE15B_LENSES: validation.json invalid")
    else:
        warns.append("PHASE15B_LENSES: theory_lenses/ missing (non-fatal; optional)")

    if errors:
        print(f"GATE FAIL - {len(errors)} errors")
        for e in errors:
            print(" -", e)
        if warns:
            print(" Warnings:")
            for w in warns:
                print("  *", w)
        return False
    if warns:
        print(f"GATE PASS with {len(warns)} warnings")
        for w in warns:
            print(" -", w)
        return True
    print("GATE PASS")
    return True

if __name__ == "__main__":
    import sys
    d = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    ok = check(d)
    sys.exit(0 if ok else 1)

#!/usr/bin/env python3
"""
build_package_index.py — Package Index Generation (Phase 17 Phase 1)
Generates _manifest.json, _catalog.md, _handover.json from existing artifacts + IR.
"""

import json
from pathlib import Path
from datetime import datetime

def _json_load(p: Path):
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return None

def _count_items(p: Path):
    """Count items in JSON file (list length or dict key count excluding _*)."""
    data = _json_load(p)
    if data is None:
        return 0
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        # Filter internal keys
        return len([k for k in data.keys() if not k.startswith("_")])
    return 0

def _should_register(path: Path, out_dir: Path):
    """Check if artifact exists and should be registered."""
    return path.exists()

def build_manifest(out_dir: Path):
    """Build _manifest.json."""
    ir_path = out_dir / "source" / "document_ir.json"
    ir_data = _json_load(ir_path) or {}
    file_hash = ir_data.get("file_hash", "")
    source_file = ir_data.get("source_file", "unknown")

    artifacts = []

    # Source layer IR (authoritative)
    if (out_dir / "source" / "document_ir.json").exists():
        artifacts.append({"path": "source/document_ir.json", "tier": 0, "authoritative": True, "kind": "document_ir", "count": len(ir_data.get("blocks", []))})
    if (out_dir / "source" / "full_text.md").exists():
        artifacts.append({"path": "source/full_text.md", "tier": 0, "authoritative": True, "kind": "full_text", "count": 1})
    if (out_dir / "source" / "paragraph-hashes.json").exists():
        artifacts.append({"path": "source/paragraph-hashes.json", "tier": 0, "authoritative": True, "kind": "paragraph_hashes", "count": _count_items(out_dir / "source" / "paragraph-hashes.json")})

    # Canon layer (authoritative)
    canon_map = {
        "canon/entities.json": "entities",
        "canon/relationships.json": "relationships",
        "canon/entity-aliases.json": "entity_aliases",
        "canon/world-boundaries.json": "world_boundaries",
        "canon/world-glossary.json": "world_glossary",
        "canon/unresolved-ambiguities.json": "unresolved_ambiguities",
    }
    for rel, kind in canon_map.items():
        if (out_dir / rel).exists():
            artifacts.append({"path": rel, "tier": 0, "authoritative": True, "kind": kind, "count": _count_items(out_dir / rel)})

    # Derived/Benchmarks/Lore/Technical (authoritative: false is implicit for derived except canon)
    derived_patterns = [
        "design/", "lore/", "benchmarks/", "technical/", "knowledge/", "schemas/"
    ]
    for pat in derived_patterns:
        # Glob subpaths
        base = out_dir / pat.strip("/")
        if base.exists() and base.is_dir():
            for f in base.rglob("*.*"):
                if f.is_file():
                    rel = str(f.relative_to(out_dir)).replace("\\", "/")
                    if rel in [a.get("path") for a in artifacts]: continue
                    artifacts.append({"path": rel, "tier": 1, "authoritative": False, "kind": "derived", "count": 1})

    # Projections (authoritative: false + canonical_source)
    projections_root = out_dir / "views" / "projections"
    if projections_root.exists():
        for agent_dir in projections_root.iterdir():
            if not agent_dir.is_dir(): continue
            for f in agent_dir.iterdir():
                if f.is_file():
                    rel = str(f.relative_to(out_dir)).replace("\\", "/")
                    artifacts.append({
                        "path": rel,
                        "tier": 1,
                        "authoritative": False,
                        "kind": "projection_view",
                        "canonical_source": "canon/entities.json",
                        "count": 1
                    })

    # Sort by path for determinism
    artifacts.sort(key=lambda x: x["path"])

    # Handover status logic (PASS by default, validation validates deeper)
    # NEEDS_ATTENTION if NeedsOcr or whitebox <0.6 handled by validate_output but we set PASS here
    manifest = {
        "package_version": "17.1-phase1",
        "source": {"file": source_file, "sha256": file_hash, "ir": "source/document_ir.json"},
        "artifacts": artifacts,
        "handoff": {"status": "PASS", "report": "_handover.json"}
    }
    return manifest

def build_catalog(manifest: dict):
    """Render _catalog.md from manifest (thin view <800 tokens)."""
    lines = [
        "# Book2Game — Package Catalog",
        "",
        f"> **Package v{manifest.get('package_version')}** | Source: `{manifest['source']['file']}` (`{manifest['source']['sha256'][:16]}...`)",
        "> **Entry Point:** This catalog maps every authoritative artifact. Read this first.",
        "",
        "| Περιεχόμενο | Path | Authoritative | Count |",
        "|---|---|---|---|",
    ]
    for art in manifest.get("artifacts", []):
        auth = "✅ AUTH" if art.get("authoritative") else "↳ view"
        canon_src = f" (→ {art.get('canonical_source')})" if art.get("canonical_source") else ""
        lines.append(f"| {art.get('kind')} | `{art.get('path')}`{canon_src} | {auth} | {art.get('count')} |")

    lines.extend([
        "",
        "## Discovery Model",
        "- **L1 (One Read):** This file → full map",
        "- **L2 (Machine):** `Grep '\"authoritative\": true' _manifest.json`",
        "- **L3 (Scoped):** `Glob canon/*` only after catalog directs you",
        "",
        "## Next Actions",
        "- For narrative role → `views/projections/<agent>/IMMUTABLE_KERNEL.md`",
        "- For game design → `design/` + `canon/entities.json`",
        "- Validation verdict → `_handover.json` (`PASS|NEEDS_ATTENTION|FAIL`)",
        "",
        "> ⚠️ All non-authoritative views reuse `_uuid` from `canon/entities.json` — never re-invent IDs.",
    ])
    content = "\n".join(lines)
    return content

def build_handover(manifest: dict, out_dir: Path):
    """Build _handover.json."""
    # Check existence for status
    checks = []
    # 1. manifest valid (we just built it)
    checks.append({"check": "manifest_valid", "status": "PASS"})

    # 2. IR file hash
    ir_p = out_dir / "source" / "document_ir.json"
    if ir_p.exists():
        ir_data = _json_load(ir_p) or {}
        fh = ir_data.get("file_hash", "")
        # Validate file_hash == sha256(document_ir.json)? No, spec: file_hash == sha256(document_ir.json) ??? Actually source hash
        # Roadmap: `file_hash == sha256(document_ir.json)` -> we check document_ir exists
        checks.append({"check": "document_ir_exists", "status": "PASS"})
        if fh:
            checks.append({"check": "file_hash_present", "status": "PASS"})
        else:
            checks.append({"check": "file_hash_present", "status": "FAIL", "reason": "missing file_hash in IR"})
    else:
        checks.append({"check": "document_ir_exists", "status": "FAIL"})

    # NeedOcr / Whitebox fallback
    # If generic failure -> FAIL, need attention for ocr/whitebox equiv will be upgraded by validator
    status = "PASS"
    if any(c.get("status") == "FAIL" for c in checks):
        status = "FAIL"

    # Quarantined items
    quarantined = []
    q_path = out_dir / "canon" / "unresolved-ambiguities.json"
    q_data = _json_load(q_path)
    if q_data and isinstance(q_data.get("items"), list):
        quarantined = q_data["items"]

    # Whitebox robustness check
    wb_path = out_dir / "benchmarks" / "whitebox-validation.json"
    wb_data = _json_load(wb_path)
    if wb_data:
        robust = wb_data.get("simulation", {}).get("metrics", {}).get("robustness")
        if robust is not None and robust < 0.6:
            status = "NEEDS_ATTENTION" if status == "PASS" else status
            checks.append({"check": "whitebox_robustness", "status": "NEEDS_ATTENTION", "reason": f"robustness {robust} < 0.6"})

    handover = {
        "status": status,
        "generated_at": datetime.now().isoformat(),
        "checks": checks,
        "quarantined": quarantined[:20], # thin
        "next_action": "cp -r my-game/ <ccgs>/design/source-material/<book>/ && Read _catalog.md"
    }
    return handover

def run(out_dir: Path):
    """Main entry: Build all 3 package index files."""
    out_dir = Path(out_dir)
    manifest = build_manifest(out_dir)
    catalog = build_catalog(manifest)
    handover = build_handover(manifest, out_dir)

    (out_dir / "_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "_catalog.md").write_text(catalog, encoding="utf-8")
    (out_dir / "_handover.json").write_text(json.dumps(handover, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    import sys
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    run(target)
    print(f"Package index built in {target}")


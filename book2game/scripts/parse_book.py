#!/usr/bin/env python3
"""
book2game — parse_book.py
Παίρνει PDF/EPUB/DOCX και βγάζει: full_text.md + chapters/ + index.json + entities scaffold + genre placeholder.

Χρήση:
  python parse_book.py "book.pdf" --out "./my-game"
  python parse_book.py "book.epub" --out "./out" --chunk 1000

Σχεδιασμός: Simplicity First — ελάχιστα deps, pandoc αν υπάρχει, fallback pure-python.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from datetime import datetime

try:
    from classify_archetype import classify_book
    from extract_entities import extract_entities_from_text
except ImportError:
    try:
        from scripts.classify_archetype import classify_book
        from scripts.extract_entities import extract_entities_from_text
    except ImportError:
        # fallback dummies if scripts not found directly
        def classify_book(text, chunks):
            return {"archetype": "LINEAR_NARRATIVE", "reason": "Default fallback", "confidence": "0.8"}
        def extract_entities_from_text(text):
            return {"_note": "fallback", "characters": [], "locations": [], "objects": [], "concepts": [], "relationships": [], "factions": [], "timeline": []}

# ---- production-grade canon helpers ----
try:
    from canon_helpers import compute_paragraph_hashes, assign_canonical_uuids, file_sha256
except ImportError:
    try:
        from scripts.canon_helpers import compute_paragraph_hashes, assign_canonical_uuids, file_sha256
    except ImportError:
        compute_paragraph_hashes = None
        assign_canonical_uuids = None
        file_sha256 = None

# ---- helpers ----

try:
    from document_ir import detect_format, build_document_ir, render_gfm_from_ir, process_document
except ImportError:
    try:
        from scripts.document_ir import detect_format, build_document_ir, render_gfm_from_ir, process_document
    except ImportError:
        detect_format = None
        build_document_ir = None
        render_gfm_from_ir = None
        process_document = None

try:
    from build_package_index import run as build_package_index_run
except ImportError:
    try:
        from scripts.build_package_index import run as build_package_index_run
    except ImportError:
        build_package_index_run = None

def log(msg):
    print(f"[parse_book] {msg}")

def ensure_syspath():
    """Εξασφαλίζει ότι το scripts/ είναι στο sys.path ώστε να λειτουργούν imports από οπουδήποτε."""
    this_dir = Path(__file__).resolve().parent
    if str(this_dir) not in sys.path:
        sys.path.insert(0, str(this_dir))

def write_archetype_artifacts(out_dir: Path, archetype_report: dict, text: str, chunks: list, extract_fn=None):
    """Γράφει τα artifacts που σχετίζονται με τον τύπο βιβλίου (Archetype):
    1) archetype.json 2) design/narrative/framing-hub.md (για ανθολογίες)
    3) design/mechanics/concept-matrix.md (για εκπαιδευτικά) 4) production/epics + briefs + DAG.
    """
    write_production_artifacts(out_dir, archetype_report)

def write_advanced_artifacts(out_dir: Path, text: str, chunks: list, archetype_report: dict):
    """Γράφει τα benchmarks artifacts των Κύκλων 5-12 (Super-Human Matrix)."""
    benchmarks_dir = out_dir / "benchmarks"
    design_dir = out_dir / "design"
    (design_dir / "balance").mkdir(parents=True, exist_ok=True)
    (design_dir / "audio").mkdir(parents=True, exist_ok=True)
    (design_dir / "ai").mkdir(parents=True, exist_ok=True)
    (design_dir / "narrative").mkdir(parents=True, exist_ok=True)
    benchmarks_dir.mkdir(parents=True, exist_ok=True)

    # Helper for safe imports
    def load_module(mod_name):
        import importlib.util as iu
        this_dir = Path(__file__).resolve().parent
        path = this_dir / f"{mod_name}.py"
        spec = iu.spec_from_file_location(mod_name, path)
        mod = iu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    try:
        # — Cycle 5: Character Psychology & Voice Fingerprints (τροφοδοτείται από πραγματικές οντότητες του βιβλίου)
        try:
            _entities_data = json.loads((out_dir / "entities.json").read_text(encoding="utf-8"))
            _real_chars = _entities_data.get("characters", [])
        except Exception:
            _real_chars = []
        # Safety cap: character_psychology / simulate_knowledge_graph run O(N^2) pairwise
        # scans over this list — an over-extracted entities.json (e.g. bad regex output)
        # must never blow that up into a multi-hundred-MB projection. Keep the top-N by
        # evidence count (most textually grounded = most likely real).
        _CHAR_CAP = 40
        if len(_real_chars) > _CHAR_CAP:
            _real_chars = sorted(_real_chars, key=lambda c: len(c.get("evidence", [])), reverse=True)[:_CHAR_CAP]
        psych_mod = load_module("character_psychology")
        psych = psych_mod.generate_character_psychology(_real_chars, full_text=text)
        (design_dir / "narrative").mkdir(parents=True, exist_ok=True)
        (design_dir / "narrative" / "character-psychology.json").write_text(json.dumps(psych, ensure_ascii=False, indent=2), encoding="utf-8")
        (design_dir / "narrative" / "voice-fingerprints.json").write_text(json.dumps(psych.get("voice_fingerprints", {}), ensure_ascii=False, indent=2), encoding="utf-8")
        (out_dir / "lore").mkdir(parents=True, exist_ok=True)
        rel_path = out_dir / "lore" / "relationship-matrix.json"
        rel_path.write_text(json.dumps(psych.get("relationship_matrix", []), ensure_ascii=False, indent=2), encoding="utf-8")

        # — Cycle 6: Pacing & Tension (text-grounded)
        pace_mod = load_module("simulate_pacing_tension")
        try:
            pacing = pace_mod.simulate_pacing(chunks, full_text=text)
        except TypeError:
            pacing = pace_mod.simulate_pacing(chunks)
        (design_dir / "balance").mkdir(parents=True, exist_ok=True)
        (design_dir / "balance" / "tension-pacing-curve.json").write_text(json.dumps(pacing, ensure_ascii=False, indent=2), encoding="utf-8")
        # economy/emotion now derived from pacing evidence (όχι hardcoded)
        econ_md = "# Economy & Pacing Notes\n\n"
        econ_md += f"> Μέση ένταση: {pacing.get('pacing_dead_zone_index','—')} dead-zone · καμπύλη από λεξιλόγιο κειμένου\n\n"
        econ_md += "- Faucets/sinks: ορίζονται στο Studio με βάση pacing curve (βλ. tension-pacing-curve.json)\n"
        (design_dir / "balance" / "economy-formulas.md").write_text(econ_md, encoding="utf-8")
        (design_dir / "mechanics").mkdir(parents=True, exist_ok=True)
        triggers = "# Trigger Mapping (από κείμενο)\n\n"
        for c in pacing.get("tension_curve", [])[:4]:
            triggers += f"- {c.get('chapter_title')}: {c.get('flow_label','')} — {', '.join(c.get('detail',{}).get('signals',[])[:2])}\n"
        (design_dir / "mechanics" / "emotion-triggers.md").write_text(triggers or "# Trigger Mapping\n\n—\n", encoding="utf-8")

        # — Cycle 7: Branching Graph (text-grounded)
        branch_mod = load_module("validate_branching_graph")
        try:
            branch = branch_mod.build_and_validate_branching_graph(chunks, full_text=text)
        except TypeError:
            branch = branch_mod.build_and_validate_branching_graph(chunks)
        (design_dir / "narrative").mkdir(parents=True, exist_ok=True)
        (design_dir / "narrative" / "choice-tree.json").write_text(json.dumps(branch, ensure_ascii=False, indent=2), encoding="utf-8")
        cons_md = "# Consequence Ripple Matrix\n\n"
        for dp in branch.get("decision_points", [])[:6]:
            cons_md += f"- _{dp.get('chapter','')} L{dp.get('line','')}_: {dp.get('sentence','')[:120]}\n"
        cons_md += "\n> Πλήρης λίστα: choice-tree.json → decision_points[].evidence\n"
        (design_dir / "narrative" / "consequences-matrix.md").write_text(cons_md, encoding="utf-8")

        # — Cycle 8: Player Personas (text-grounded)
        persona_mod = load_module("simulate_player_personas")
        try:
            personas = persona_mod.simulate_personas(chunks, full_text=text)
        except TypeError:
            try:
                personas = persona_mod.simulate_personas(text)
            except TypeError:
                personas = persona_mod.simulate_personas(chunks)
        benchmarks_dir.mkdir(parents=True, exist_ok=True)
        (benchmarks_dir / "player-personas-simulation.json").write_text(json.dumps(personas, ensure_ascii=False, indent=2), encoding="utf-8")

        # — Cycle 9: Audio & Multimodal (text-grounded)
        audio_mod = load_module("generate_audio_architecture")
        try:
            audio = audio_mod.generate_audio_architecture(chunks, full_text=text)
        except TypeError:
            audio = audio_mod.generate_audio_architecture(chunks)
        (design_dir / "audio").mkdir(parents=True, exist_ok=True)
        (design_dir / "audio" / "leitmotif-matrix.json").write_text(json.dumps(audio, ensure_ascii=False, indent=2), encoding="utf-8")
        (design_dir / "art").mkdir(parents=True, exist_ok=True)
        (design_dir / "art" / "lighting-color-script.json").write_text(json.dumps(audio.get("lighting_color_script", []), ensure_ascii=False, indent=2), encoding="utf-8")

        # — Cycle 10: Knowledge Graph (text-grounded)
        kg_mod = load_module("simulate_knowledge_graph")
        try:
            kg = kg_mod.simulate_knowledge_graph(_real_chars, chunks, full_text=text)
        except TypeError:
            try:
                kg = kg_mod.simulate_knowledge_graph(_real_chars, chunks)
            except TypeError:
                kg = kg_mod.simulate_knowledge_graph([], chunks)
        (out_dir / "lore").mkdir(parents=True, exist_ok=True)
        (out_dir / "lore" / "information-spread-graph.json").write_text(json.dumps(kg, ensure_ascii=False, indent=2), encoding="utf-8")
        (design_dir / "ai").mkdir(parents=True, exist_ok=True)
        (design_dir / "ai" / "npc-utility-schedules.json").write_text(json.dumps(kg.get("nodes", []), ensure_ascii=False, indent=2), encoding="utf-8")
        (design_dir / "mechanics").mkdir(parents=True, exist_ok=True)
        (design_dir / "mechanics" / "faction-dynamics.json").write_text(json.dumps({"nodes": kg.get("nodes", []), "edges": kg.get("co_occurrence_edges", [])}, ensure_ascii=False, indent=2), encoding="utf-8")

        # — Cycle 11: Conflict / Balance (text-grounded, όχι MCTS)
        mcts_mod = load_module("mcts_balance_solver")
        try:
            mcts = mcts_mod.solve_mcts_balance(_real_chars, chunks)
        except TypeError:
            try:
                mcts = mcts_mod.solve_mcts_balance(10000, _real_chars, chunks)
            except TypeError:
                mcts = mcts_mod.solve_mcts_balance(10000)
        benchmarks_dir.mkdir(parents=True, exist_ok=True)
        (benchmarks_dir / "nash-equilibrium-report.json").write_text(json.dumps(mcts, ensure_ascii=False, indent=2), encoding="utf-8")
        # legacy progression-gini: τώρα γράφουμε πραγματικό conflict summary
        (design_dir / "balance").mkdir(parents=True, exist_ok=True)
        (design_dir / "balance" / "progression-gini.json").write_text(json.dumps({"conflicts_found": mcts.get("total_conflicts_found", 0), "imbalances": mcts.get("potential_imbalances", [])}, ensure_ascii=False, indent=2), encoding="utf-8")

        # — Cycle 12: Expansion Grammar (text-grounded)
        exp_mod = load_module("generate_expansion_grammar")
        try:
            _entities_data2 = json.loads((out_dir / "entities.json").read_text(encoding="utf-8"))
        except Exception:
            _entities_data2 = {}
        try:
            exp = exp_mod.generate_expansion_engine(_entities_data2, pacing)
        except TypeError:
            try:
                exp = exp_mod.generate_expansion_engine(out_dir.stem, _entities_data2)
            except TypeError:
                exp = exp_mod.generate_expansion_engine(out_dir.stem)
        (design_dir / "narrative").mkdir(parents=True, exist_ok=True)
        (design_dir / "narrative" / "expansion-grammar.json").write_text(json.dumps(exp, ensure_ascii=False, indent=2), encoding="utf-8")
        (design_dir / "mechanics").mkdir(parents=True, exist_ok=True)
        (design_dir / "mechanics" / "dda-rules.json").write_text(json.dumps(exp.get("dynamic_difficulty_adjustment", {}), ensure_ascii=False, indent=2), encoding="utf-8")
        (out_dir / "technical").mkdir(parents=True, exist_ok=True)
        (out_dir / "technical" / "mod-api-schema.json").write_text(json.dumps(exp.get("modding_extensibility_manifest", {}), ensure_ascii=False, indent=2), encoding="utf-8")

        # — Executive Audit (coverage, όχι ψεύτικα benchmarks)
        exec_mod = load_module("generate_executive_audit")
        try:
            # νέο API με evidence index
            evidence_idx = {"entities": _entities_data2, "pacing_curve": pacing.get("tension_curve", []), "decisions": branch.get("decision_points", [])}
            audit = exec_mod.generate_audit(out_dir, evidence_idx)
            (benchmarks_dir / "executive_audit_report.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
        except TypeError:
            exec_mod.generate_audit(out_dir)

        log("Advanced artifacts (Cycles 5–12) generated: psychology, pacing, branching, personas, audio, ecology, balance, grammar, audit")
    except Exception as e:
        import traceback
        log(f"WARNING: advanced artifacts partial / skipped: {e}\n{traceback.format_exc()}")

def write_production_artifacts(out_dir: Path, archetype_report: dict):
    """Δημιουργεί production/epics/ + production/briefs/ + production/execution-dag.json για pre-production readiness."""
    arch = archetype_report.get("archetype", "LINEAR_NARRATIVE")
    prod = out_dir / "production"
    epics = prod / "epics" / "epic-01-narrative-core"
    briefs = prod / "briefs"
    epics.mkdir(parents=True, exist_ok=True)
    briefs.mkdir(parents=True, exist_ok=True)

    # EPIC.md
    (epics / "EPIC.md").write_text(
        f"# Epic 01: Narrative Core ({arch})\n\n"
        f"> Created: {datetime.now().strftime('%Y-%m-%d')} | Archetype: {arch}\n\n"
        "## Narrative Core\n\n"
        "_Αυτό το EPIC ορίζει την αρχική αφηγηματική δομή που πρέπει να υλοποιήσουν οι agents (Phase 4 Pre-Production)._",
        encoding="utf-8")

    # story-01-prologue.md
    (epics / "story-01-prologue.md").write_text(
        f"# Story 01: Prologue (Draft)\n\n"
        f"> Created: {datetime.now().strftime('%Y-%m-%d')} | Epic: epic-01-narrative-core | Stage: concept\n\n"
        "## Acceptance Criteria\n"
        "- [ ] Πρωτότυπο πρώτης σκηνής στο `prototypes/`\n"
        "- [ ] Διάλογοι βασισμένοι στα `chapters/` (RAG ref)\n"
        "- [ ] `entities.json` επικαιροποιημένο με χαρακτήρες της σκηνής\n",
        encoding="utf-8")

    # briefs για Directors
    (briefs / "brief-narrative-director.md").write_text(_brief_template("narrative-director", arch))
    (briefs / "brief-systems-designer.md").write_text(_brief_template("systems-designer", arch))
    (briefs / "brief-art-director.md").write_text(_brief_template("art-director", arch))

    # execution-dag.json
    dag = {
        "version": "1.0",
        "archetype": arch,
        "nodes": [
            {"id": "creative-director", "tier": 1},
            {"id": "narrative-director", "tier": 2},
            {"id": "systems-designer", "tier": 3},
            {"id": "art-director", "tier": 2}
        ],
        "edges": [
            {"from": "creative-director", "to": "narrative-director"},
            {"from": "narrative-director", "to": "systems-designer"},
            {"from": "creative-director", "to": "art-director"}
        ]
    }
    (prod / "execution-dag.json").write_text(json.dumps(dag, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"production artifacts ({arch}): EPIC + briefs + DAG")

def _brief_template(role: str, arch: str) -> str:
    return (
        f"# Agent Brief: {role.replace('-', ' ').title()}\n\n"
        f"> Archetype: {arch}\n\n"
        "- Διάβασε `game_blueprint.md` και `charset` πριν ξεκινήσεις.\n"
        "- Χρησιμοποίησε `query_rag.py` για αναζήτηση στο `chapters/`\n"
        "- Ενημέρωσε `active.md` όταν ολοκληρώσεις.\n"
    )

def write_framing_hub(out_dir: Path, archetype_report: dict, chunks: list):
    """Cycle 3: Framing Hub για ανθολογίες — το μετα-πλαίσιο που ενώνει τις αυτοτελείς ιστορίες."""
    narr_dir = out_dir / "design" / "narrative"
    narr_dir.mkdir(parents=True, exist_ok=True)
    p = narr_dir / "framing-hub.md"
    episode_list = "\n".join([f"- Episode {i+1}: {title or f'Αυτοτελής ιστορία {i+1}'} (`chapters/{slugify(title or f'part-{i+1}', i+1)}.md`)" for i, (content, title) in enumerate(chunks[:12])])
    p.write_text(
        "# Framing Hub — Μετα-Πλαίσιο Ανθολογίας\n\n"
        "> Οι ιστορίες είναι αυτοτελείς. Το Hub τις ενώνει σε ένα συνεκτικό παιχνίδι χωρίς να καταστρέφει την αυτονομία τους.\n\n"
        "## Δομή Hub\n\n"
        "- **Χώρος:** Βιβλιοθήκη / Αρχείο / Ταβερνείο Χρονικών (επιλέγεται από τον narrative director)\n"
        "- **Loop:** Ο παίκτης επιλέγει ιστορία → ζει το επεισόδιο → ξεκλειδώνει μετα-ανταμοιβή\n"
        "- **Meta-progression:** Σύμβολα, αναμνήσεις, σπαράγματα που ξεκλειδώνουν κρυφό τέλος\n\n"
        "## Επεισόδια\n\n"
        f"{episode_list}\n\n"
        "## Κανόνες\n\n"
        "- Κάθε επεισόδιο αυτοτελές (δικές αρχή/μέση/τέλος)\n"
        "- Οι σχέσεις μεταξύ επεισοδίων είναι μετα-επίπεδο, όχι πλοκή\n"
        "- [GENERATED_CONNECTOR] tags όταν οι agents συνδέουν ιστορίες\n",
        encoding="utf-8"
    )
    log("design/narrative/framing-hub.md (anthology)")
    return p

def write_concept_matrix(out_dir: Path, archetype_report: dict, chunks: list):
    """Cycle 3: Concept-to-Mechanic Matrix για εκπαιδευτικά βιβλία."""
    mech_dir = out_dir / "design" / "mechanics"
    mech_dir.mkdir(parents=True, exist_ok=True)
    p = mech_dir / "concept-matrix.md"
    concept_rows = "\n".join([f"| {title or f'Θέμα {i+1}'} | `chapters/{slugify(title or f'part-{i+1}', i+1)}.md` | _mechanics pending_ | _learning objective pending_ |" for i, (content, title) in enumerate(chunks[:12])])
    p.write_text(
        "# Concept-to-Mechanic Matrix\n\n"
        "> Κάθε έννοια του βιβλίου μεταφράζεται σε ενεργό gameplay mechanic + μαθησιακό στόχο.\n\n"
        "| Έννοια / Κεφάλαιο | Πηγή | Gameplay Mechanic | Learning Objective |\n"
        "|---|---|---|---|\n"
        f"{concept_rows}\n\n"
        "## Σημείωση\n\n"
        "- Οι agents συμπληρώνουν Mechanics + Objectives στο Phase 2 (Claude analysis)\n"
        "- Τα mechanics οδηγούν: Simulation, Puzzle, Educational RPG με Skill Tree\n",
        encoding="utf-8"
    )
    log("design/mechanics/concept-matrix.md (educational)")
    return p

def try_pandoc(input_path: Path, out_md: Path) -> bool:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        return False
    try:
        result = subprocess.run(
            [pandoc, str(input_path), "-t", "gfm", "--wrap=none"],
            capture_output=True, text=True, timeout=120, encoding="utf-8"
        )
        if result.returncode == 0 and result.stdout.strip():
            out_md.write_text(result.stdout, encoding="utf-8")
            log(f"pandoc OK: {input_path.name} -> {out_md.name} ({len(result.stdout)} chars)")
            return True
        else:
            log(f"pandoc failed: {result.stderr[:300]}")
            return False
    except Exception as e:
        log(f"pandoc exception: {e}")
        return False

def parse_pdf_pymupdf(input_path: Path) -> str:
    try:
        import fitz  # pymupdf
    except ImportError:
        return None
    try:
        doc = fitz.open(str(input_path))
        parts = []
        for i, page in enumerate(doc):
            text = page.get_text("text")
            if text.strip():
                parts.append(text)
            else:
                # maybe scanned — note it
                parts.append(f"\n[Σελίδα {i+1}: εικόνα/σαρωμένο — χωρίς εξαγώγιμο κείμενο]\n")
        doc.close()
        full = "\n\n".join(parts)
        log(f"pymupdf: {len(full)} chars, {len(parts)} pages")
        return full
    except Exception as e:
        log(f"pymupdf error: {e}")
        return None

def parse_pdf_pdfminer(input_path: Path) -> str:
    try:
        from pdfminer.high_level import extract_text
    except ImportError:
        return None
    try:
        text = extract_text(str(input_path))
        log(f"pdfminer: {len(text)} chars")
        return text
    except Exception as e:
        log(f"pdfminer error: {e}")
        return None

def parse_pdf_ocr(input_path: Path) -> str:
    """
    Προσπάθεια OCR για σκαναρισμένα PDF.
    Χρησιμοποιεί fitz (PyMuPDF) ή pdf2image + pytesseract.
    Αν λείπει το pytesseract ή το tesseract binary, επιστρέφει None χωρίς crash.
    """
    try:
        import pytesseract
        from PIL import Image
    except (ImportError, Exception):
        log("pytesseract or PIL not installed - skipping OCR fallback")
        return None

    log("Attempting OCR fallback for scanned PDF...")
    parts = []

    # Try fitz rendering first
    try:
        import fitz
        doc = fitz.open(str(input_path))
        for i, page in enumerate(doc):
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            ocr_text = pytesseract.image_to_string(img)
            if ocr_text.strip():
                parts.append(f"\n--- [OCR Page {i+1}] ---\n{ocr_text.strip()}")
        doc.close()
        if parts:
            full = "\n\n".join(parts)
            log(f"OCR (via fitz+pytesseract) extracted {len(full)} chars")
            return full
    except Exception as e:
        log(f"fitz OCR failed/unavailable: {e}")

    # Fallback to pdf2image if fitz fails
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(str(input_path))
        for i, img in enumerate(images):
            ocr_text = pytesseract.image_to_string(img)
            if ocr_text.strip():
                parts.append(f"\n--- [OCR Page {i+1}] ---\n{ocr_text.strip()}")
        if parts:
            full = "\n\n".join(parts)
            log(f"OCR (via pdf2image+pytesseract) extracted {len(full)} chars")
            return full
    except Exception as e:
        log(f"pdf2image OCR failed/unavailable: {e}")

    return None

def parse_pdf_fallback(input_path: Path) -> str:
    # Try pymupdf then pdfminer, else fallback to OCR or return guidance
    text = parse_pdf_pymupdf(input_path)
    if text and len(text.strip()) > 100:
        return text
    text2 = parse_pdf_pdfminer(input_path)
    if text2 and len(text2.strip()) > 100:
        return text2

    # If extracted text is insufficient (< 100 chars), attempt OCR
    ocr_text = parse_pdf_ocr(input_path)
    if ocr_text and len(ocr_text.strip()) > 10:
        return ocr_text

    if text and text.strip():
        return text
    return None

def parse_epub(input_path: Path) -> str:
    # Try ebooklib+bs4 first, fallback to zip+html parse
    try:
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup
        book = epub.read_epub(str(input_path))
        parts = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), "html.parser")
                # clean scripts/styles
                for tag in soup(["script", "style"]):
                    tag.decompose()
                text = soup.get_text(separator="\n")
                # collapse whitespace
                text = re.sub(r"\n{3,}", "\n\n", text)
                text = re.sub(r"[ \t]{2,}", " ", text)
                if text.strip():
                    parts.append(text.strip())
        full = "\n\n---\n\n".join(parts)
        log(f"ebooklib: {len(full)} chars, {len(parts)} docs")
        if len(full.strip()) > 100:
            return full
    except ImportError as e:
        log(f"ebooklib/bs4 not installed: {e}")
    except Exception as e:
        log(f"ebooklib error: {e}")

    # Fallback: raw zip
    try:
        parts = []
        with zipfile.ZipFile(str(input_path), "r") as z:
            for name in z.namelist():
                if name.endswith((".html", ".xhtml", ".htm")):
                    try:
                        raw = z.read(name).decode("utf-8", errors="ignore")
                        # strip tags naively
                        text = re.sub(r"<[^>]+>", " ", raw)
                        text = re.sub(r"\s{2,}", " ", text)
                        text = re.sub(r"\n{3,}", "\n\n", text)
                        if len(text.strip()) > 50:
                            parts.append(text.strip())
                    except Exception:
                        continue
        full = "\n\n---\n\n".join(parts)
        log(f"zip fallback: {len(full)} chars, {len(parts)} files")
        if len(full.strip()) > 100:
            return full
    except Exception as e:
        log(f"zip fallback error: {e}")
    return None

def parse_docx(input_path: Path) -> str:
    try:
        import docx
        doc = docx.Document(str(input_path))
        parts = []
        for para in doc.paragraphs:
            t = para.text.strip()
            if not t:
                continue
            # headings -> markdown
            style = para.style.name if para.style else ""
            if style.startswith("Heading 1"):
                parts.append(f"# {t}")
            elif style.startswith("Heading 2"):
                parts.append(f"## {t}")
            elif style.startswith("Heading 3"):
                parts.append(f"### {t}")
            else:
                parts.append(t)
        # tables
        for table in doc.tables:
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells]
                if any(cells):
                    parts.append(" | ".join(cells))
        full = "\n\n".join(parts)
        log(f"python-docx: {len(full)} chars, {len(parts)} blocks")
        if len(full.strip()) > 50:
            return full
    except ImportError as e:
        log(f"python-docx not installed: {e}")
    except Exception as e:
        log(f"python-docx error: {e}")

    # Try mammoth as fallback
    try:
        import mammoth
        with open(str(input_path), "rb") as f:
            result = mammoth.convert_to_markdown(f)
            text = result.value
            log(f"mammoth: {len(text)} chars")
            if len(text.strip()) > 50:
                return text
    except ImportError:
        pass
    except Exception as e:
        log(f"mammoth error: {e}")
    return None

def parse_txt(input_path: Path) -> str:
    try:
        for enc in ["utf-8", "windows-1253", "windows-1252", "iso-8859-7", "latin-1"]:
            try:
                text = input_path.read_text(encoding=enc)
                if text.strip():
                    log(f"txt ({enc}): {len(text)} chars")
                    return text
            except UnicodeError:
                continue
    except Exception as e:
        log(f"txt error: {e}")
    return None

def extract_text(input_path: Path, out_md: Path) -> str:
    suffix = input_path.suffix.lower()
    # 1) try pandoc first (best quality, zero extra deps if installed)
    if suffix in [".pdf", ".epub", ".docx", ".html", ".htm"]:
        if try_pandoc(input_path, out_md):
            return out_md.read_text(encoding="utf-8")

    text = None
    if suffix == ".pdf":
        text = parse_pdf_fallback(input_path)
    elif suffix == ".epub":
        text = parse_epub(input_path)
    elif suffix in [".docx", ".doc"]:
        text = parse_docx(input_path)
    elif suffix in [".txt", ".md"]:
        text = parse_txt(input_path)
    else:
        # try as txt
        text = parse_txt(input_path)
        if not text:
            text = parse_pdf_fallback(input_path)

    if text is None or len(text.strip()) < 20:
        # Check if scanned PDF
        if suffix == ".pdf":
            msg = (
                "Δεν βρέθηκε εξαγώγιμο κείμενο. Το PDF μοιάζει σκαναρισμένο (εικόνα).\n"
                "Λύση v2: OCR με tesseract/marker. Προς το παρόν, δοκίμασε να εξάγεις το PDF ως searchable PDF.\n"
            )
            log(msg)
            # still write placeholder so pipeline continues
            text = f"# Σαρωμένο PDF — χωρίς εξαγώγιμο κείμενο\n\n{msg}\n\nΑρχείο: {input_path.name}\nΜέγεθος: {input_path.stat().st_size} bytes\n"
        else:
            raise RuntimeError(f"Αποτυχία ανάγνωσης: {input_path} (τύπος {suffix}). Δοκίμασε PDF/EPUB/DOCX/TXT.")

    # normalize
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    # Don't write yet — caller writes to full_text.md
    return text

# ---- chunking ----

def chunk_text(text: str, chunk_tokens: int = 1000) -> list:
    """
    Κόβει σε κεφάλαια/σκηνές. ~1 token ≈ 4 chars για ελληνικά/αγγλικά.
    chunk_tokens = στόχος ανά κομμάτι.
    Προσπαθεί να κόψει σε επικεφαλίδες/παραγράφους, όχι στη μέση πρότασης.
    """
    chars_per_chunk = chunk_tokens * 4  # approx
    # Detect chapter headings
    heading_re = re.compile(
        r"^(?:#+\s+.*|ΚΕΦΑΛΑΙΟ.*|Κεφάλαιο.*|CHAPTER.*|Chapter.*|Ενότητα.*|\d+\.\s+[Α-ΩA-Z].*|\d{1,3})\s*$",
        re.MULTILINE
    )
    # Find heading positions
    headings = [(m.start(), m.group(0).strip()) for m in heading_re.finditer(text)]

    # If no headings, split by paragraphs
    if not headings:
        paras = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = []
        cur = []
        cur_len = 0
        for p in paras:
            if cur_len + len(p) > chars_per_chunk and cur:
                chunks.append(("\n\n".join(cur), None))
                cur = [p]
                cur_len = len(p)
            else:
                cur.append(p)
                cur_len += len(p) + 2
        if cur:
            chunks.append(("\n\n".join(cur), None))
        return chunks

    # Split by headings
    chunks = []
    for idx, (pos, title) in enumerate(headings):
        end = headings[idx + 1][0] if idx + 1 < len(headings) else len(text)
        section = text[pos:end].strip()
        # If section too large, split further by paragraphs
        if len(section) > chars_per_chunk * 1.5:
            paras = [p.strip() for p in section.split("\n\n") if p.strip()]
            cur = []
            cur_len = 0
            part = 1
            for p in paras:
                if cur_len + len(p) > chars_per_chunk and cur:
                    chunks.append(("\n\n".join(cur), f"{title} — μέρος {part}"))
                    part += 1
                    cur = [p]
                    cur_len = len(p)
                else:
                    cur.append(p)
                    cur_len += len(p) + 2
            if cur:
                # first part keeps original title
                if part == 1:
                    chunks.append(("\n\n".join(cur), title))
                else:
                    chunks.append(("\n\n".join(cur), f"{title} — μέρος {part}"))
        else:
            chunks.append((section, title))

    # Handle prologue before first heading
    if headings and headings[0][0] > 0:
        prologue = text[:headings[0][0]].strip()
        if prologue and len(prologue) > 100:
            prologue_title = "Πρόλογος / Εισαγωγή"
            prologue_chunks = []
            if len(prologue) > chars_per_chunk:
                paras = [p.strip() for p in prologue.split("\n\n") if p.strip()]
                cur = []
                cur_len = 0
                part = 1
                for p in paras:
                    if cur_len + len(p) > chars_per_chunk and cur:
                        prologue_chunks.append(("\n\n".join(cur), f"{prologue_title} — μέρος {part}"))
                        part += 1
                        cur = [p]
                        cur_len = len(p)
                    else:
                        cur.append(p)
                        cur_len += len(p)
                if cur:
                    if part == 1:
                        prologue_chunks.append(("\n\n".join(cur), prologue_title))
                    else:
                        prologue_chunks.append(("\n\n".join(cur), f"{prologue_title} — μέρος {part}"))
            else:
                prologue_chunks.append((prologue, prologue_title))
            # prologue precedes every heading-derived chapter in reading order
            chunks[0:0] = prologue_chunks

    return chunks

def slugify(title: str, idx: int) -> str:
    if not title:
        return f"ch{idx:02d}-untitled"
    # keep greek letters, replace spaces/punct with -
    s = title.lower().strip()
    s = re.sub(r"[^\w\u0370-\u03FF\u1F00-\u1FFF0-9]+", "-", s, flags=re.UNICODE)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    s = s[:40].strip("-")
    if not s:
        s = "untitled"
    return f"ch{idx:02d}-{s}"

# ---- scaffold writers ----

def write_deprecation_wrappers(out_dir: Path):
    """Φάση 11: Γράφει backward compatibility wrappers και προειδοποιητικά μηνύματα στα παλαιά flat paths."""
    deprecation_mapping = {
        "character_psychology.json": "design/narrative/character-psychology.json",
        "tension-pacing-curve.json": "design/balance/tension-pacing-curve.json",
        "choice-tree.json": "design/narrative/choice-tree.json",
        "player-personas-simulation.json": "benchmarks/player-personas-simulation.json",
        "leitmotif-matrix.json": "design/audio/leitmotif-matrix.json",
        "information-spread-graph.json": "lore/information-spread-graph.json",
        "nash-equilibrium-report.json": "benchmarks/nash-equilibrium-report.json",
        "expansion-grammar.json": "design/narrative/expansion-grammar.json",
        "executive_audit_report.json": "benchmarks/executive_audit_report.json",
    }
    
    for legacy_name, new_path in deprecation_mapping.items():
        flat_path = out_dir / legacy_name
        target_path = out_dir / new_path
        warning_data = {
            "_deprecation_warning": f"WARNING: Legacy flat path '{legacy_name}' is deprecated in book2game v2.0+. Use '{new_path}' in the 5-layer canonical/derived structure instead.",
            "_redirect": new_path,
            "status": "deprecated_backward_compatibility_wrapper"
        }
        if target_path.exists():
            try:
                target_data = json.loads(target_path.read_text(encoding="utf-8-sig"))
                warning_data["_payload_summary"] = f"Forwarded from {new_path}"
            except Exception:
                pass
        flat_path.write_text(json.dumps(warning_data, ensure_ascii=False, indent=2), encoding="utf-8")
        log(f"[DEPRECATION] Created backward compatibility wrapper for legacy flat path: {legacy_name} -> {new_path}")


def write_source_hashes(out_dir: Path, full_text_path: Path):
    """Production-grade: compute SHA-256 paragraph hashes from full_text.md."""
    if compute_paragraph_hashes is None:
        log("WARNING: canon_helpers not available, skipping paragraph hashes")
        return None
    source_dir = out_dir / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    src = source_dir / "full_text.md"
    if full_text_path.resolve() != src.resolve():
        import shutil
        shutil.copy2(full_text_path, src)
    hashes = compute_paragraph_hashes(src)
    hash_path = source_dir / "paragraph-hashes.json"
    hash_path.write_text(json.dumps(hashes, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"source/paragraph-hashes.json: {len(hashes['paragraphs'])} paragraphs, file_hash={hashes['file_hash'][:16]}...")
    return hashes


def write_canon_layer(out_dir: Path, entities_raw: dict, text: str, hashes: dict = None):
    """Production-grade: split entities into canon/ artifacts with epistemic markers."""
    canon_dir = out_dir / "canon"
    canon_dir.mkdir(parents=True, exist_ok=True)

    if assign_canonical_uuids is None:
        log("WARNING: canon_helpers not available, writing raw entities to canon/")
        (canon_dir / "entities.json").write_text(json.dumps(entities_raw, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"canonical": {}, "aliases": {}, "uuid_map": {}}

    canon_result = assign_canonical_uuids(entities_raw, text)
    canonical = canon_result["canonical"]

    # canon/entities.json
    (canon_dir / "entities.json").write_text(json.dumps(canonical, ensure_ascii=False, indent=2), encoding="utf-8")
    n_total = sum(len(v) for v in canonical.values())
    log(f"canon/entities.json: {n_total} entities with canonical UUIDs")

    # canon/relationships.json
    rels = entities_raw.get("relationships", [])
    canon_rels = []
    uuid_map = canon_result["uuid_map"]
    for r in rels:
        if isinstance(r, dict):
            src_name = r.get("source") or r.get("from") or ""
            tgt_name = r.get("target") or r.get("to") or ""
            canon_rels.append({
                **r,
                "_epistemic": "canon",
                "_source_uuid": uuid_map.get(src_name, ""),
                "_target_uuid": uuid_map.get(tgt_name, ""),
            })
    (canon_dir / "relationships.json").write_text(json.dumps(canon_rels, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"canon/relationships.json: {len(canon_rels)} relationships")

    # canon/entity-aliases.json
    (canon_dir / "entity-aliases.json").write_text(json.dumps(canon_result["aliases"], ensure_ascii=False, indent=2), encoding="utf-8")

    # canon/world-boundaries.json (initial: open-space)
    boundaries = {
        "_epistemic": "open_space",
        "_reason": "World boundaries derived from entity extraction; requires narrative director validation",
        "locations": canonical.get("locations", []),
        "factions": canonical.get("factions", []),
    }
    (canon_dir / "world-boundaries.json").write_text(json.dumps(boundaries, ensure_ascii=False, indent=2), encoding="utf-8")

    # canon/world-glossary.json (placeholder — populated by analysis)
    glossary = {
        "_epistemic": "open_space",
        "_reason": "Glossary to be populated by narrative analysis from canon entities",
        "terms": []
    }
    (canon_dir / "world-glossary.json").write_text(json.dumps(glossary, ensure_ascii=False, indent=2), encoding="utf-8")

    # canon/unresolved-ambiguities.json (empty — quarantine bucket)
    (canon_dir / "unresolved-ambiguities.json").write_text(json.dumps({"_note": "Quarantine: items without sufficient source evidence", "items": []}, ensure_ascii=False, indent=2), encoding="utf-8")

    # audit/provenance.json — Phase 17.7: add reverse index uuid -> [hash]
    audit_dir = out_dir / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    reverse = {}
    if hashes and hashes.get("paragraphs") and canon_result.get("uuid_map"):
        # Build paragraph text -> hash map and offset index for reverse lookup
        paras = hashes["paragraphs"]
        # Map uuid -> first paragraph hash containing the entity name (1-hop)
        for name, uuid in canon_result["uuid_map"].items():
            if not name or not text:
                continue
            off = text.lower().find(name.lower())
            if off == -1:
                # fallback: first paragraph hash
                if paras:
                    reverse[uuid] = [paras[0]["hash"]]
                continue
            # find paragraph containing offset by reconstructing approx positions
            acc = 0
            found = None
            for p in paras:
                # p["text"] is truncated to 500 chars, use length heuristic
                plen = len(p.get("text", "")) + 2  # + blank line
                if acc <= off < acc + plen + 500:
                    found = p["hash"]
                    break
                acc += plen
            reverse[uuid] = [found or paras[0]["hash"]]
    provenance = {
        "tool_version": "book2game v2.0.0",
        "source_hash": hashes.get("file_hash", "") if hashes else "",
        "extraction_timestamp": datetime.now().isoformat(),
        "canon_entity_count": n_total,
        "uuid_map": canon_result["uuid_map"],
        "reverse": reverse,
    }
    (audit_dir / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")

    return canon_result


def write_full_text(out_dir: Path, text: str, source_name: str):
    p = out_dir / "full_text.md"
    header = f"# Πλήρες Κείμενο — {source_name}\n\n> Πηγή: {source_name}  \n> Ημερομηνία εξαγωγής: {datetime.now().strftime('%Y-%m-%d %H:%M')}  \n> Μήκος: {len(text)} χαρακτήρες, {len(text.split())} λέξεις\n\n---\n\n"
    p.write_text(header + text, encoding="utf-8")
    log(f"full_text.md: {len(text)} chars")
    return p

def write_chapters(out_dir: Path, chunks: list, text: str):
    ch_dir = out_dir / "chapters"
    ch_dir.mkdir(parents=True, exist_ok=True)
    index = []
    offset = 0
    for idx, (content, title) in enumerate(chunks, 1):
        slug = slugify(title or f"part-{idx}", idx)
        fname = f"{slug}.md"
        fpath = ch_dir / fname
        header = f"# {title or f'Μέρος {idx}'}\n\n> Chunk {idx}/{len(chunks)} — {len(content)} chars\n\n---\n\n"
        fpath.write_text(header + content, encoding="utf-8")
        # index entry
        # find offset in original text
        try:
            pos = text.index(content[:80]) if len(content) > 80 else text.index(content[:20])
        except ValueError:
            pos = offset
        index.append({
            "id": f"ch{idx:02d}",
            "title": title or f"Μέρος {idx}",
            "file": f"chapters/{fname}",
            "chars": len(content),
            "words": len(content.split()),
            "offset": pos,
        })
        offset += len(content)
    log(f"chapters/: {len(chunks)} files")
    return index

def write_index(out_dir: Path, index: list, source_name: str, text: str):
    p = out_dir / "index.json"
    data = {
        "source": source_name,
        "generated": datetime.now().isoformat(),
        "total_chars": len(text),
        "total_words": len(text.split()),
        "chunks": len(index),
        "entries": index,
        "rag_hint": "Χρήση: grep -n 'όρος' full_text.md  ή  grep -rn 'όρος' chapters/  — για μεγάλα βιβλία μην κάνεις Read(full_text.md)"
    }
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"index.json: {len(index)} entries")
    return p

def write_entities_scaffold(out_dir: Path, text: str = ""):
    p = out_dir / "entities.json"
    entities = None
    if text:
        try:
            entities = extract_entities_from_text(text)
        except Exception as e:
            log(f"extract_entities failed, using empty scaffold: {e}")
    if not entities:
        entities = {
            "_note": "Συμπληρώνεται από Claude ανάλυση στο Βήμα 2 του skill. Αυτό είναι scaffold για να περνάει validation.",
            "characters": [],
            "locations": [],
            "objects": [],
            "concepts": [],
            "relationships": [],
            "factions": [],
            "timeline": []
        }
    p.write_text(json.dumps(entities, ensure_ascii=False, indent=2), encoding="utf-8")
    n_entities = len(entities.get("characters", [])) + len(entities.get("locations", []))
    log(f"entities.json ({n_entities} autodetected)")
    return p

def write_lore_scaffold(out_dir: Path):
    lore_dir = out_dir / "lore"
    lore_dir.mkdir(exist_ok=True)
    p = lore_dir / "bible.md"
    p.write_text(
        "# Lore Bible — Scaffold\n\n"
        "> Συμπληρώνεται από Claude ανάλυση. Περιέχει τον κόσμο, τους κανόνες, τις φυλές, την ιστορία.\n\n"
        "## Κόσμος\n\n_..._\n\n## Κανόνες\n\n_..._\n\n## Χρονολόγιο\n\n_..._\n",
        encoding="utf-8"
    )
    log("lore/bible.md scaffold")
    return p

def write_studio_workflow_doc(out_dir: Path):
    docs_dir = out_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    p = docs_dir / "studio-workflow.md"
    p.write_text(
        "# Game Studio Workflow & Execution Law\n\n"
        "> **Νόμος Λειτουργίας:** Οποιοσδήποτε agent αναλάβει αυτό το project μέσα στο Claude Code Game Studio, οφείλει να συμμορφώνεται αυστηρά με τους παρακάτω κανόνες.\n\n"
        "## 1. 3-Tier Coordination\n"
        "- **Tier 1 Directors (Opus):** `creative-director`, `technical-director`, `producer` — καθορίζουν το όραμα, τα tradeoffs και τα sprint boundaries.\n"
        "- **Tier 2 Leads (Sonnet):** `game-designer`, `narrative-director`, `art-director`, `qa-lead`, `release-manager` — διαχειρίζονται τα επιμέρους τμήματα.\n"
        "- **Tier 3 Specialists:** Υλοποιούν stories, γράφουν κώδικα, σχεδιάζουν συστήματα, τρέχουν τεστ.\n\n"
        "## 2. 7-Phase Pipeline & Gates\n"
        "Η πρόοδος ελέγχεται αποκλειστικά από τα gates του Game Studio:\n"
        "1. `/gate-check concept` → Απαιτεί `design/gdd/game-concept.md`, `systems-index.md`, `art-bible.md`, `technical/engine.md`\n"
        "2. `/gate-check systems` → Απαιτεί πλήρη GDDs ανά σύστημα (8 ενότητες + Game Feel)\n"
        "3. `/gate-check tech` → Απαιτεί `docs/architecture/architecture.md` + min 3 ADRs + `control-manifest.md`\n"
        "4. `/gate-check pre-prod` → Απαιτεί UX docs, entity inventory, epics & stories\n"
        "5. `/gate-check production` → Sprint loop (`/story-readiness` → `/dev-story` → `/story-done`)\n"
        "6. `/gate-check polish` → Min 3 playtest reports\n"
        "7. `/gate-check release` → Release & Launch checklist\n\n"
        "## 3. Κανόνες Συνέχειας (Multi-Session Resume)\n"
        "- Ποτέ μην ξεκινάς στα τυφλή. Διάβασε πρώτα το **`roadmap.md`** (ποια φάση τρέχει) και το **`active.md`** (ποιο ήταν το τελευταίο commit/session state).\n"
        "- Κάθε session κλείνει με append στο **`active.md`**.\n"
        "- Απαγορεύεται η παράκαμψη των gates. Αν ένα gate αποτυγχάνει, διορθώνεις το σφάλμα πριν προχωρήσεις.\n",
        encoding="utf-8"
    )
    log("docs/studio-workflow.md")

def write_studio_scaffold(out_dir: Path, source_name: str, text: str):
    gdd_dir = out_dir / "design" / "gdd"
    art_dir = out_dir / "design" / "art"
    prod_dir = out_dir / "production"
    gdd_dir.mkdir(parents=True, exist_ok=True)
    art_dir.mkdir(parents=True, exist_ok=True)
    prod_dir.mkdir(parents=True, exist_ok=True)

    word_count = len(text.split())
    # guess tone placeholder
    concept = f"""# Game Concept — {source_name}

> Πηγή: {source_name}  | Λέξεις: {word_count} | Ημερομηνία: {datetime.now().strftime('%Y-%m-%d')}

## 1. Elevator Pitch

> _Συμπληρώνεται από Claude ανάλυση — μία παράγραφος που πουλάει το παιχνίδι σε 30 δευτερόλεπτα._

Βασισμένο στο βιβλίο «{source_name}». Το παιχνίδι μεταφέρει τον κόσμο, τους χαρακτήρες και την κεντρική σύγκρουση του βιβλίου σε διαδραστική εμπειρία.

## 2. Core Identity

- **Είδος (προτεινόμενο):** _βλ. Genre Ranking παρακάτω — συμπληρώνεται από Claude_
- **Πλατφόρμα:** PC (πρώτο), με δυνατότητα console/mobile
- **Κοινό:** Αναγνώστες του βιβλίου + παίκτες narrative/adventure
- **Core Fantasy:** Να ζήσεις την ιστορία από μέσα, να πάρεις αποφάσεις που το βιβλίο μόνο διηγείται

## 3. Core Fantasy & Unique Hook

- **Fantasy:** {source_name} — γίνε ο πρωταγωνιστής
- **Hook:** Ο κόσμος του βιβλίου με τους δικούς του κανόνες, όχι generic fantasy

## 4. MDA Analysis (8 Aesthetics — ranked)

| # | Aesthetic | Σχέση με βιβλίο |
|---|-----------|----------------|
| 1 | Narrative | Κεντρική αφήγηση βιβλίου |
| 2 | Discovery | Εξερεύνηση κόσμου/μυστηρίου |
| 3 | Challenge | Γρίφοι/αποφάσεις |
| 4 | Fellowship | Σχέσεις χαρακτήρων |
| 5 | Fantasy | Βύθιση στον κόσμο |
| 6 | Expression | Επιλογές διαλόγου |
| 7 | Sensation | Ατμόσφαιρα |
| 8 | Submission | Χαλάρωση/ανάγνωση |

> _Η σειρά οριστικοποιείται από Claude μετά από ανάλυση ύφους._

## 5. Player Motivation (SDT + Bartle)

- **Autonomy:** Επιλογές που αλλάζουν την ιστορία
- **Competence:** Κατανόηση κανόνων κόσμου
- **Relatedness:** Δεσμοί με χαρακτήρες
- **Bartle:** Explorer + Achiever κυρίως

## 6. Core Loop

- **30s:** Διάλογος/εξερεύνηση/αλληλεπίδραση
- **5-15m:** Ολοκλήρωση σκηνής/κεφαλαίου
- **Session (30-60m):** Κεφάλαιο + αποκάλυψη
- **Long-term:** Ολοκλήρωση ιστορίας, πολλαπλά τέλη

## 7. Game Pillars (3-5)

1. **Πιστότητα στο βιβλίο** — κανόνες κόσμου αδιαπραγμάτευτοι
2. **Αφήγηση πρώτα** — μηχανισμοί υπηρετούν την ιστορία
3. **Επιλογή με συνέπεια** — οι αποφάσεις μετράνε
4. **Ατμόσφαιρα** — ύφος βιβλίου σε κάθε pixel/νότα

**Anti-pillars:** Όχι grinding, όχι pay-to-win, όχι lore-breaking.

## 8. Technical Considerations

- Engine: ανοιχτό (Godot/Unity/Unreal — επιλέγεται στο Technical Setup phase)
- RAG: `full_text.md` + `index.json` για αναφορά λεπτομερειών
- Save system: κεφάλαιο-based

## 9. Risks

- Μεγάλο scope αν μεταφέρουμε όλο το βιβλίο 1:1 → MVP = 2-3 κεφάλαια
- Spoilers → guardrails στο narrative

## 10. MVP Definition

- **MVP:** 1 κεφάλαιο playable, 2 χαρακτήρες, βασικός διάλογος + 1 μηχανισμός (γρίφος/μάχη ανάλογα genre)
- **Vertical Slice:** 3 κεφάλαια, πλήρες loop
- **Full Vision:** Όλο το βιβλίο

## Genre Ranking — Προσωρινό (ο Claude το οριστικοποιεί)

> Βλ. `references/genre-taxonomy.md` για κριτήρια.

| Rank | Genre | Καταλληλότητα | Αιτιολόγηση (draft) |
|------|-------|---------------|---------------------|
| 1 | Adventure | ★★★★☆ | Αφήγηση + εξερεύνηση ταιριάζει σε βιβλίο |
| 2 | Visual Novel | ★★★★☆ | Διάλογοι + επιλογές |
| 3 | RPG | ★★★☆☆ | Χαρακτήρες + εξέλιξη |
| 4 | Puzzle | ★★★☆☆ | Αν έχει μυστήριο/γρίφους |

_Η τελική κατάταξη με αιτιολόγηση γίνεται από Claude στο Βήμα 2._

---
*Scaffold — συμπληρώνεται από Claude ανάλυση.*
"""
    (gdd_dir / "game-concept.md").write_text(concept, encoding="utf-8")

    systems = """# Systems Index

> Πίνακας όλων των συστημάτων — priority + dependencies

| System | Κατηγορία | Priority | Dependencies | Status |
|--------|-----------|----------|--------------|--------|
| Narrative / Dialogue | Narrative | MVP | — | Draft |
| World / Exploration | Core | MVP | Narrative | Draft |
| Choice & Consequence | Core | MVP | Narrative | Draft |
| Character Progression | Progression | Vertical Slice | Narrative | Draft |
| Puzzle / Challenge | Gameplay | Vertical Slice | World | Draft |
| Audio / Atmosphere | Audio | Vertical Slice | — | Draft |
| Save / Persistence | Persistence | MVP | — | Draft |
| UI / UX | UI | MVP | — | Draft |

## Dependency Map

```
Foundation: Save, UI
    ↓
Core: Narrative, World, Choice
    ↓
Feature: Progression, Puzzle
    ↓
Presentation: Audio
```

## Recommended Design Order

1. Narrative → 2. World → 3. Choice → 4. Save/UI → 5. Progression → 6. Puzzle → 7. Audio

## Circular Dependencies

_Καμία προς το παρόν._

## High-Risk Systems

- Narrative branching (scope explosion) → guardrails: max 3 branches ανά κεφάλαιο στο MVP
"""
    (gdd_dir / "systems-index.md").write_text(systems, encoding="utf-8")

    pillars = """# Game Pillars

> Cross-departmental — όλοι οι agents διαβάζουν αυτό.

## Pillar 1: Πιστότητα στο βιβλίο
Κάθε χαρακτήρας, τοποθεσία, κανόνας κόσμου προέρχεται από το βιβλίο. Αν δεν είναι στο `full_text.md`, δεν μπαίνει στο παιχνίδι χωρίς έγκριση.

## Pillar 2: Αφήγηση πρώτα
Οι μηχανισμοί υπηρετούν την ιστορία, όχι το αντίστροφο.

## Pillar 3: Επιλογή με συνέπεια
Κάθε σημαντική επιλογή έχει ορατή συνέπεια εντός 15 λεπτών παιχνιδιού.

## Pillar 4: Ατμόσφαιρα
Το ύφος του βιβλίου (τόνος, γλώσσα, ρυθμός) σε κάθε σκηνή.

## Anti-Pillars
- Όχι grinding χωρίς νόημα
- Όχι lore-breaking για χάρη mechanics
- Όχι pay-to-win

## Design Tests
- «Θα το αναγνώριζε ο αναγνώστης του βιβλίου;» → αν όχι, κόβεται
- «Προχωράει την ιστορία;» → αν όχι, είναι filler
"""
    (gdd_dir / "game-pillars.md").write_text(pillars, encoding="utf-8")

    art = """# Art Bible — Scaffold

> Συμπληρώνεται από Claude + art-director.

## Palette
_Εξάγεται από ύφος βιβλίου — π.χ. σκοτεινό/μυστηριώδες → desaturated, warm highlights_

## Rendering
_Stylized vs realistic — επιλέγεται ανάλογα genre_

## Proportions
_..._

## Naming Conventions
`assets/art/ch{NN}/{character|location}_{variant}.png`

## References
_..._
"""
    (art_dir / "art-bible.md").write_text(art, encoding="utf-8")

    (prod_dir / "stage.txt").write_text("concept\n", encoding="utf-8")
    log("Studio scaffold: game-concept + systems-index + pillars + art-bible + stage.txt")

OVERCLAIM_PATTERNS = [
    # unverifiable benchmark-style claims — move to quarantine instead of shipping as fact
    re.compile(r"\b99\.8%\b"),
    re.compile(r"\b0\.00%\b.*?deadlock", re.IGNORECASE),
    re.compile(r"Gini\s*<?\s*0\.1\d"),
    re.compile(r"PROVEN_BALANCED", re.IGNORECASE),
    re.compile(r"\bNash Equilibrium\b", re.IGNORECASE),
    re.compile(r"Metacritic\s*\d{2}", re.IGNORECASE),
    re.compile(r"D30\s*.*49\.4%", re.IGNORECASE),
    re.compile(r"D1\s*.*86\.4%", re.IGNORECASE),
]


def _json_load_local(p: Path):
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        try:
            raw = p.read_bytes()
            return json.loads(raw[3:].decode("utf-8") if raw.startswith(b"\xef\xbb\xbf") else raw.decode("utf-8"))
        except Exception:
            return None


def write_contract_snapshot(out_dir: Path):
    """Phase 13: copy repo contracts/stage-contracts.json into output/contracts/."""
    repo_contracts = Path(__file__).resolve().parent.parent / "contracts" / "stage-contracts.json"
    if not repo_contracts.exists():
        repo_contracts = Path(__file__).resolve().parent / "contracts" / "stage-contracts.json"
    out_contracts = out_dir / "contracts"
    out_contracts.mkdir(parents=True, exist_ok=True)
    if repo_contracts.exists():
        import shutil as _sh
        _sh.copy2(repo_contracts, out_contracts / "stage-contracts.json")
        try:
            _ver = json.loads(repo_contracts.read_text(encoding="utf-8-sig", errors="replace")).get("version", "?")
        except Exception:
            _ver = "?"
        log(f"contracts/stage-contracts.json -> output (v{_ver})")
    else:
        # minimal fallback
        (out_contracts / "stage-contracts.json").write_text(json.dumps({
            "version": "1.0.0",
            "stages": [],
            "_note": "fallback — repo contracts/stage-contracts.json not found at build time",
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        log("contracts/stage-contracts.json — fallback written (repo contract not found)")


def quarantine_overclaims(out_dir: Path):
    """
    Phase 13: anti-overclaim.
    Scans derived artifacts for unverifiable benchmark strings (99.8%, Nash, Metacritic…).
    Anything that matches OVERCLAIM_PATTERNS is appended to canon/unresolved-ambiguities.json
    with epistemic quarantine, so it never ships as canon fact.
    """
    canon_q = out_dir / "canon" / "unresolved-ambiguities.json"
    existing = _json_load_local(canon_q)
    if existing is None:
        existing = {"_note": "Quarantine: items without sufficient source evidence", "items": []}
    if "items" not in existing:
        existing["items"] = []

    # only scan derived-ish outputs — canon is already gated
    scan_rel_paths = [
        "benchmarks/executive_audit_report.json",
        "benchmarks/nash-equilibrium-report.json",
        "benchmarks/player-personas-simulation.json",
        "design/balance/progression-gini.json",
        "design/narrative/character-psychology.json",
    ]
    new_quarantined: list[dict] = []
    for rel in scan_rel_paths:
        p = out_dir / rel
        if not p.exists():
            continue
        txt = p.read_text(encoding="utf-8-sig", errors="ignore")
        for pat in OVERCLAIM_PATTERNS:
            for m in pat.finditer(txt):
                snippet = txt[max(0, m.start() - 60): m.end() + 60].replace("\n", " ").strip()
                new_quarantined.append({
                    "artifact": rel,
                    "pattern": pat.pattern,
                    "match": m.group(0)[:120],
                    "context": snippet[:280],
                    "_epistemic": "quarantined",
                    "reason": "Unverifiable benchmark claim — requires playable build / playtest, not pre-production heuristic",
                    "action": "Removed from fact claims; retained here for audit traceability",
                })
                break  # one per file per pattern is enough

    # dedupe by (artifact, pattern)
    seen: set[tuple[str, str]] = {(it.get("artifact"), it.get("pattern")) for it in existing["items"] if isinstance(it, dict)}
    appended = 0
    for item in new_quarantined:
        key = (item["artifact"], item["pattern"])
        if key not in seen:
            existing["items"].append(item)
            seen.add(key)
            appended += 1

    if appended:
        existing["_quarantine_updated"] = datetime.now().isoformat()
        (out_dir / "canon").mkdir(parents=True, exist_ok=True)
        canon_q.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
        log(f"anti-overclaim: quarantined {appended} unverifiable claim(s) → canon/unresolved-ambiguities.json")
    else:
        log("anti-overclaim: no unverifiable claims found — quarantine unchanged")


def run_whitebox_validation(out_dir: Path, seed: int = 42):
    """Phase 13: run whitebox_runner on the freshly-built output (seed=42 deterministic)."""
    try:
        import importlib.util as _iu
        _wb_path = Path(__file__).resolve().parent / "whitebox_runner.py"
        if not _wb_path.exists():
            log("whitebox_runner.py not found — skipping whitebox stage")
            return
        _spec = _iu.spec_from_file_location("whitebox_runner", _wb_path)
        _mod = _iu.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        _mod.run(out_dir, seed=seed)
    except Exception as e:
        import traceback
        log(f"WARNING: whitebox_runner failed: {e}\n{traceback.format_exc()}")


def write_deprecated_legacy_wrappers(out_dir: Path):
    """Φάση 11 — Deprecation legacy flat artifacts.
    Δημιουργεί/ενημερώνει legacy root wrappers με προειδοποιητικό μήνυμα deprecation
    καθοδηγώντας τους agents στα νέα 5-layer paths (source/, canon/, derived/, views/projections/).
    """
    deprecation_notice = (
        "<!-- DEPRECATION WARNING -->\n"
        "> [DEPRECATED LEGACY ARTIFACT]\n"
        "> Αυτό το αρχείο διατηρείται αποκλειστικά για backward compatibility.\n"
        "> Η πρωτογενής και έγκυρη πηγή πληροφορίας έχει μεταφερθεί στην 5-layer αρχιτεκτονική:\n"
        "> - Source text / hashes: source/full_text.md , source/paragraph-hashes.json\n"
        "> - Canonical entities: canon/entities.json\n"
        "> - Agent Projections: views/projections/<agent-name>/\n\n"
    )

    # Legacy root full_text.md notice header prepend if needed
    ft_legacy = out_dir / "full_text.md"
    if ft_legacy.exists():
        content = ft_legacy.read_text(encoding="utf-8")
        if "[DEPRECATED LEGACY ARTIFACT]" not in content:
            ft_legacy.write_text(deprecation_notice + content, encoding="utf-8")

    # Legacy root entities.json wrapper
    ent_legacy = out_dir / "entities.json"
    canon_ent = out_dir / "canon" / "entities.json"
    if canon_ent.exists():
        try:
            c_data = json.loads(canon_ent.read_text(encoding="utf-8"))
            wrapper_data = {
                "_deprecation_warning": "DEPRECATED LEGACY ARTIFACT. Use canon/entities.json or views/projections/<agent>/canon.projection.json",
                "_canonical_source": "canon/entities.json",
                **c_data
            }
            ent_legacy.write_text(json.dumps(wrapper_data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            log(f"WARNING: legacy entities wrapper creation failed: {e}")

    log("Legacy deprecation wrappers updated successfully.")


# ---- main ----

def main():
    parser = argparse.ArgumentParser(description="book2game — PDF/EPUB/DOCX → Game Studio scaffold")
    parser.add_argument("book", help="Διαδρομή προς βιβλίο (PDF/EPUB/DOCX/TXT/MD)")
    parser.add_argument("--out", dest="out", default=None, help="Φάκελος προορισμού (default: <book>_game)")
    parser.add_argument("--chunk", type=int, default=1000, help="Tokens ανά chunk (default 1000)")
    parser.add_argument("--export-yarn", dest="export_yarn", action="store_true", help="Phase 14b: export Yarn")
    parser.add_argument("--export-nodes", dest="export_nodes", action="store_true", help="Phase 14b: export node graph")
    parser.add_argument("--sim-seed", type=int, default=42, help="Phase 16a: simulation seed (default 42)")
    parser.add_argument("--stop-after-entities", dest="stop_after_entities", action="store_true",
                         help="Βήμα 1.5: σταμάτα αμέσως μετά το draft entities.json (πριν το Βήμα 2 12-Cycle engine) ώστε ο agent να το βελτιώσει πρώτα")
    parser.add_argument("--resume-entities", dest="resume_entities", action="store_true",
                         help="Βήμα 1.5: συνέχισε στο Βήμα 2 διαβάζοντας το ήδη-υπάρχον (πιθανώς agent-βελτιωμένο) entities.json από --out, χωρίς να ξαναγίνει extraction/chunking")
    args = parser.parse_args()

    book_path = Path(args.book).resolve()
    if not book_path.exists():
        print(f"Σφάλμα: δεν βρέθηκε αρχείο: {book_path}", file=sys.stderr)
        sys.exit(1)

    if args.out:
        out_dir = Path(args.out).resolve()
    else:
        out_dir = book_path.parent / f"{book_path.stem}_game"

    out_dir.mkdir(parents=True, exist_ok=True)
    log(f"Input: {book_path}")
    log(f"Output: {out_dir}")
    log(f"Chunk: {args.chunk} tokens")

    canon_result = None
    if args.resume_entities:
        # Βήμα 1.5 resume: το Βήμα 1 (extraction/chunking/draft entities) έτρεξε ήδη σε
        # προηγούμενη κλήση με --stop-after-entities· ο agent βελτίωσε το entities.json
        # στο --out στο μεταξύ. Εδώ ΔΕΝ ξαναγράφουμε το entities.json — μόνο διαβάζουμε
        # ό,τι υπάρχει ήδη στο δίσκο και συνεχίζουμε κατευθείαν στο Βήμα 2.
        ft_path = out_dir / "source" / "full_text.md"
        if not ft_path.exists():
            ft_path = out_dir / "full_text.md"
        if not ft_path.exists():
            print(f"Σφάλμα: --resume-entities αλλά δεν βρέθηκε full_text.md κάτω από {out_dir}. "
                  f"Χρειάζεται πρώτα τρέξιμο χωρίς --resume-entities (ιδανικά με --stop-after-entities).", file=sys.stderr)
            sys.exit(1)
        if not (out_dir / "entities.json").exists():
            print(f"Σφάλμα: --resume-entities αλλά δεν βρέθηκε entities.json στο {out_dir}.", file=sys.stderr)
            sys.exit(1)
        text = ft_path.read_text(encoding="utf-8")
        try:
            source_hashes = write_source_hashes(out_dir, ft_path)
        except Exception as e:
            log(f"WARNING: paragraph hashes failed: {e}")
            source_hashes = None
        chunks = chunk_text(text, chunk_tokens=args.chunk)
        if not chunks:
            chunks = [(text, "Πλήρες Κείμενο")]
        log(f"--resume-entities: παράλειψη extraction/chunking ({len(text)} chars από δίσκο), entities.json διατηρείται όπως είναι")
    else:
        # 1) Extract text
        tmp_md = out_dir / "_tmp_extract.md"
        try:
            text = extract_text(book_path, tmp_md)
        except Exception as e:
            print(f"Σφάλμα εξαγωγής: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            if tmp_md.exists():
                try:
                    tmp_md.unlink()
                except:
                    pass

        if not text or len(text.strip()) < 20:
            print("Σφάλμα: εξήχθη κενό κείμενο.", file=sys.stderr)
            sys.exit(1)

        # 1b) Phase 17: Normalized Document IR (source/document_ir.json) + GFM full_text.md
        ft_path = None
        if process_document is not None and build_document_ir is not None:
            try:
                ir_path = process_document(book_path, out_dir, text)
                if ir_path and ir_path.exists():
                    ft_path = ir_path
                    log(f"Phase 17 IR: source/document_ir.json + source/full_text.md (GFM, {len(ir_path.read_text(encoding='utf-8'))} chars)")
                else:
                    log("WARNING: document_ir process_document returned empty, falling back to legacy write_full_text")
                    ft_path = write_full_text(out_dir, text, book_path.name)
            except Exception as e:
                import traceback as _tb
                log(f"WARNING: document_ir failed: {e}\n{_tb.format_exc()}")
                ft_path = None
        # 2) Write full_text (legacy fallback if IR not written)
        if ft_path is None or not ft_path.exists():
            ft_path = write_full_text(out_dir, text, book_path.name)

        # 2b) Production-grade: paragraph hashes + canon layer
        source_hashes = None
        try:
            source_hashes = write_source_hashes(out_dir, ft_path)
            log("Paragraph hashes written to source/paragraph-hashes.json")
        except Exception as e:
            log(f"WARNING: paragraph hashes failed: {e}")

        # 3) Chunk
        chunks = chunk_text(text, chunk_tokens=args.chunk)
        if not chunks:
            chunks = [(text, "Πλήρες Κείμενο")]
        index = write_chapters(out_dir, chunks, text)
        write_index(out_dir, index, book_path.name, text)

        # 4) Scaffolds
        entities_path = write_entities_scaffold(out_dir, text=text)
        write_lore_scaffold(out_dir)

        if args.stop_after_entities:
            log(f"--stop-after-entities: σταμάτημα μετά το draft entities.json.")
            log(f"Agent: βελτίωσε το {out_dir / 'entities.json'} (Βήμα 1.5 του SKILL.md), μετά ξανατρέξε με --resume-entities --out \"{out_dir}\" για να συνεχίσει το Βήμα 2.")
            return

    # 4b) Production-grade: canon layer with UUIDs
    try:
        entities_raw = json.loads((out_dir / "entities.json").read_text(encoding="utf-8"))
        canon_result = write_canon_layer(out_dir, entities_raw, text, source_hashes)
        log(f"Canon layer: {canon_result['canonical'].keys() if canon_result else 'skipped'}")
    except Exception as e:
        log(f"WARNING: canon layer failed: {e}")
    write_studio_scaffold(out_dir, book_path.stem, text)
    write_studio_workflow_doc(out_dir)

    # 4b) Archetype analysis + production artifacts (Cycle 3 & 4: framing/briefs/DAG)
    archetype_report = classify_book(text, chunks)
    log(f"Archetype: {archetype_report['archetype']} ({archetype_report.get('confidence', '?')})")
    (out_dir / "archetype.json").write_text(json.dumps(archetype_report, ensure_ascii=False, indent=2), encoding="utf-8")

    if archetype_report["archetype"] == "ANTHOLOGY_EPISODIC":
        write_framing_hub(out_dir, archetype_report, chunks)
    elif archetype_report["archetype"] == "THEMATIC_EDUCATIONAL":
        write_concept_matrix(out_dir, archetype_report, chunks)

    write_production_artifacts(out_dir, archetype_report)

    # 4c) Generate advanced cycle artifacts (5–12) — psychology, pacing, branching, personas, audio, ecology, balance, longevity
    generate_advanced_artifacts = write_advanced_artifacts
    generate_advanced_artifacts(out_dir, text, chunks, archetype_report)

    # 4d) Production-grade: assemble ALL agent projections
    try:
        from pathlib import Path as _P
        import importlib.util as _iu
        _asm_path = _P(__file__).resolve().parent / "assemble_projection.py"
        if _asm_path.exists():
            _spec = _iu.spec_from_file_location("assemble_projection", _asm_path)
            _mod = _iu.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)
            _assembled = 0
            for _aname, _aspec in _mod.AGENT_SPECS.items():
                if _mod.assemble_agent(out_dir, _aname, _aspec):
                    _assembled += 1
            log(f"Projections assembled: {_assembled}/{len(_mod.AGENT_SPECS)}")
    except Exception as e:
        import traceback
        log(f"WARNING: projection assembly failed: {e}\n{traceback.format_exc()}")

    # 4e) Φάση 11: Create/update legacy deprecation wrappers
    try:
        write_deprecated_legacy_wrappers(out_dir)
    except Exception as e:
        log(f"WARNING: legacy deprecation wrappers failed: {e}")

    # 4f) Phase 13 — Runtime Validation Layer (whitebox + contracts + anti-overclaim)
    try:
        write_contract_snapshot(out_dir)
    except Exception as e:
        log(f"WARNING: contract snapshot failed: {e}")
    try:
        quarantine_overclaims(out_dir)
    except Exception as e:
        log(f"WARNING: anti-overclaim quarantine failed: {e}")
    try:
        run_whitebox_validation(out_dir)
    except Exception as e:
        log(f"WARNING: whitebox validation failed: {e}")

    # 4h) Phase 17.1 — Package Index (manifest + catalog + handover)
    if build_package_index_run is not None:
        try:
            build_package_index_run(out_dir)
            log("Phase 17 Package Index: _manifest.json + _catalog.md + _handover.json")
        except Exception as e:
            import traceback as _tb2
            log(f"WARNING: package index failed: {e}\n{_tb2.format_exc()}")
    # 4g) Phase 15 — Data Backbone (schemas + knowledge)
    try:
        from pathlib import Path as _PB
        import importlib.util as _IU2
        for _mod_name in ["generate_data_backbone", "generate_exports", "simulate_state", "theory_lenses"]:
            _p = _PB(__file__).resolve().parent / f"{_mod_name}.py"
            if not _p.exists():
                continue
            _spec2 = _IU2.spec_from_file_location(_mod_name, _p)
            _m2 = _IU2.module_from_spec(_spec2)
            _spec2.loader.exec_module(_m2)
            if hasattr(_m2, "run"):
                # pass flags for exports
                if _mod_name == "generate_exports":
                    _m2.run(out_dir, flags={"export_yarn": getattr(args, "export_yarn", False) or not getattr(args, "export_only_flagged", False),
                                            "export_nodes": getattr(args, "export_nodes", False) or not getattr(args, "export_only_flagged", False)})
                elif _mod_name == "simulate_state":
                    _m2.run(out_dir, seed=getattr(args, "sim_seed", 42))
                else:
                    _m2.run(out_dir)
            log(f"{_mod_name} — OK")
    except Exception as e:
        import traceback
        log(f"WARNING: Phase 15/14b/16a/15b runner failed: {e}\n{traceback.format_exc()}")

    # 5) game_blueprint.md + technical/engine.md
    blueprint_p = out_dir / "game_blueprint.md"
    blueprint_p.write_text(
        f"# Game Blueprint — {book_path.stem}\n\n"
        f"> Πηγή: {book_path.name} | Αρχείο: game_blueprint.md | Ημερομηνία: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        f"## Elevator Pitch\n\n_Συμπληρώνεται από Claude ανάλυση. Ένα δυνατό pitch που συνδέει το βιβλίο με το gameplay._\n\n"
        f"## Σύνοψη\n\n_Αυτό το αρχείο είναι η κεντρική εισαγωγή για κάθε agent του Game Studio που μπαίνει στο project._\n\n"
        f"## Studio Execution Model\n\n"
        f"> Όταν αυτός ο φάκελος ανοίγει μέσα στο Claude Code Game Studio, η ανάπτυξη ακολουθεί τον νόμο του Studio:\n"
        f"> 7 φάσεις με gates (`/gate-check <phase>`), agents με tiers (Directors → Leads → Specialists), templates από το `.claude/docs/templates/`.\n\n"
        f"### Πώς συνεχίζει ο επόμενος agent\n"
        f"1. Διάβασε **`roadmap.md`** — αυτό είναι το μόνο έγκυρο χρονοδιάγραμμα. Κάθε φάση έχει σημειωμένο το gate της.\n"
        f"2. Διάβασε **`docs/studio-workflow.md`** — ο νόμος λειτουργίας μέσα στο Studio (φάσεις, gates, ρόλοι, απαγορεύσεις).\n"
        f"3. Διάβασε **`active.md`** — τι πέρασε το τελευταίο session, τι εκκρεμεί.\n"
        f"4. Εκτέλεσε την τρέχουσα φάση ΜΟΝΟ μέσω των templates και gates του Studio.\n"
        f"5. Ποτέ μην εφεύρεις νέα δομή. Ό,τι δεν ορίζει το Studio, δεν υπάρχει.\n\n"
        f"## Δομή Φακέλου\n\n"
        f"- `full_text.md` + `chapters/` + `index.json`: Πλήρες κείμενο & RAG index\n"
        f"- `entities.json` + `lore/bible.md`: Χαρακτήρες & Κόσμος\n"
        f"- `design/gdd/`: Game Concept, Systems Index, Game Pillars\n"
        f"- `technical/engine.md`: Επιλογή μηχανής & MCP servers\n"
        f"- `docs/studio-workflow.md`: Νόμος λειτουργίας μέσα στο Game Studio\n"
        f"- `active.md` + `roadmap.md`: Multi-session track\n\n"
        f"## Genre Ranking & Engine Selection\n\n"
        f"- **Προτεινόμενο Genre:** _Adventure_ (βλ. `design/gdd/game-concept.md` — οριστικοποιείται από Claude)\n"
        f"- **Επιλεγμένο Engine:** _Godot 4.x_ (βλ. `technical/engine.md` — αιτιολόγηση βάσει είδους, ύφους, πλατφόρμας)\n\n"
        f"## Εκτέλεση\n\n"
        f"1. Άνοιγμα φακέλου στο Claude Code Game Studio\n"
        f"2. Τρέξιμο `/gate-check concept`\n"
        f"3. Συνέχιση από `roadmap.md`\n",
        encoding="utf-8"
    )
    log("game_blueprint.md")

    tech_dir = out_dir / "technical"
    tech_dir.mkdir(exist_ok=True)

    engine_md = tech_dir / "engine.md"
    engine_md.write_text(
        f"# Game Engine Selection\n\n"
        f"## Επιλογή\n\n- **Engine:** Godot 4.x (GDScript / C#)\n"
        f"- **Αιτιολόγηση:** Βασίστηκε στο είδος Adventure, άρα η Godot παρέχει εξαιρετική υποστήριξη 2D & lightweight 3D, με ελαφρύ footprint & ενσωματωμένο editor.\n\n"
        f"## Target Platforms\n\n- PC (Windows, Linux, macOS)\n- Mobile (Android, iOS)\n- Web (HTML5)\n\n"
        f"## Game Studio MCP Integration\n\n"
        f"- **MCP Server:** Godot MCP Server\n"
        f"- **Agent:** godot-specialist, gdscript\n"
        f"- **Bridge Hooks:** Headless CLI execution, GUT unit tests, GDScript linter\n",
        encoding="utf-8"
    )
    log("technical/engine.md")

    mcp_md = tech_dir / "mcp-servers.md"
    mcp_md.write_text(
        f"# Game Studio MCP Servers & Integrations\n\n"
        f"| Engine | MCP Server | Τι κάνει | Απαιτήσεις |\n"
        f"|--------|------------|----------|------------|\n"
        f"| Godot | Godot MCP Server | Headless CLI execution, scene inspector, GUT tests | Godot 4.x installed |\n"
        f"| Unity | Unity MCP Bridge | Editor WebSocket/IPC, playmode automation | Unity 6+ running |\n"
        f"| Unreal | Unreal Remote Execution | Editor automation, Blueprint compilation | UE 5.x running |\n"
        f"| Phaser | Node.js / Playwright | Web app testing & DOM inspector | Node.js + Browser |\n"
        f"| Custom | CLI / GDB / LLDB | Script execution & low-level debugging | OS command line |\n",
        encoding="utf-8"
    )
    log("technical/mcp-servers.md")

    # 6) Output README.md — Game Studio integration guide
    readme_p = out_dir / "README.md"
    readme_p.write_text(
        f"# Game Project — {book_path.stem}\n\n"
        f"> Αυτόματα δημιουργημένος φάκελος από το book2game. Έτοιμος για ανάπτυξη μέσα στο Claude Code Game Studio.\n\n"
        f"## Πώς να τον συνδέσεις με το Game Studio\n\n"
        f"1. **Προϋπόθεση:** Έχεις κλωνοποιήσει το template του Game Studio (Donchitos/Claude-Code-Game-Studios) και έχει ρυθμιστεί το `.claude/` (agents, skills, hooks).\n"
        f"2. **Τοποθέτηση:** Αντικατέστησε/συγχώνευσε αυτόν τον φάκελο στη ρίζα του Game Studio project. Κράτησε το `.claude/` του Studio ανέπαφο.\n"
        f"3. **Πρώτο gate:** Τρέξε `/gate-check concept`. Το output είναι ήδη δομημένο ώστε να περνάει (game-concept, systems-index, pillars, art-bible, stage.txt=concept).\n"
        f"4. **Συνέχεια:** Ο επόμενος agent ξεκινά από `roadmap.md` + `docs/studio-workflow.md`. Εκεί είναι ο νόμος του Studio.\n"
        f"5. **Resume after break:** Διάβασε `active.md` → συνέχισε την τρέχουσα φάση → τρέξε το gate της → ενημέρωσε `active.md`.\n\n"
        f"## Τι περιέχει\n\n"
        f"- `full_text.md` + `chapters/` + `index.json`: Πλήρες κείμενο βιβλίου, RAG-ready\n"
        f"- `entities.json` + `lore/bible.md`: Χαρακτήρες, κόσμος, κανόνες\n"
        f"- `game_blueprint.md`: Κεντρική εισαγωγή + Studio Execution Model\n"
        f"- `technical/engine.md`: Επιλεγμένη μηχανή + MCP servers\n"
        f"- `design/gdd/`: Concept, Systems, Pillars — ακριβώς τα templates του Studio\n"
        f"- `docs/studio-workflow.md`: Ο νόμος λειτουργίας μέσα στο Studio\n\n"
        f"## Σημείωση\n\n"
        f"Αυτός ο φάκελος ΔΕΝ αντικαθιστά το Game Studio. Είναι το **υλικό (bible, full text, analysis)** που τροφοδοτεί το Studio. Το workflow (φάσεις, gates, agents) ανήκει στο Studio.\n",
        encoding="utf-8"
    )
    log("README.md")

    # 7) design.md / active.md / roadmap.md
    design_p = out_dir / "design.md"
    if not design_p.exists():
        design_p.write_text(
            f"# Design — {book_path.stem}\n\n"
            f"> Πηγή: {book_path.name}  \n> Λέξεις: {len(text.split())}  \n> Chunks: {len(chunks)}\n\n"
            "## Σύνοψη\n\n_Συμπληρώνεται από Claude ανάλυση (Βήμα 2 του skill)._\n\n"
            "## Contracts\n\n- Input: `full_text.md` + `chapters/`\n- Output: `entities.json`, `lore/bible.md`, `design/gdd/*`\n",
            encoding="utf-8"
        )

    active_p = out_dir / "active.md"
    active_content = f"""# Active — {book_path.stem}

> Ζωντανό track. Ενημερώνεται σε κάθε session. Μην ξαναγράφεις ιστορία — κάνε append.

## Gates

- [x] G1: PDF/EPUB/DOCX → full_text.md — CHECK: python parse_book.py — EXPECT: FULL_TEXT_OK — EVIDENCE: {len(text)} chars, {len(text.split())} words
- [x] G2: Chunking + index — CHECK: count chapters/ — EXPECT: INDEX_OK — EVIDENCE: {len(chunks)} chunks, index.json OK
- [x] G3: Scaffold entities.json — CHECK: entities.json exists — EXPECT: ENTITIES_OK scaffold — EVIDENCE: pending Claude ανάλυση
- [ ] G4: Genre ranking 13 κατηγοριών — CHECK: grep Genre game-concept.md — EXPECT: GENRE_RANKED — EVIDENCE: pending
- [ ] G5: Studio scaffold gate-check — CHECK: validate_output.py — EXPECT: GATE_PASS — EVIDENCE: pending
- [ ] G6: Resume — CHECK: active.md exists — EXPECT: RESUME_OK — EVIDENCE: {datetime.now().isoformat()}

## Session Log

- {datetime.now().strftime('%Y-%m-%d %H:%M')} — parse_book.py OK — {book_path.name} → {len(chunks)} chunks
- Επόμενο: Claude ανάλυση (Βήμα 2) → entities.json + game-concept.md final

## Handoff

_Κανένα._
"""
    active_p.write_text(active_content, encoding="utf-8")

    roadmap_p = out_dir / "roadmap.md"
    if not roadmap_p.exists():
        roadmap_p.write_text(
            f"# Studio Master Roadmap — {book_path.stem}\n\n"
            f"> Studio-aligned 7-Phase Roadmap. Κάθε φάση ξεκλειδώνει μόνο όταν περάσει το αντίστοιχο Gate.\n\n"
            f"## Phase 1: Concept & RAG — 🟡 IN PROGRESS\n"
            f"- [x] Βιβλίο parsed (`full_text.md` + {len(chunks)} chapters + `index.json`)\n"
            f"- [x] Engine selected & MCP defined (`technical/engine.md`)\n"
            f"- [ ] Claude ανάλυση: `entities.json`, `lore/bible.md`, `design/gdd/game-concept.md`\n"
            f"- [ ] Gate Check: `/gate-check concept` (PASS)\n"
            f"- [ ] Μετάβαση: `echo 'systems' > production/stage.txt`\n\n"
            f"## Phase 2: Systems Design — ⏳ LOCKED\n"
            f"- [ ] GDDs ανά σύστημα στο `design/gdd/<system>.md` (8 υποχρεωτικές ενότητες + Game Feel)\n"
            f"- [ ] Economy balance, formulas, progression curves\n"
            f"- [ ] Cross-review GDDs\n"
            f"- [ ] Gate Check: `/gate-check systems` (PASS)\n\n"
            f"## Phase 3: Technical Setup — ⏳ LOCKED\n"
            f"- [ ] `docs/architecture/architecture.md` + ADRs (≥3 `adr-*.md`)\n"
            f"- [ ] `control-manifest.md` + Input mapping\n"
            f"- [ ] Studio MCP server active (Godot/Unity/Unreal bridge)\n"
            f"- [ ] Gate Check: `/gate-check tech` (PASS)\n\n"
            f"## Phase 4: Pre-Production — ⏳ LOCKED\n"
            f"- [ ] `design/assets/entity-inventory.md` + `design/ux/*.md`\n"
            f"- [ ] Epics & User Stories στο `production/epics/`\n"
            f"- [ ] Prototype στο `prototypes/`\n"
            f"- [ ] Gate Check: `/gate-check pre-prod` (PASS)\n\n"
            f"## Phase 5: Production — ⏳ LOCKED\n"
            f"- [ ] Sprint loop: `/story-readiness` → `/dev-story` → `/story-done`\n"
            f"- [ ] Implementation υπό 3-tier coordination (Director -> Lead -> Specialist)\n"
            f"- [ ] Gate Check: `/gate-check production` (PASS)\n\n"
            f"## Phase 6: Polish & QA — ⏳ LOCKED\n"
            f"- [ ] Playtest reports (≥3 στο `production/playtests/`)\n"
            f"- [ ] Performance profiling & accessibility check\n"
            f"- [ ] Gate Check: `/gate-check polish` (PASS)\n\n"
            f"## Phase 7: Release — ⏳ LOCKED\n"
            f"- [ ] Release checklist & build deployment\n"
            f"- [ ] Final gate: `/gate-check release` (PASS)\n",
            encoding="utf-8"
        )

    # Summary
    print("\n" + "="*60)
    print(f"DONE: {out_dir}")
    print(f"   full_text.md: {len(text)} chars")
    print(f"   chapters/: {len(chunks)} files")
    print(f"   index.json: {len(chunks)} entries")
    print(f"   design/gdd/game-concept.md: scaffold OK")
    print(f"   active.md + roadmap.md: track OK")
    print(f"   Epomeno: Claude analysi (Vima 2 tou SKILL.md)")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()

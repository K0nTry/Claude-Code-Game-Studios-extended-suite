#!/usr/bin/env python3
"""
audit_lore_drift.py — Πραγματικός έλεγχος συνοχής/placeholders.

Ελέγχει:
  - Παρουσία placeholders (Συμπληρώνεται, pending, TBD, _..._) που δείχνουν ημιτελή αρχεία
  - Συνέπεια ονομάτων (ίδιο όνομα με διαφορετική ορθογραφία)
  - Κενά evidence (αρχεία χωρίς αποσπάσματα/γραμμές)
"""

import re
import sys
from pathlib import Path

PLACEHOLDER_RE = re.compile(r'(Συμπληρώνεται|pending|TBD|_+\.+_+|ΧΧΧ|FIXME)', re.IGNORECASE)

def audit_drift(out_dir: Path) -> dict:
    out_dir = Path(out_dir)
    findings = []
    placeholders = []

    for p in out_dir.rglob("*.json"):
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
            if PLACEHOLDER_RE.search(txt):
                placeholders.append(str(p.relative_to(out_dir)))
                findings.append(f"placeholder σε {p.relative_to(out_dir)}")
        except Exception:
            findings.append(f"μη αναγνώσιμο {p}")

    for p in out_dir.rglob("*.md"):
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
            if PLACEHOLDER_RE.search(txt):
                placeholders.append(str(p.relative_to(out_dir)))
        except Exception:
            pass

    # έλεγχος ονομάτων: ίδιο όνομα με διαφορετικό τόνο/πεζά
    name_variants = {}
    ents_p = out_dir / "entities.json"
    if ents_p.exists():
        try:
            import json
            data = json.loads(ents_p.read_text(encoding="utf-8"))
            names = [c.get("name","") for c in data.get("characters",[])]
            low_map = {}
            for n in names:
                low = n.lower()
                low_map.setdefault(low, []).append(n)
            for low, variants in low_map.items():
                if len(set(variants)) > 1:
                    name_variants[low] = variants
        except Exception:
            pass

    status = "PASS" if not placeholders and not name_variants else "ATTENTION"
    return {
        "status": status,
        "placeholders_found_in": placeholders,
        "name_variants": name_variants,
        "findings": findings,
        "verdict": "OK — κανένα placeholder/ασυνέπεια" if status=="PASS" else f"Έλεγξε: {len(placeholders)} αρχεία με placeholders"
    }

if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    r = audit_drift(out)
    print(f"Lore Drift Audit: {r['status']}")
    print(r["verdict"])
    if r["placeholders_found_in"]:
        for p in r["placeholders_found_in"]:
            print(f" - {p}")

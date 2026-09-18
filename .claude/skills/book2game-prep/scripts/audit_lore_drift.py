#!/usr/bin/env python3
"""
audit_lore_drift.py — Adversarial έλεγχος κατά του Lore Drift.
Ελέγχει αν οι αυτόνομες δημιουργικές παρεμβολές ([GENERATED_CONNECTOR])
και τα framing devices παραβιάζουν τους πυλώνες του παιχνιδιού (game-pillars.md).
"""

import sys
import re
from pathlib import Path

def audit_drift(out_dir: Path) -> dict:
    pillars_file = out_dir / "design" / "gdd" / "game-pillars.md"
    connectors_file = out_dir / "lore" / "connectors.md"
    
    pillars_text = pillars_file.read_text(encoding="utf-8", errors="ignore") if pillars_file.exists() else ""
    connectors_text = connectors_file.read_text(encoding="utf-8", errors="ignore") if connectors_file.exists() else ""

    # Εντοπισμός connectors
    connectors = re.findall(r'\[GENERATED_CONNECTOR\](.*)', connectors_text)

    # Έλεγχος anti-pillars
    anti_pillars = ["grinding", "pay-to-win", "lore-breaking"]
    violations = []

    for conn in connectors:
        for ap in anti_pillars:
            if ap in conn.lower():
                violations.append(f"Πιθανή παραβίαση Anti-Pillar '{ap}': {conn.strip()}")

    status = "VERIFIED_PASS" if not violations else "DRIFT_DETECTED"
    
    return {
        "status": status,
        "connectors_checked": len(connectors),
        "violations": violations,
        "verdict": "Όλες οι δημιουργικές συνδέσεις υπακούουν στους πυλώνες." if not violations else "Εντοπίστηκαν παραβιάσεις lore."
    }

if __name__ == "__main__":
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    report = audit_drift(out_dir)
    print(f"Lore Drift Audit: {report['status']}")
    print(f"Verdict: {report['verdict']}")
    if report["violations"]:
        for v in report["violations"]:
            print(f" - {v}")
        sys.exit(1)
    sys.exit(0)

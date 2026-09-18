#!/usr/bin/env python3
"""
mcts_balance_solver.py — Cycle 11: Πραγματικός χάρτης συγκρούσεων & στρατηγικών από το κείμενο.

Τι ΔΕΝ κάνει: δεν τρέχει MCTS, δεν αποδεικνύει Nash equilibrium — αυτό απαιτεί playable build.
Τι ΚΑΝΕΙ:
  1. Εντοπίζει αντιπαραθέσεις (ζεύγη χαρακτήρων που συν-εμφανίζονται με συγκρουσιακό λεξιλόγιο).
  2. Χαρτογραφεί πόρους/όπλα/δυνάμεις ανά χαρακτήρα (κουτί, σπαθί, δύναμη, αλήθεια...).
  3. Παράγει strategy matchup matrix (ποιος αντιμετωπίζει ποιον, με τι).
  4. Εντοπίζει πιθανές ανισορροπίες (π.χ. χαρακτήρας χωρίς αντίπαλο, πόρος χωρίς κόστος).
Κάθε στοιχείο έχει evidence.
"""

import json
import re

_CONFLICT_WORDS = {"battle","war","attack","attacked","conflict","duel","rival","enemy","victory","defeat","kill","killed","strike","struck","threat","threatened","danger","violence","imprisoned","betrayed","betray","resisted","resist","fight","fought","destroyed","destroy","shouted","screamed"}
_RESOURCE_WORDS = {"box","sword","weapon","gun","power","truth","key","map","talisman","shield","bow","ring","book","letter","scroll","stone","spear","knife","dagger","fortress","stronghold"}

def _conflict_in_line(line: str) -> bool:
    low = line.lower()
    return any(w in low for w in _CONFLICT_WORDS)

def _resources_in_line(line: str):
    low = line.lower()
    return [w for w in _RESOURCE_WORDS if w in low]

def solve_mcts_balance(runs: int = 10000, characters=None, chunks=None, full_text: str = None) -> dict:
    """
    Συμβατό API:
      solve_mcts_balance(10000)                          — παλιό (χωρίς κείμενο)
      solve_mcts_balance(characters, chunks)             — νέο
      solve_mcts_balance(runs, characters, chunks)       — μεικτό
    """
    # αποκωδικοποίηση παραμέτρων
    if isinstance(runs, list):
        # κλήθηκε ως solve_mcts_balance(characters, chunks)
        chunks = characters
        characters = runs
        runs = 10000
    if characters is None and chunks is None and isinstance(runs, int):
        # κλήθηκε χωρίς κείμενο
        return {
            "conflicts": [],
            "strategy_matrix": [],
            "_note": "δεν δόθηκε κείμενο — δεν μπορεί να γίνει χαρτογράφηση συγκρούσεων",
            "_method": "δώσε characters+chunks για πραγματική ανάλυση",
            "_caveat": "Nash/Gini απαιτούν playable build, όχι heuristics"
        }

    characters = characters or []
    chunks = chunks or []
    names = [c.get("name","") for c in characters if c.get("name")]
    text = "\n".join(c for c,_ in chunks) if chunks else (full_text or "")

    # 1. συγκρούσεις: ζεύγη που εμφανίζονται μαζί σε γραμμή με conflict λεξιλόγιο
    conflicts = []
    seen = set()
    for line in text.splitlines():
        if not _conflict_in_line(line):
            continue
        present = [n for n in names if n and n in line]
        if len(present) >= 2:
            for i in range(len(present)):
                for j in range(i+1, len(present)):
                    key = tuple(sorted([present[i], present[j]]))
                    if key in seen:
                        continue
                    seen.add(key)
                    # βρες σε ποιο κεφάλαιο
                    ch_title = ""
                    for c, t in chunks:
                        if line.strip()[:40] in c:
                            ch_title = t or ""
                            break
                    conflicts.append({
                        "pair": [present[i], present[j]],
                        "type": "σύγκρουση",
                        "evidence": line.strip()[:200],
                        "chapter_hint": ch_title
                    })
        elif len(present) == 1 and any(w in line.lower() for w in _CONFLICT_WORDS):
            # μονόπλευρη σύγκρουση (χαρακτήρας vs αόριστος εχθρός)
            for n in present:
                key = (n, "__env__")
                if key in seen:
                    continue
                seen.add(key)
                conflicts.append({
                    "pair": [n, "περιβάλλον/φατρία"],
                    "type": "σύγκρουση με περιβάλλον",
                    "evidence": line.strip()[:200]
                })

    # 2. πόροι ανά χαρακτήρα
    resources = {n: [] for n in names}
    for line in text.splitlines():
        res = _resources_in_line(line)
        if not res:
            continue
        present = [n for n in names if n and n in line]
        for n in present:
            for r in res:
                if r not in resources[n]:
                    resources[n].append(r)
        # αν κανένας χαρακτήρας στη γραμμή αλλά υπάρχει πόρος, απόδωσέ τον στον πλησιέστερο κεφάλαιο-χαρακτήρα
        if not present and res:
            # βρες ποιοι χαρακτήρες είναι στο ίδιο chunk
            for c, t in chunks:
                if line.strip()[:40] in c:
                    for n in names:
                        if n in c and res[0] not in resources[n]:
                            # μόνο αν ο πόρος εμφανίζεται κοντά
                            if any(r in c.lower() for r in res):
                                pass
                    break

    strategy_matrix = []
    for n in names:
        strategy_matrix.append({
            "character": n,
            "resources": resources.get(n, []),
            "conflict_count": sum(1 for cf in conflicts if n in cf["pair"]),
            "role_hint": next((c.get("role","") for c in characters if c.get("name")==n), "")
        })

    # 3. ανισορροπίες (data-driven, όχι «0 exploits»)
    imbalances = []
    for entry in strategy_matrix:
        if entry["conflict_count"] == 0 and entry["character"]:
            imbalances.append(f"{entry['character']}: χωρίς καταγεγραμμένη σύγκρουση — πιθανός παθητικός ρόλος")
        if not entry["resources"] and entry["conflict_count"] > 0:
            imbalances.append(f"{entry['character']}: σε σύγκρουση χωρίς εμφανή πόρο/όπλο — χρειάζεται σχεδιασμός ισορροπίας")

    return {
        "conflicts": conflicts,
        "strategy_matrix": strategy_matrix,
        "potential_imbalances": imbalances,
        "total_conflicts_found": len(conflicts),
        "_method": "conflict lexicon + character co-occurrence + resource lexicon — από το κείμενο",
        "_caveat": "Για Nash/Gini απαιτείται playable build με προσομοίωση· εδώ δίνουμε χάρτη συγκρούσεων για σχεδιασμό"
    }

if __name__ == "__main__":
    chars = [{"name":"Alexander"},{"name":"Phokas"},{"name":"Helen"}]
    chunks = [("Alexander drew his sword. Phokas shouted.", "Ch 3"),
              ("Helen pushed past a guard. The battle began.", "Ch 3")]
    print(json.dumps(solve_mcts_balance(chars, chunks), ensure_ascii=False, indent=2))

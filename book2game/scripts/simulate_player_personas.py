#!/usr/bin/env python3
"""
simulate_player_personas.py — Cycle 8: Χαρτογράφηση βιβλίου σε αρχέτυπα παικτών (Bartle/Yee)
με EVIDENCE από το κείμενο. Δεν προβλέπει retention/Metacritic — δίνει προφίλ συμβατότητας.

Πώς μετράμε (0..1 ανά αρχέτυπο, από το κείμενο):
  Explorer:   πυκνότητα τοποθεσιών/κόσμου + περιγραφικές προτάσεις + μυστήρια/ανακαλύψεις
  Achiever:   στόχοι/αποστολές ("πρέπει", "σκοπός", "στόχος", λίστες, αριθμοί)
  Socializer: διάλογοι + σχέσεις + φατρίες + συναισθηματικό λεξιλόγιο
  Killer/Challenger: συγκρούσεις/μάχες + αποφάσεις υψηλού ρίσκου + ανταγωνισμός
Κάθε σκορ συνοδεύεται από evidence (αποσπάσματα) — όχι από «προβλέψεις».
"""

import json
import re

_EXPLORER_WORDS = {"discovery","discovered","mystery","hidden","secret","world","location","map","route","path","cave","temple","city","mountain","forest","island","ruins","ancient","uncover","revelation","explore","exploration"}
_ACHIEVER_WORDS = {"goal","purpose","mission","must","completion","collection","achievement","progress","level","reward","trophy","experience","grade","rank","ranking","training","trial","quest","objective"}
_SOCIAL_WORDS = {"friend","group","team","alliance","faction","relationship","dialogue","conversation","love","hate","betrayal","loyalty","family","brother","sister","father","mother","partner","companion"}
_KILLER_WORDS = {"battle","war","attack","conflict","duel","rival","enemy","victory","defeat","kill","strike","hunt","trap","ambush","strategy","tactics","power","weapon"}

def _score(text: str, vocab: set):
    low = text.lower()
    hits = [w for w in vocab if w in low]
    # κανονικοποίηση ανά 1000 λέξεις
    words = len(text.split()) or 1
    density = len(hits) / (words/1000)
    # 0..1 με κορεσμό
    score = min(0.95, 0.15 + density * 0.12)
    # μικρή ώθηση αν υπάρχουν πολλά αποσπάσματα
    if len(hits) >= 4:
        score = min(0.95, score + 0.08)
    return round(score, 2), hits[:5]

def _collect_evidence(text: str, vocab: set, limit=3):
    ev = []
    for line in text.splitlines():
        low = line.lower()
        if any(w in low for w in vocab):
            s = line.strip()
            if len(s) > 20:
                ev.append(s[:180])
                if len(ev) >= limit:
                    break
    return ev

def simulate_personas(chunks_or_profile=None, full_text: str = None) -> dict:
    """
    Συμβατό API:
      simulate_personas(chunks)            — από το pipeline (λίστα)
      simulate_personas(full_text_str)     — από δοκιμή
      simulate_personas(game_profile_dict) — παλιό (αγνοείται, δίνει ουδέτερο)
      simulate_personas()                  — κενό
    """
    text = ""
    if isinstance(chunks_or_profile, list):
        parts = []
        for item in chunks_or_profile:
            if isinstance(item, (list,tuple)) and len(item)==2:
                parts.append(item[0])
            elif isinstance(item, dict):
                parts.append(item.get("content",""))
            else:
                parts.append(str(item))
        text = "\n".join(parts) if parts else (full_text or "")
        if full_text:
            text = full_text + "\n" + text
    elif isinstance(chunks_or_profile, str) and chunks_or_profile.strip():
        text = chunks_or_profile if not full_text else chunks_or_profile + "\n" + full_text
    elif isinstance(chunks_or_profile, dict):
        # παλιό game_profile — δεν έχουμε κείμενο
        text = full_text or ""
    else:
        text = full_text or ""

    if not text.strip():
        return {
            "personas": [], "_note": "δεν δόθηκε κείμενο — δεν μπορεί να γίνει χαρτογράφηση",
            "_method": "δώσε chunks ή full_text"
        }

    quote_marks = text.count('"') + text.count("“") + text.count("”")
    dialog_density = quote_marks / max(1, len(text.splitlines()))
    # scores
    explorer_s, explorer_hits = _score(text, _EXPLORER_WORDS)
    achiever_s, achiever_hits = _score(text, _ACHIEVER_WORDS)
    social_s, social_hits = _score(text, _SOCIAL_WORDS)
    killer_s, killer_hits = _score(text, _KILLER_WORDS)

    # διάλογοι ενισχύουν Socializer
    if dialog_density > 0.05:
        social_s = min(0.95, social_s + 0.10)

    personas = [
        {
            "persona": "Explorer (Εξερευνητής)",
            "motivation": "Ανακάλυψη κόσμου, μυστικά, περιβάλλον",
            "compatibility_score": explorer_s,
            "top_signals": explorer_hits,
            "evidence": _collect_evidence(text, _EXPLORER_WORDS),
            "design_hint": "δυνατό αν explorer >0.55: έμφαση σε χάρτη/εξερεύνηση/κρυφά"
        },
        {
            "persona": "Achiever (Επιτευγματίας)",
            "motivation": "Στόχοι, αποστολές, πρόοδος, συλλογή",
            "compatibility_score": achiever_s,
            "top_signals": achiever_hits,
            "evidence": _collect_evidence(text, _ACHIEVER_WORDS),
            "design_hint": "δυνατό αν achiever >0.55: σαφείς αποστολές/ανταμοιβές"
        },
        {
            "persona": "Socializer (Κοινωνικός)",
            "motivation": "Σχέσεις, διάλογοι, φατρίες, ηθικές επιλογές",
            "compatibility_score": social_s,
            "top_signals": social_hits,
            "evidence": _collect_evidence(text, _SOCIAL_WORDS),
            "design_hint": "δυνατό αν social >0.55: διάλογοι/σχέσεις/συνέπειες"
        },
        {
            "persona": "Killer/Challenger (Ανταγωνιστής)",
            "motivation": "Σύγκρουση, πρόκληση, κυριαρχία σε συστήματα",
            "compatibility_score": killer_s,
            "top_signals": killer_hits,
            "evidence": _collect_evidence(text, _KILLER_WORDS),
            "design_hint": "δυνατό αν killer >0.55: μάχες/δυσκολία/στρατηγική"
        },
    ]
    personas.sort(key=lambda p: p["compatibility_score"], reverse=True)
    overall = round(sum(p["compatibility_score"] for p in personas)/4, 2)

    return {
        "personas": personas,
        "overall_player_fit_score": overall,
        "top_fit": personas[0]["persona"] if personas else None,
        "_method": "λεξιλόγιο ανά αρχέτυπο + πυκνότητα ανά 1000 λέξεις + evidence αποσπάσματα",
        "_caveat": "Δεν προβλέπει retention/Metacritic — αυτά απαιτούν playtest, όχι heuristics"
    }

if __name__ == "__main__":
    import sys
    from pathlib import Path
    if len(sys.argv) > 1:
        txt = Path(sys.argv[1]).read_text(encoding="utf-8")
        print(json.dumps(simulate_personas(txt), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(simulate_personas("The battle was fierce. Alexander must complete the mission. His friends are waiting for him."), ensure_ascii=False, indent=2))

#!/usr/bin/env python3
"""
simulate_pacing_tension.py — Cycle 6: Πραγματική καμπύλη έντασης από το κείμενο.

Δεν φτιάχνει τριγωνομετρικές καμπύλες από το πλήθος κεφαλαίων.
Μετράει ανά κεφάλαιο:
  - πυκνότητα ρημάτων δράσης / σύγκρουσης
  - θαυμαστικά, ερωτηματικά, αποσιωπητικά
  - μήκος προτάσεων (κοντές = ένταση, μακρές = ανάπαυλα)
  - αρνητικό/θετικό λεξιλόγιο
  - διάλογοι vs αφήγηση
Και παράγει μια καμπύλη με evidence (κορυφαίες λέξεις-σήματα ανά κεφάλαιο).
"""

import json
import re
from pathlib import Path

_ACTION_VERBS = {
    "έτρεξε","περπάτησε","χτύπησε","χτύπησα","μάχη","πόλεμος","επίθεση","επιτέθηκε",
    "σκότωσε","σκοτώσει","απειλή","απειλεί","κίνδυνος","ουρλιαξε","ούρλιαξε","φώναξε",
    "βρόντηξε","έσπρωξε","τράβηξε","άνοιξαν","βρυχηθμό","πολεμήσω","πολεμήσει","μάχομαι",
    "τρέχω","τρέχει","κυνηγώ","φεύγω","κρύβομαι","χτυπά","ρίχνω","ρίχνει","σπάω","σπάει",
    "fight","attack","run","kill","shout","scream","hit","strike","battle","war"
}
_TENSION_PUNCT = re.compile(r'[!¡‼]+')
_QUESTION_RE = re.compile(r'[?？;]+')
_SENT_SPLIT = re.compile(r'(?<=[.!?…])\s+')
_NEG_WORDS = {"φόβος","σκοτειν","απειλή","κίνδυνος","θάνατος","σκιά","σκότος","μάχη","πόλεμος","βία","εχθρός","αίμα","φωτιά","στάχτη","θειάφι","σιδερέν","βρυχηθμ","ουρλια"}
_POS_WORDS = {"ελπίδα","φως","αυγή","χαρά","αγάπη","ειρήνη","ελευθερία","νίκη","χαμόγελο","ήλιος","ζεστασιά"}


def _score_chunk(text: str):
    sents = [s.strip() for s in _SENT_SPLIT.split(text) if s.strip()]
    n_sents = len(sents) if sents else 1
    words = text.split()
    n_words = len(words) if words else 1
    avg_len = n_words / n_sents
    # δράση
    low = text.lower()
    action_hits = sum(1 for v in _ACTION_VERBS if v in low)
    action_density = action_hits / max(1, n_sents)
    # στίξη
    punct_hits = len(_TENSION_PUNCT.findall(text))
    punct_density = punct_hits / n_sents
    q_hits = len(_QUESTION_RE.findall(text))
    # μήκος: κοντές προτάσεις -> ένταση
    short_ratio = sum(1 for s in sents if len(s.split()) <= 8) / n_sents
    # λεξιλόγιο
    neg_hits = sum(1 for w in _NEG_WORDS if w in low)
    pos_hits = sum(1 for w in _POS_WORDS if w in low)
    neg_density = neg_hits / n_sents
    pos_density = pos_hits / n_sents
    # διάλογοι
    dialog_density = text.count("«") / n_sents

    # σύνθεση 0..1 (βάρη επιλεγμένα για διακριτότητα, όχι για «άριστο σκορ»)
    raw = (
        action_density * 0.30 +
        punct_density * 0.25 +
        short_ratio * 0.15 +
        neg_density * 0.15 +
        dialog_density * 0.10 +
        min(0.15, q_hits / n_sents * 2)
    )
    # αντίβαρο θετικού λεξιλογίου
    raw = raw - pos_density * 0.10
    # κανονικοποίηση
    tension = max(0.05, min(0.95, 0.25 + raw * 1.1))

    # σήματα για evidence
    signals = []
    if action_hits:
        top_actions = [v for v in _ACTION_VERBS if v in low][:4]
        signals.append(f"δράση: {', '.join(top_actions)}")
    if punct_hits:
        signals.append(f"έντονη στίξη ×{punct_hits}")
    if short_ratio > 0.35:
        signals.append(f"κοντές προτάσεις {round(short_ratio*100)}%")
    if neg_hits:
        top_neg = [w for w in _NEG_WORDS if w in low][:3]
        signals.append(f"αρνητικό λεξιλόγιο: {', '.join(top_neg)}")
    if dialog_density > 0.15:
        signals.append(f"διάλογοι {round(dialog_density*100)}% των προτάσεων")

    return round(tension, 3), {
        "avg_sentence_words": round(avg_len, 1),
        "action_hits": action_hits,
        "punct_hits": punct_hits,
        "neg_hits": neg_hits,
        "pos_hits": pos_hits,
        "short_sentence_ratio": round(short_ratio, 2),
        "signals": signals or ["ήρεμη αφήγηση / περιγραφή"]
    }


def simulate_pacing(chunks_or_count, full_text: str = None):
    """
    Δέχεται είτε (chunks: list[(content,title)]) είτε (chapter_count: int) για συμβατότητα.
    Αν δοθεί full_text, χρησιμοποιείται για επιπλέον σήματα. Αλλιώς μόνο chunks.
    """
    # συμβατότητα με παλιό API: simulate_pacing(3)
    if isinstance(chunks_or_count, int):
        n = chunks_or_count
        # fallback χωρίς κείμενο: ουδέτερη καμπύλη με σαφή σήμανση
        curve = []
        for i in range(n):
            curve.append({
                "chapter_index": i+1,
                "chapter_title": f"Κεφάλαιο {i+1}",
                "tension_score": 0.5,
                "signals": ["καμία ανάλυση κειμένου — δόθηκε μόνο αριθμός κεφαλαίων"],
                "note": "δώσε chunks+text για πραγματική μέτρηση"
            })
        return {
            "model": "text-grounded tension per chapter (no text provided — neutral fallback)",
            "tension_curve": curve,
            "_caveat": "Για πραγματική καμπύλη πέρασε chunks+full_text"
        }

    chunks = chunks_or_count or []
    if not chunks:
        return {"model": "no chunks", "tension_curve": [], "_note": "κανένα κεφάλαιο"}

    curve = []
    for idx, item in enumerate(chunks, 1):
        if isinstance(item, (list, tuple)) and len(item) == 2:
            content, title = item
        elif isinstance(item, dict):
            content, title = item.get("content",""), item.get("title","")
        else:
            content, title = str(item), f"Κεφάλαιο {idx}"
        score, detail = _score_chunk(content)
        # σύντομο απόσπασμα για proof
        snippet = content.strip().splitlines()[0][:120] if content.strip() else ""
        curve.append({
            "chapter_index": idx,
            "chapter_title": title or f"Κεφάλαιο {idx}",
            "tension_score": score,
            "detail": detail,
            "evidence_snippet": snippet
        })

    # dead-zone: πόσα διαδοχικά κεφάλαια έχουν σχεδόν ίδια ένταση (διαφορά <0.08)
    dead = 0
    for i in range(1, len(curve)):
        if abs(curve[i]["tension_score"] - curve[i-1]["tension_score"]) < 0.08:
            dead += 1
    dead_zone = round(dead / max(1, len(curve)-1), 3) if len(curve) > 1 else 0.0

    # flow label per chapter
    for c in curve:
        s = c["tension_score"]
        if s > 0.72:
            c["flow_label"] = "κορύφωση / αγώνας"
        elif s > 0.50:
            c["flow_label"] = "ένταση / πρόκληση"
        elif s > 0.32:
            c["flow_label"] = "ισορροπία / διερεύνηση"
        else:
            c["flow_label"] = "ανάπαυλα / περισυλλογή"

    return {
        "model": "lexical tension per chapter (verbs, punctuation, sentence length, vocab)",
        "tension_curve": curve,
        "pacing_dead_zone_index": dead_zone,
        "_method": "κάθε κεφάλαιο μετράται ξεχωριστά από το κείμενό του — όχι τριγωνομετρία",
        "_note": "Για economia/gini χρειάζεται πραγματικό game design — εδώ δίνουμε μόνο pacing"
    }


if __name__ == "__main__":
    import sys
    from pathlib import Path as _P
    if len(sys.argv) > 1:
        txt = _P(sys.argv[1]).read_text(encoding="utf-8")
        # δοκίμασε ως full_text chunk
        print(json.dumps(simulate_pacing([(txt, "Δείγμα")]), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(simulate_pacing(3), ensure_ascii=False, indent=2))

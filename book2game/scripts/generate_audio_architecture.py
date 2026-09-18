#!/usr/bin/env python3
"""
generate_audio_architecture.py — Cycle 9: Πραγματική αισθητηριακή χαρτογράφηση από το κείμενο.

Αντί για σταθερά 3 leitmotifs με modulo, βγάζει:
  1. Top keywords (εκτός stopwords) ανά συχνότητα — αυτά είναι τα θέματα.
  2. Αντιστοίχιση ανά κεφάλαιο (ποια θέματα κυριαρχούν πού).
  3. Tone per chapter (dark vs bright λεξιλόγιο) για πρόταση φωτισμού/LUT.
Κάθε στοιχείο έχει evidence (αποσπάσματα).
"""

import json
import re
from collections import Counter

_STOP = {
    "και","να","το","την","τον","της","του","τα","οι","ο","η","με","σε","από","για","που","ως","στο",
    "στη","στον","στην","στα","δεν","είναι","ήταν","θα","έχει","είχε","έχω","αυτό","αυτή","αυτός","ότι",
    "όταν","αν","ή","αλλά","όμως","είμαι","είσαι","είμαστε","είστε","είχα","είχες","ένα","μια","ένας",
    "της","τους","μας","σας","μου","σου","του","της","κεφάλαιο","chapter","the","and","a","an","is","are","was","were","in","on","at","to","of","for"
}
_DARK_WORDS = {"σκοτειν","σκιά","σκότος","μαύρο","νύχτα","ομίχλη","στάχτη","θειάφι","σιδερέν","βρυχηθμ","απειλή","φόβος","θάνατος","αίμα","κρύο","παγωμέν","σκοτειν","σκιερός"}
_BRIGHT_WORDS = {"φως","αυγή","ήλιος","λαμπερό","ζεστασιά","χαρά","ελπίδα","λευκό","χρυσό","καθαρό","φωτεινό","άνθιση","γαλάζιο"}

_WORD_RE = re.compile(r'[Α-Ωα-ωA-Za-z]{3,}')

def _keywords(text: str, top_n=12):
    words = [w.lower() for w in _WORD_RE.findall(text)]
    filtered = [w for w in words if w not in _STOP and len(w) > 3]
    cnt = Counter(filtered)
    return cnt.most_common(top_n)

def _tone(text: str):
    low = text.lower()
    dark = sum(1 for w in _DARK_WORDS if w in low)
    bright = sum(1 for w in _BRIGHT_WORDS if w in low)
    if dark > bright + 1:
        return "σκοτεινός / δραματικός", dark, bright
    if bright > dark + 1:
        return "φωτεινός / ελπιδοφόρος", dark, bright
    return "ισορροπημένος", dark, bright

def generate_audio_architecture(chunks, full_text: str = None) -> dict:
    """
    chunks: list[(content, title)]
    full_text: προαιρετικό (για global keywords)
    """
    if not chunks:
        return {"leitmotif_matrix": [], "_note": "κανένα κεφάλαιο"}

    # global keywords από όλο το κείμενο
    all_text = "\n".join(c for c,_ in chunks) if chunks else (full_text or "")
    global_kw = _keywords(all_text)

    leitmotifs = []
    lighting = []

    for idx, (content, title) in enumerate(chunks, 1):
        t = title or f"Κεφάλαιο {idx}"
        kw = _keywords(content, top_n=5)
        tone_label, dark, bright = _tone(content)
        # evidence: 1-2 γραμμές όπου εμφανίζεται το top keyword
        ev = []
        if kw:
            top_w = kw[0][0]
            for line in content.splitlines():
                if top_w in line.lower() and len(line.strip()) > 20:
                    ev.append(line.strip()[:160])
                    if len(ev) >= 2:
                        break
        # leitmotif πρόταση: θέμα = top keywords, όχι σταθερό "Το Μέλλον / Μυστήριο"
        leitmotifs.append({
            "chapter_index": idx,
            "chapter_title": t,
            "top_keywords": [{"word": w, "count": c} for w, c in kw],
            "dominant_theme": kw[0][0] if kw else "—",
            "tone": tone_label,
            "evidence": ev,
            "audio_hint": "χαμηλό/σκοτεινό pad" if "σκοτειν" in tone_label else "φωτεινό/ελπιδοφόρο layer" if "φωτειν" in tone_label else "ουδέτερο ambient"
        })
        # lighting
        lut = "Noir / desaturated" if "σκοτειν" in tone_label else "Warm / natural" if "φωτειν" in tone_label else "Neutral cinematic"
        lighting.append({
            "chapter_index": idx,
            "chapter_title": t,
            "tone": tone_label,
            "dark_hits": dark, "bright_hits": bright,
            "lut_suggestion": lut,
            "evidence": ev[:1]
        })

    return {
        "global_keywords": [{"word": w, "count": c} for w, c in global_kw],
        "leitmotif_matrix": leitmotifs,
        "lighting_color_script": lighting,
        "_method": "συχνότητα λέξεων (εκτός stopwords) + dark/bright λεξιλόγιο ανά κεφάλαιο — όχι presets",
        "_note": "Για τελική μουσική/φωτισμό χρειάζεται art direction· εδώ δίνουμε χαρτογράφηση θεμάτων"
    }

if __name__ == "__main__":
    demo = [("Ο Αλέξανδρος περπάτησε στο σκοτεινό λιμάνι. Η σκιά τον ακολουθούσε.", "Κεφ 1"),
            ("Το φως της αυγής έλουσε την Ακρόπολη. Η ελπίδα επέστρεψε.", "Κεφ 2")]
    print(json.dumps(generate_audio_architecture(demo), ensure_ascii=False, indent=2))

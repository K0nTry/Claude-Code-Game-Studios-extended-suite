#!/usr/bin/env python3
"""
character_psychology.py — Cycle 5: Ψυχολογική Αρχιτεκτονική & Αποτύπωμα Φωνής
ΠΡΑΓΜΑΤΙΚΗ ανάλυση από το κείμενο. Κάθε χαρακτηριστικό έχει απόδειξη (evidence).

Πώς μετράμε:
  1. Μαζεύουμε όλους τους διαλόγους κάθε ομιλητή από το full_text
     (pattern «…», είπε/ρώτησε/απάντησε ο/η Χ)
  2. Voice fingerprints: μέσο μήκος πρότασης, τύπος-προς-προτάσεις (TTR), πυκνότητα διαλόγου
  3. Big-5 proxies (0-100): Openness από ερωτήσεις/διερεύνηση,
     Conscientiousness από οργανωτικό λεξιλόγιο, Extraversion από όγκο/ρυθμό λόγου,
     Agreeableness από κοινωνικές λέξεις, Neuroticism από αρνητικό συναίσθημα.
     Σημείωση: proxies — για ψυχομετρική ακρίβεια LLM enrichment.
  4. Relationship matrix: co-occurrence ανά κεφάλαιο + σαφή αποσπάσματα
"""

import json
import re
from collections import Counter, defaultdict

_DIALOGUE_RE = re.compile(r'[«“"]([^»”"]+)[»”"]')
# «…», είπε/ρώτησε ο/η Χ  |  είπε ο/η Χ ... «…»
_VERB_RE = r'(?:είπε|απάντησε|ρώτησε|γέλασε|βρόντηξε|ψιθύρισε|ούρλιαξε|φώναξε|σκέφτηκε|παρατήρησε|συμπλήρωσε|αναρωτήθηκε|μουρμούρισε|διέταξε|πρόσταξε|συμβούλεψε|ψιθύρισε)'
_ATTR_AFTER = re.compile(rf'[»”]\s*,?\s*{_VERB_RE}\s+(?:ο|η)\s+([Α-ΩA-Z][α-ωά-ώa-z]+)', re.IGNORECASE)
_ATTR_BEFORE = re.compile(rf'{_VERB_RE}\s+(?:ο|η)\s+([Α-ΩA-Z][α-ωά-ώa-z]+)[^«»]*[«“]', re.IGNORECASE)

_OPEN_Q = set()
_OPEN_WORDS = {"γιατί","πώς","ποιο","ποιος","πού","πότε","άραγε","σκέφτηκα","αναρωτήθηκα","μήπως","ίσως","ίσως","βέβαια","αλήθεια"}
_CONSC_WORDS = {"πρέπει","οργάνωση","σχέδιο","πρόγραμμα","τακτική","ακριβώς","προσεκτικά","μεθοδικά","σταθερά","πειθαρχία","κανόνας","καθήκον","υποχρέωση","έλεγχος"}
_EXTRA_BONUS = re.compile(r'[!…]+')
_AGREE_WORDS = {"ευχαριστώ","συγγνώμη","παρακαλώ","βοήθεια","μαζί","φίλος","αγάπη","καλός","καλή","ευγενικός","φιλικός","στήριξη","κατανόηση","συγχώρεση","ειρήνη"}
_NEURO_WORDS = {"φόβος","άγχος","ανησυχία","τρέμω","πανικός","απελπισία","θυμός","μίσος","κλάμα","δάκρυ","σκιερός","σκοτεινός","απειλή","κίνδυνος","πόνος","εφιάλτης","μοναξιά"}

def _extract_dialogues(full_text: str):
    """Επιστρέφει {όνομα: [διάλογοι]} + {όνομα: [αποσπάσματα με evidence]}"""
    by_speaker = defaultdict(list)
    evidence = defaultdict(list)
    lines = full_text.splitlines()
    for ln, line in enumerate(lines, 1):
        for m in _DIALOGUE_RE.finditer(line):
            dialog = m.group(1).strip()
            if len(dialog) < 3:
                continue
            # ψάξε attribution στο ίδιο line
            attr = _ATTR_AFTER.search(line[m.end():]) or _ATTR_AFTER.search(line)
            if attr:
                speaker = attr.group(1)
                by_speaker[speaker].append(dialog)
                evidence[speaker].append({"quote": dialog[:160], "line": ln, "context": line.strip()[:200]})
            else:
                # δοκίμασε πριν τον διάλογο
                before = line[:m.start()]
                b = re.search(rf'{_VERB_RE}\s+(?:ο|η)\s+([Α-ΩA-Z][α-ωά-ώa-z]+)', before, re.IGNORECASE)
                if b:
                    speaker = b.group(1)
                    by_speaker[speaker].append(dialog)
                    evidence[speaker].append({"quote": dialog[:160], "line": ln, "context": line.strip()[:200]})
    return by_speaker, evidence

def _ttr_score(tokens):
    if not tokens:
        return 0.0
    return len(set(t.lower() for t in tokens)) / len(tokens)

def _avg_words(dialogs):
    if not dialogs:
        return 0
    total = sum(len(d.split()) for d in dialogs)
    return round(total / len(dialogs), 1)

def _big5_proxy(dialogs, all_tokens, char_name, full_text_lower, total_chars):
    """Proxy scores 0-100, με εξήγηση πώς υπολογίστηκαν."""
    joined = " ".join(dialogs).lower() if dialogs else ""
    tokens_lower = [t.lower() for t in all_tokens] if all_tokens else []
    # Openness: ερωτήσεις + διερευνητικό λεξιλόγιο + TTR
    q_marks = joined.count("?") + joined.count(";")
    open_hits = sum(1 for w in _OPEN_WORDS if w in joined)
    ttr = _ttr_score(all_tokens) if all_tokens else 0
    openness = min(95, 35 + q_marks*8 + open_hits*6 + int(ttr*20))
    # Conscientiousness: οργανωτικό λεξιλόγιο + μέσο μήκος (δομημένος λόγος)
    consc_hits2 = sum(1 for w in _CONSC_WORDS if w in joined)
    avg = _avg_words(dialogs) if dialogs else 0
    conscientiousness = min(95, 35 + consc_hits2*10 + (1 if avg > 10 else 0)*8)
    # Extraversion: όγκος διαλόγου + θαυμαστικά/αποσιωπητικά + σύντομες εκρήξεις
    vol = len(dialogs)
    punct_energy = len(_EXTRA_BONUS.findall(joined))
    extraversion = min(95, 30 + vol*6 + punct_energy*5 + (8 if avg < 7 and vol > 2 else 0))
    # Agreeableness: κοινωνικές/θετικές λέξεις
    agree_hits = sum(1 for w in _AGREE_WORDS if w in joined)
    agreeableness = min(95, 40 + agree_hits*9)
    # Neuroticism: αρνητικό συναίσθημα
    neuro_hits2 = sum(1 for w in _NEURO_WORDS if w in joined)
    neuroticism = min(90, 25 + neuro_hits2*12)
    return {
        "openness": int(openness),
        "conscientiousness": int(conscientiousness),
        "extraversion": int(extraversion),
        "agreeableness": int(agreeableness),
        "neuroticism": int(neuroticism),
        "_method": "lexical proxies from dialogue (questions, social/organizing/negative vocab, TTR, volume)",
        "_note": "Για κλινική ακρίβεια Big-5 απαιτείται LLM enrichment — εδώ δίνουμε ανιχνεύσιμα proxies"
    }

def _vocab_tier(ttr, avg):
    if ttr > 0.75 and avg > 12:
        return "Πλούσιο / Λογοτεχνικό"
    if ttr > 0.55:
        return "Μεσαίο / Εκφραστικό"
    if avg < 7:
        return "Λιτός / Κοφτός"
    return "Τυπικό / Αφηγηματικό"

def _rhythm(avg, vol):
    if avg == 0:
        return "σιωπηλός (καμία άμεση ατάκα στο κείμενο)"
    if avg < 7:
        return "κοφτός, εκρηκτικός — σύντομες ατάκες"
    if avg < 11:
        return "ισορροπημένος — φυσικός διάλογος"
    if avg < 16:
        return "στοχαστικός — μακρές φράσεις"
    return "ρητορικός — εκτενείς μονόλογοι"

def generate_character_psychology(characters: list, full_text: str = "") -> dict:
    text = full_text or ""
    lower = text.lower()
    by_speaker, ev_map = _extract_dialogues(text)

    psychology = {}
    voices = {}
    rel_matrix = []

    # κανονικοποίησε ονόματα (case-insensitive match)
    speaker_keys_lower = {k.lower(): k for k in by_speaker}

    for char in characters:
        name = char.get("name", "—")
        role = char.get("role", "NPC")
        key = speaker_keys_lower.get(name.lower())
        dialogs = by_speaker.get(key, []) if key else []
        evs = ev_map.get(key, []) if key else []
        # αν δεν βρέθηκε ακριβές match, ψάξε substring
        if not dialogs:
            for k, v in by_speaker.items():
                if name.lower() in k.lower() or k.lower() in name.lower():
                    dialogs = v
                    evs = ev_map[k]
                    break
        tokens = " ".join(dialogs).split() if dialogs else []
        avg = _avg_words(dialogs)
        ttr = _ttr_score(tokens)
        big5 = _big5_proxy(dialogs, tokens, name, lower, len(text))

        # moral & flaw από proxies (όχι σταθερά)
        if big5["agreeableness"] > 65:
            moral = "Καλόκαρδος / Προστατευτικός"
        elif big5["conscientiousness"] > 70:
            moral = "Πειθαρχημένος / Καθήκον"
        elif big5["neuroticism"] > 55:
            moral = "Συγκρουσιακός / Παρορμητικός"
        else:
            moral = "Πραγματιστής / Ουδέτερος"

        if big5["neuroticism"] > 60:
            flaw = "Ευάλωτος στο άγχος / παρορμητικές αποφάσεις"
        elif big5["conscientiousness"] > 75:
            flaw = "Άκαμπτος / δυσκολία προσαρμογής"
        elif big5["openness"] < 45:
            flaw = "Συντηρητικός / αποφεύγει το ρίσκο"
        else:
            flaw = "Ιδεαλιστής / υπερεκτιμά τους άλλους"

        desire = "Αναζήτηση αλήθειας" if big5["openness"] > 65 else "Προστασία των δικών του" if big5["agreeableness"] > 60 else "Απόδειξη αξίας / αναγνώριση"

        psychology[name] = {
            "name": name, "role": role,
            "big_five": {k: v for k, v in big5.items() if not k.startswith("_")},
            "big_five_method": big5["_method"],
            "big_five_note": big5["_note"],
            "moral_alignment": moral,
            "core_flaw": flaw,
            "driving_desire": desire,
            "dialogue_count": len(dialogs),
            "evidence_dialogues": evs[:4]
        }
        voices[name] = {
            "name": name,
            "speech_rhythm": _rhythm(avg, len(dialogs)),
            "avg_sentence_length_words": avg if dialogs else 0,
            "vocabulary_tier": _vocab_tier(ttr, avg) if dialogs else "— (καμία άμεση ατάκα)",
            "type_token_ratio": round(ttr, 3) if tokens else 0,
            "dialogue_count": len(dialogs),
            "sample_quotes": [e["quote"] for e in evs[:3]],
            "method": "μετρήθηκε από διαλόγους «…» που αποδίδονται στον χαρακτήρα στο κείμενο"
        }

    # relationship matrix — μόνο από πραγματικό κείμενο
    if len(characters) >= 2:
        # co-occurrence per chapter proxy: split by chapter headings
        ch_re = re.compile(r'^(?:#+\s+.*|ΚΕΦΑΛΑΙΟ.*|Chapter.*)$', re.MULTILINE | re.IGNORECASE)
        parts = ch_re.split(text)
        for i in range(len(characters)):
            for j in range(i+1, len(characters)):
                a = characters[i].get("name",""); b = characters[j].get("name","")
                co = sum(1 for p in parts if a in p and b in p)
                total = len(parts) if parts else 1
                together = round(co/total, 2)
                # βρες 1-2 αποσπάσματα όπου εμφανίζονται μαζί
                together_quotes = []
                for line in text.splitlines():
                    if a in line and b in line:
                        together_quotes.append(line.strip()[:160])
                        if len(together_quotes) >= 2:
                            break
                rel_matrix.append({
                    "source": a, "target": b,
                    "co_occurrence_ratio": together,
                    "shared_chapters": co,
                    "evidence": together_quotes,
                    "note": "co-occurrence = σε πόσα κεφάλαια/ενότητες εμφανίζονται μαζί"
                })

    return {
        "psychology": psychology,
        "voice_fingerprints": voices,
        "relationship_matrix": rel_matrix,
        "_method": "dialogue extraction + lexical proxies (TTR, length, vocab hits) — όχι presets",
        "_caveat": "Big-5 εδώ είναι proxies· για αφηγηματική ακρίβεια χρειάζεται LLM enrichment πάνω στα evidence"
    }

if __name__ == "__main__":
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else None
    if p:
        from pathlib import Path
        txt = Path(p).read_text(encoding="utf-8")
        chars = [{"name": n} for n in ["Αλέξανδρος","Ελένη","Δημήτρης","Φωκάς"]]
        print(json.dumps(generate_character_psychology(chars, txt), ensure_ascii=False, indent=2))

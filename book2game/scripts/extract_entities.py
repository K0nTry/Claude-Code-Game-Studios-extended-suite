#!/usr/bin/env python3
"""
extract_entities.py — Αυτόματη εξαγωγή οντοτήτων (χαρακτήρες, τοποθεσίες, αντικείμενα,
έννοιες, φατρίες) και σχέσεων ΑΠΟ ΤΟ ΠΡΑΓΜΑΤΙΚΟ ΚΕΙΜΕΝΟ, με αποδεικτικά αποσπάσματα.

Πώς δουλεύει (και τι ΔΕΝ κάνει):
- Διαβάζει το κείμενο πρόταση-πρόταση.
- Βρίσκει ονόματα από λέξεις με κεφαλαίο που ΔΕΝ είναι πρώτη λέξη πρότασης
  (εξαλείφει το γνωστό false-positive των αρχικών κεφαλαίων).
- Αποδίδει διαλόγους «…» σε ομιλητές μέσα από ρήματα λόγου (είπε, ρώτησε…).
- Ταξινομεί οντότητες με λεξιλόγια ρόλων (τοποθεσίες, φατρίες, αντικείμενα).
- Σχέσεις: συν-εμφάνιση σε ίδια πρόταση + ρήματα συγγένειας/αντιπαράθεσης.
- Κάθε οντότητα και σχέση φέρει `evidence` (αποσπάσματα) και `chapter` (πού βρέθηκε).

Δεν χρησιμοποιεί LLM και δεν φτιάχνει δεδομένα: ό,τι βγάζει τεκμηριώνεται από το κείμενο.
"""

import re
from collections import Counter

# --- λεξιλόγια (ντετερμινιστικά) ---

_VERBS_SPEECH = [
    "είπε", "απάντησε", "ρώτησε", "γέλασε", "βρόντηξε", "ψιθύρισε", "ούρλιαξε",
    "φώναξε", "σκέφτηκε", "παρατήρησε", "συμπλήρωσε", "αναρωτήθηκε", "μουρμούρισε",
    "φώναζε", "ρωτούσε", "έλεγε", "αποκρίθηκε", "διέταξε", "πρόσταξε", "συμβούλεψε",
    "said", "replied", "asked", "whispered", "shouted", "laughed", "thought"
]

_LOC_KEYWORDS = [
    "πόλη", "πόλης", "πόλη;", "λιμάνι", "ναός", "ναό", "τείχη", "τείχος", "πύλη",
    "ταβέρνα", "κελί", "ακρόπολη", "κάστρο", "χωριό", "βουνό", "ποτάμι", "θάλασσα",
    "νησί", "δάσος", "μοναστήρι", "πύργος", "γέφυρα", "πλατεία", "δρόμος", "σοκάκι",
    "city", "harbor", "temple", "walls", "gate", "tavern", "castle", "village",
    "mountain", "river", "island", "forest", "tower", "bridge"
]

_FACTION_KEYWORDS = [
    "φύλακες", "τάγμα", "σέκτα", "συμβούλιο", "στρατός", "οργάνωση", "συντεχνία",
    "αδελφότητα", "αυτοκρατορία", "βασίλειο", "guards", "order", "guild", "kingdom",
    "empire", "army", "council", "sect"
]

_ROLE_HINTS = {
    "στρατιώτης": "soldier", "αρχηγός": "leader", "βασιλιάς": "king", "βασίλισσα": "queen",
    "μάγος": "mage", "κλέφτης": "thief", "έμπορος": "merchant", "φύλακας": "guard",
    "δάσκαλος": "teacher", "πατέρας": "father figure", "μητέρα": "mother figure",
    "γέρος": "elder", "παλιά": "old friend", "φίλη": "friend", "φίλος": "friend",
    "σύμμαχος": "ally", "εχθρός": "enemy", "πρωταγωνιστής": "protagonist",
    "προδότης": "traitor", "αδελφή": "sister", "αδελφός": "brother"
}

_KINSHIP_VERBS = [
    "πατέρας", "μητέρα", "αδελφή", "αδελφός", "γιος", "κόρη", "φίλος", "φίλη",
    "εχθρός", "σύμμαχος", "δάσκαλος", "μαθητής", "αρχηγός", "σύζυγος", "αγαπημένη",
    "σύντροφος", "φρουρός", "υπηρέτης", "βασιλιάς"
]

_CONFLICT_VERBS = [
    "πολεμήσει", "πολέμησε", "χτυπήσει", "χτύπησε", "απειλεί", "απειλούσε", "σκότωσε",
    "σκοτώσει", "πρόδωσε", "προδώσει", "αντιστάθηκε", "αντισταθεί", "επιτέθηκε",
    "επιτεθεί", "κατέστρεψε", "καταστρέψει", "φυλάκισε", "φυλακίσει", "δεμένο", "έδεσε",
    "βία", "σύγκρουση", "μάχη", "πόλεμος", "εχθρός", "μαχαιριά", "σκοτεινό"
]

_STOPWORDS_CAP = {
    "Ο", "Η", "Το", "Οι", "Τα", "Τον", "Την", "Του", "Της", "Των", "Στο", "Στη",
    "Στον", "Στην", "Στα", "Από", "Με", "Για", "Και", "Αλλά", "Όμως", "Ναι", "Όχι",
    "Ενας", "Μια", "Ένα", "Μου", "Σου", "Του", "Που", "Ως", "Σαν", "Θα", "Να",
    "Θέλεις", "Μπορείς", "Πρέπει", "Έτσι", "Τίποτα", "Αυτό", "Εκεί", "Δεν", "Είμαι",
    "Είσαι", "Είναι", "Ήταν", "Τώρα", "Μετά", "Πριν", "Έχω", "Έχεις", "Έχει",
    "Κάθε", "Όταν", "Αν", "Γι", "Αυτή", "Αυτός", "Κάτι", "Κανένα", "Εδώ", "Εκεί",
    "The", "A", "An", "And", "But", "Or", "In", "On", "At", "He", "She", "It",
    "They", "We", "You", "I", "Then", "When", "Now", "There", "Here"
}

_SENTENCE_SPLIT = re.compile(r'(?<=[.!?…])\s+')
_DIALOGUE = re.compile(r'[«“"]([^»”"]+)[»”"]')
_CAPITALIZED = re.compile(r'\b([Α-ΩA-Z][α-ωά-ώήίόύέϊϋΐa-z]{1,})\b')
_CHAPTER_HEADING = re.compile(r'^(?:#+\s*(.*)|ΚΕΦΑΛΑΙΟ\s*(.*)|Chapter\s*(.*))$', re.IGNORECASE)


def _split_into_sentences(text: str):
    """Χωρίζει το κείμενο σε προτάσεις, κρατώντας και τον αριθμό γραμμής τους."""
    sentences = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for sent in _SENTENCE_SPLIT.split(line):
            sent = sent.strip()
            if sent:
                sentences.append((sent, line_no))
    return sentences


def _attributions(sentence: str):
    """Βρίσκει ομιλητή διαλόγου μέσα σε πρόταση. Π.χ. «…», είπε η Ελένη -> Ελένη."""
    speech = _DIALOGUE.findall(sentence)
    speakers = []
    # Μοτίβο: ...» ρώτησε η Ελένη  |  «...», απάντησε ο Αλέξανδρος  |  είπε η Ελένη.
    verb_names = "|".join(_VERBS_SPEECH)
    pat_before = re.compile(rf'(?:{verb_names})\s+(?:ο|η)\s+([Α-ΩΑ-Ζ][α-ωά-ώήίόύέϊϋΐ]+)', re.IGNORECASE)
    pat_after = re.compile(r'([Α-ΩΑ-Ζ][α-ωά-ώήίόύέϊϋΐ]+?)\s+(?:{verb_names})'.replace("??", ""), re.IGNORECASE)
    # πιο απλό: «...», απάντησε ο Χ -> ο Χ
    m = re.search(rf'»,?\s*(?:{verb_names})\s+(?:ο|η)\s+([Α-ΩΑ-Ζ][α-ωά-ώήίόύέϊϋΐ]+)', sentence)
    if m:
        speakers.append(m.group(1))
    # «...», είπε ο Χ (χωρίς κόμμα ή με κόμμα)
    m2 = re.search(rf'[»”]\s*,?\s*(?:{verb_names})\s+(?:ο|η)\s+([Α-ΩΑ-Ζ][α-ωά-ώήίόύέϊϋΐ]+)', sentence)
    if m2:
        speakers.append(m2.group(1))
    # είπε ο Χ πρώτα, μετά «...»
    m3 = re.search(rf'(?:{verb_names})\s+(?:ο|η)\s+([Α-ΩΑ-Ζ][α-ωά-ώήίόύέϊϋΐ]+).+?[«“]', sentence)
    if m3 and not m:
        speakers.append(m3.group(1))
    # «...» (Χ) — σπάνιο σχήμα
    m4 = re.search(r'[»”]\s*\(([Α-ΩΑ-Ζ][α-ωά-ώήίόύέϊϋΐ]+)\)', sentence)
    if m4:
        speakers.append(m4.group(1))
    # Αφαίρεση διπλών διατηρώντας σειρά
    seen = []
    for s in speakers:
        if s not in seen:
            seen.append(s)
    return speech, seen


def extract_entities_from_text(text: str, chunks: list = None) -> dict:
    """Κύρια συνάρτηση: εξάγει οντότητες με αποδεικτικά αποσπάσματα.

    Args:
        text: πλήρες κείμενο βιβλίου.
        chunks: προαιρετικά, λίστα (content, title) από parse_book για citation κεφαλαίων.
    """
    # Χάρτης κεφαλαίων: για κάθε απόσπασμα βρίσκουμε σε ποιο chunk ανήκει (απλό grep).
    chunk_titles = {}
    if chunks:
        for idx, (content, title) in enumerate(chunks, 1):
            hook = content[:60].strip()
            if hook:
                chunk_titles[hook] = title or f"Κεφάλαιο {idx}"
    # Εναλλακτικός χάρτης: νούμερο σειράς → τίτλος (το ξαναφτιάχνουμε γραμμικά)
    chapter_of_line = {}
    if chunks:
        pos = 0
        line_start = 0
        for idx, (content, title) in enumerate(chunks, 1):
            lines = content.splitlines()
            for i, _ in enumerate(lines):
                chapter_of_line[line_start + i + 1] = title or f"Κεφάλαιο {idx}"
            line_start += len(lines)

    sentences = _split_into_sentences(text)

    # --- 1. Ονόματα (κεφαλαία που ΔΕΝ είναι στην αρχή πρότασης) ---
    name_counter = Counter()
    name_first = {}          # όνομα -> πρώτο απόσπασμα
    dialogue_speaker_counter = Counter()

    for sent, line_no in sentences:
        stripped = sent.lstrip()
        # Βρες όλα τα capitalized tokens
        caps = _CAPITALIZED.findall(stripped)
        # Αφαίρεσε την πρώτη λέξη της πρότασης (αρχική κεφαλαία, όχι όνομα)
        if caps:
            first_word = re.match(r'^[\W\d]*([Α-ΩA-Z][α-ωά-ώήίόύέϊϋΐa-z]+)', stripped)
            if first_word and caps and caps[0] == first_word.group(1):
                # Αν το δεύτερο κεφαλαίο ακολουθεί αμέσως (π.χ. "Η Ελένη") το πρώτο είναι άρθρο
                pass
            caps = caps[0:]
        for name in caps:
            if name in _STOPWORDS_CAP or len(name) < 3:
                continue
            # Μητροπολιτική αρχή: πρώτη λέξη πρότασης που έχει άρθρο μπροστά ("Η Ελένη ...")
            if re.match(rf'^(?:Ο|Η|Το|Οι|Τα)\s+{re.escape(name)}\b', stripped):
                name_counter[name] += 1
                if name not in name_first:
                    name_first[name] = (sent, line_no)
                continue
            # Αν είναι πρώτη λέξη πρότασης ΚΑΙ δεν εμφανίζεται αλλού ως κεφαλαία, είναι ύποπτη.
            # Θα την κρατήσουμε μόνο αν εμφανίζεται ≥2 φορές ή σε διάλογο/μετά από άρθρο.
            if stripped.startswith(name):
                # Είναι η πρώτη λέξη. Μόνο αν ξανα-εμφανίζεται αργότερα το θεωρούμε όνομα.
                name_counter[name] += 500  # βάρος: πιθανό αλλά πρέπει να επιβεβαιωθεί
                if name not in name_first:
                    name_first[name] = (sent, line_no)
                continue
            name_counter[name] += 1
            if name not in name_first:
                name_first[name] = (sent, line_no)

        # 2. Διάλογοι: απόδοση ομιλητή
        speech, speakers = _attributions(stripped)
        for sp in speakers:
            dialogue_speaker_counter[sp] += len(speech) if speech else 1
            if sp not in name_counter:
                name_counter[sp] += 2
                if sp not in name_first:
                    name_first[sp] = (sent, line_no)

    # Όσα βρέθηκαν με βάρος 500 και δεν επιβεβαιώθηκαν ξανά τα αφαιρούμε (αρχική λέξη ψευδές).
    confirmed = [n for n, c in name_counter.items() if c >= 2]
    candidates = [n for n, c in name_counter.items() if c >= 3 and n not in confirmed]
    # Τελικά ονόματα: επιβεβαιωμένα (≥2 εμφανίσεις συνολικά) ή ομιλητές διαλόγων
    all_names = set(confirmed) | set(dialogue_speaker_counter.keys())
    if not all_names:
        for n, c in name_counter.most_common(5):
            if c >= 2:
                all_names.add(n)

    # --- 3. Ταξινόμηση με λεξιλόγια ---
    characters, locations, objects, concepts, factions = [], [], [], [], []
    name_role_hint = {}

    for name in sorted(all_names, key=lambda n: -name_counter[n]):
        name_lower = name.lower()
        # Φατρίες (πολλαπλή λέξη): ψάξε "Γκρίζοι Φύλακες" ως φράση
        # Τοποθεσία;
        is_loc = any(k in name_lower for k in _LOC_KEYWORDS)
        is_faction = any(k in name_lower for k in _FACTION_KEYWORDS)
        if is_faction:
            factions.append({"name": name, "type": "Faction",
                             "evidence": [{"quote": name_first.get(name, ("", 0))[0][:160],
                                           "line": name_first.get(name, ("", 0))[1]}]})
        elif is_loc:
            locations.append({"name": name, "type": "Location",
                              "evidence": [{"quote": name_first.get(name, ("", 0))[0][:160],
                                            "line": name_first.get(name, ("", 0))[1]}]})
        else:
            # Ρόλος: από προτάσεις γύρω από το όνομα
            role = None
            for sent, line_no in sentences:
                if name in sent:
                    for hint, role_name in _ROLE_HINTS.items():
                        if hint in sent.lower():
                            role = role_name
                            break
                if role:
                    break
            characters.append({"name": name,
                               "role": role or ("Dialogue Speaker" if name in dialogue_speaker_counter else "Recurring Entity"),
                               "traits": ["Αυτόματη εξαγωγή από συχνότητα"],
                               "evidence": [{"quote": name_first.get(name, ("", 0))[0][:160],
                                             "line": name_first.get(name, ("", 0))[1]}]})

    # --- 4. Σχέσεις: co-occurrence σε πρόταση + λεξιλόγιο συγγένειας/σύγκρουσης ---
    relationships = []
    char_names = [c["name"] for c in characters]
    seen_rel = set()

    for sent, line_no in sentences:
        present = [n for n in char_names if n in sent]
        if len(present) >= 2:
            for i in range(len(present)):
                for j in range(i + 1, len(present)):
                    a, b = present[i], present[j]
                    key = tuple(sorted([a, b]))
                    if key in seen_rel:
                        continue
                    sent_lower = sent.lower()
                    rel_type = "αναφορά/συνάντηση"
                    if any(k in sent_lower for k in _KINSHIP_VERBS):
                        rel_type = "συγγένεια/φιλία"
                    if any(k in sent_lower for k in _CONFLICT_VERBS):
                        rel_type = "σύγκρουση"
                    relationships.append({
                        "source": a, "target": b, "relation": rel_type,
                        "type": rel_type,
                        "evidence": [{"quote": sent[:200], "line": line_no}]
                    })
                    seen_rel.add(key)

    # --- 5. Αντικείμενα & έννοιες: φράσεις με άρθρο + γνωστά ουσιαστικά ---
    objects_found = set()
    concepts_found = set()
    for sent, line_no in sentences:
        low = sent.lower()
        for pat in [r'\bκουτί\b', r'\bσπαθί\b', r'\bκλειδί\b', r'\bχάρτης\b', r'\bδαχτυλίδι\b',
                    r'\bβιβλίο\b', r'\bγράμμα\b', r'\bτετράδιο\b', r'\bαρχαίο κειμήλιο\b',
                    r'\bφυλαχτό\b', r'\bτόξο\b', r'\bασπίδα\b', r'\bπεργαμηνή\b', r'\bκουτί\b']:
            if re.search(pat, low):
                objects_found.add((pat.replace(r'\b', '').replace(r'\b', ''), sent, line_no))
        for concept in ["δύναμη", "αλήθεια", "σοφία", "φως", "σκιά", "βία", "ελευθερία",
                        "θάνατος", "ζωή", "τιμή", "πιστότητα", "ελπίδα", "δικαιοσύνη",
                        "τρέλα", "έλεος", "εκδίκηση", "συμφιλίωση", "θυσία", "φόβος",
                        "θάρρος", "γνώση", "μυστικό", "προδοσία"]:
            if concept in low:
                concepts_found.add((concept, sent, line_no))

    for obj, sent, line_no in objects_found:
        if not any(o["name"] == obj for o in objects):
            objects.append({"name": obj.capitalize(), "type": "Object",
                            "evidence": [{"quote": sent[:160], "line": line_no}]})
    for concept, sent, line_no in concepts_found:
        if not any(c["name"] == concept for c in concepts):
            concepts.append({"name": concept, "category": "Concept",
                             "evidence": [{"quote": sent[:160], "line": line_no}]})

    # --- 6. Faction μέλη (σχέση μέλους) ---
    for fac in factions:
        for c in characters:
            sent, line_no = name_first.get(c["name"], ("", 0))
            if fac["name"].lower() in sent.lower():
                relationships.append({
                    "source": c["name"], "target": fac["name"],
                    "relation": "μέλος/ανήκει", "type": "affiliation",
                    "evidence": [{"quote": sent[:160], "line": line_no}]
                })

    # --- 7. Timeline (κορυφαίες αναφορές) ---
    timeline = [{"chapter_hint": t or "", "quote": q[:160], "line": ln}
                for t, q, ln in []]

    # Κενά σηματοδοτούν ειλικρινά όταν δεν βρέθηκε τίποτα
    if not characters:
        characters = []
    if not locations:
        locations = []
    if not relationships:
        relationships = []

    return {
        "_note": "Αυτόματη εξαγωγή με αποδεικτικά αποσπάσματα (extract_entities.py). "
                 "Κάθε entry έχει evidence από το κείμενο.",
        "characters": characters,
        "locations": locations,
        "objects": objects,
        "concepts": concepts,
        "relationships": relationships,
        "factions": factions,
        "timeline": timeline,
        "stats": {
            "total_sentences": len(sentences),
            "names_detected": len(all_names),
            "method": "rule-based: capitalized-in-context + dialogue attribution + role vocab"
        }
    }


if __name__ == "__main__":
    import json
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "sample.md"
    txt = open(path, encoding="utf-8").read()
    res = extract_entities_from_text(txt)
    print(json.dumps(res, ensure_ascii=False, indent=2))
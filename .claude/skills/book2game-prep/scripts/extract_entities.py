#!/usr/bin/env python3
"""
extract_entities.py — Αυτόματη εξαγωγή χαρακτήρων, τοποθεσιών, εννοιών και αντικειμένων από το κείμενο.
Χρησιμοποιεί regex heuristics, κεφαλαία γράμματα και συχνότητα εμφάνισης.
"""

import re
import json
from collections import Counter

def extract_entities_from_text(text: str) -> dict:
    # Καθαρισμός & εντοπισμός λέξεων με κεφαλαίο γράμμα (πιθανά ονόματα/τοποθεσίες)
    # Ελληνικά & Αγγλικά proper nouns
    pattern_gr_en = r'\b([Α-ΩA-Z][α-ωa-z\u0370-\u03FF]{2,}(?:\s+[Α-ΩA-Z][α-ωa-z\u0370-\u03FF]{2,})*)\b'
    matches = re.findall(pattern_gr_en, text)

    # Φιλτράρισμα κοινών λέξεων στην αρχή προτάσεων
    stopwords = {
        "Κεφάλαιο", "Chapter", "Ενότητα", "Αλλά", "Και", "Ο", "Η", "Το", "Οι", "Τα", 
        "Ενας", "Μια", "Ένα", "The", "A", "An", "And", "But", "Or", "In", "On", "At"
    }

    filtered = [m for m in matches if m not in stopwords and len(m) > 3]
    counts = Counter(filtered)

    # Ταξινόμηση συχνοτήτων
    top_common = [item[0] for item in counts.most_common(20)]

    # --- Citation + line tracking: scan line-by-line for first occurrence ---
    lines = text.split('\n')
    heading_re = re.compile(
        r'^(?:#+\s+.*|ΚΕΦΑΛΑΙΟ.*|Κεφάλαιο.*|CHAPTER.*|Chapter.*|Ενότητα.*|\d+\.\s+[Α-ΩA-Z].*)$'
    )
    chapter_boundaries = []  # list of (line_idx, citation_label)
    for i, line in enumerate(lines):
        stripped = line.strip()
        if heading_re.match(stripped):
            num = len(chapter_boundaries) + 1
            chapter_boundaries.append((i, f"ch{num:02d}"))

    def line_to_citation(line_idx):
        """Map a line index to its chapter citation label."""
        if not chapter_boundaries:
            return "full_text"
        current = chapter_boundaries[0][1]
        for ch_line, ch_label in chapter_boundaries:
            if ch_line <= line_idx:
                current = ch_label
            else:
                break
        return current

    # Track first occurrence of each entity name across the full text
    entity_first = {}  # name -> (line_idx, citation)
    for i, line in enumerate(lines):
        for m in re.findall(pattern_gr_en, line):
            if m not in entity_first:
                entity_first[m] = (i, line_to_citation(i))

    # Heuristics διαχωρισμού
    characters = []
    locations = []
    objects = []
    concepts = []

    # Λέξεις κλειδιά για τοποθεσίες
    loc_keywords = ["πόλη", "νησί", "πύργος", "κάστρο", "όρος", "βουνό", "ποταμός", "sea", "city", "island", "castle", "mountain"]
    
    for item in top_common:
        item_lower = item.lower()
        is_loc = any(k in item_lower for k in loc_keywords)
        first_line, first_citation = entity_first.get(item, (0, "full_text"))
        if is_loc:
            locations.append({"name": item, "type": "Location", "description": "Εντοπίστηκε αυτόματα από το κείμενο", "citation": first_citation, "line": first_line})
        elif len(characters) < 5:
            characters.append({"name": item, "role": "Protagonist / Recurring Entity", "traits": ["Αυτόματη εξαγωγή"], "citation": first_citation, "line": first_line})
        else:
            concepts.append({"name": item, "category": "General Concept", "citation": first_citation, "line": first_line})

    # Αν δεν βρέθηκαν αρκετοί, βάζουμε defaults
    if not characters:
        characters.append({"name": "Πρωταγωνιστής", "role": "Main Character", "traits": ["Κεντρικός ρόλος"], "citation": "full_text", "line": 0})
    if not locations:
        locations.append({"name": "Κεντρική Τοποθεσία", "type": "Hub", "description": "Βασικός χώρος δράσης", "citation": "full_text", "line": 0})

    return {
        "_note": "Αυτόματη εξαγωγή οντοτήτων μέσω extract_entities.py",
        "characters": characters,
        "locations": locations,
        "objects": objects,
        "concepts": concepts,
        "relationships": [
            {"source": characters[0]["name"], "target": locations[0]["name"], "relation": "resides_in"}
        ],
        "factions": [],
        "timeline": []
    }

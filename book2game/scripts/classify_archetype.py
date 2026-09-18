#!/usr/bin/env python3
"""
classify_archetype.py — Ανιχνεύει αυτόματα τον τύπο του βιβλίου:
1. LINEAR_NARRATIVE: Ενιαία ιστορία, κοινός πρωταγωνιστής, χρονική εξέλιξη.
2. ANTHOLOGY_EPISODIC: Συλλογή αυτοτελών ιστοριών/διηγημάτων (διαφορετικοί χαρακτήρες ανά κεφάλαιο).
3. THEMATIC_EDUCATIONAL: Εκπαιδευτικό/θεματικό δοκίμιο, έννοιες, μελέτες (απουσία παραδοσιακών χαρακτήρων).
"""

import re
import sys
from pathlib import Path

EDUCATIONAL_KEYWORDS = [
    "εισαγωγή", "θεωρία", "ορισμός", "ανάλυση", "μεθοδολογία", "συμπέρασμα",
    "κεφάλαιο", "ενότητα", "μελέτη", "αρχή", "κανόνας", "σύστημα", "παράδειγμα",
    "επιστήμη", "ιστορία", "οικονομία", "τεχνολογία", "φιλοσοφία", "έννοια",
    "introduction", "theory", "definition", "analysis", "methodology", "conclusion",
    "chapter", "section", "study", "principle", "rule", "system", "example"
]

NARRATIVE_VERBS = [
    "είπε", "απάντησε", "ρώτησε", "κοίταξε", "έτρεξε", "περπάτησε", "σκέφτηκε", "είδε",
    "said", "replied", "asked", "looked", "walked", "thought", "saw", "felt"
]

def analyze_archetype(text: str, chapters: list = None) -> dict:
    text_lower = text.lower()
    words = text_lower.split()
    total_words = len(words) if words else 1

    # 1. Έλεγχος Educational/Thematic
    edu_hits = sum(text_lower.count(k) for k in EDUCATIONAL_KEYWORDS)
    edu_density = (edu_hits / total_words) * 1000

    # 2. Έλεγχος Narrative διαλόγων & ρημάτων
    dialogue_quotes = len(re.findall(r'[«»"""]', text))
    narrative_hits = sum(text_lower.count(v) for v in NARRATIVE_VERBS)
    narrative_density = (narrative_hits / total_words) * 1000

    # 3. Ανάλυση συνέχειας χαρακτήρων ανάμεσα σε κεφάλαια (αν υπάρχουν chapters)
    archetype = "LINEAR_NARRATIVE"
    confidence = 0.8
    reasoning = []

    if edu_density > 15.0 and narrative_density < 3.0 and dialogue_quotes < 10:
        archetype = "THEMATIC_EDUCATIONAL"
        confidence = 0.9
        reasoning.append(f"Υψηλή πυκνότητα επιστημονικών/εκπαιδευτικών όρων ({edu_density:.1f}/1k λέξεις)")
        reasoning.append("Χαμηλή παρουσία αφηγηματικών ρημάτων και απουσία διαλόγων")
    elif chapters and len(chapters) >= 2:
        # Έλεγχος αν κάθε κεφάλαιο έχει εντελώς διαφορετικές λέξεις με κεφαλαία (αυτοτελή πρόσωπα)
        proper_nouns_per_chapter = []
        for ch in chapters:
            content = ch.get("content", "")
            nouns = set(re.findall(r'\b[Α-ΩA-Z][α-ωa-z]{2,}\b', content))
            proper_nouns_per_chapter.append(nouns)
        
        # Υπολογισμός κοινών ονομάτων μεταξύ των 2 πρώτων κεφαλαίων
        if len(proper_nouns_per_chapter) >= 2:
            intersection = proper_nouns_per_chapter[0].intersection(proper_nouns_per_chapter[1])
            if len(intersection) < 2 and narrative_density >= 2.0:
                archetype = "ANTHOLOGY_EPISODIC"
                confidence = 0.85
                reasoning.append("Αυτοτελή κεφάλαια: Ελάχιστη επικάλυψη πρωταγωνιστών ανάμεσα στα κεφάλαια")
                reasoning.append("Παρουσία αφήγησης αλλά κατακερματισμένη δομή χαρακτήρων")
            else:
                archetype = "LINEAR_NARRATIVE"
                confidence = 0.88
                reasoning.append("Συνεχής αφήγηση: Επαναλαμβανόμενοι βασικοί χαρακτήρες και κοινή πλοκή")
    else:
        if narrative_density >= 3.0 or dialogue_quotes >= 10:
            archetype = "LINEAR_NARRATIVE"
            confidence = 0.85
            reasoning.append("Αφηγηματικό ύφος με διαλόγους και εξέλιξη χαρακτήρων")
        else:
            archetype = "THEMATIC_EDUCATIONAL"
            confidence = 0.75
            reasoning.append("Θεματική/δοκιμιακή παρουσίαση εννοιών")

    return {
        "archetype": archetype,
        "confidence": confidence,
        "metrics": {
            "edu_density_per_1k": round(edu_density, 2),
            "narrative_density_per_1k": round(narrative_density, 2),
            "dialogue_quotes_count": dialogue_quotes
        },
        "reasoning": reasoning,
        "recommended_studio_approach": {
            "LINEAR_NARRATIVE": "Κλασική δομή 3 πράξεων, ενιαίο hero's journey, άμεσο story loop.",
            "ANTHOLOGY_EPISODIC": "Framing Hub (Αρχείο/Βιβλιοθήκη), Modular Cases/Runs, Meta-Progression.",
            "THEMATIC_EDUCATIONAL": "Concept-to-Mechanic Matrix, Management/Simulation or Puzzle, Skill Tree."
        }[archetype]
    }

def extract_chapter_data(chunks):
    """Μετατρέπει τα chunks (content, title) σε λεξικά για ανάλυση."""
    return [{"content": c, "title": t or f"part-{i+1}"} for i, (c, t) in enumerate(chunks)]

def classify_book(text: str, chunks: list = None) -> dict:
    """Ενιαία συνάρτηση για το parse_book.py — δέχεται κείμενο + chunks."""
    chapter_data = extract_chapter_data(chunks) if chunks else None
    res = analyze_archetype(text, chapter_data)
    return res

if __name__ == "__main__":
    if len(sys.argv) > 1:
        p = Path(sys.argv[1])
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="ignore")
            res = analyze_archetype(text)
            print(f"Archetype: {res['archetype']} (Confidence: {res['confidence']})")
            for r in res['reasoning']:
                print(f" - {r}")

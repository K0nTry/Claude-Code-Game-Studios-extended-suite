#!/usr/bin/env python3
"""
generate_expansion_grammar.py — Cycle 12: Γραμματική επέκτασης με terminals από το βιβλίο.

Αντί για generic «Μυστηριώδης επιστολή στο <LOCATION>», βγάζει:
  - Terminals: πραγματικοί χαρακτήρες, τοποθεσίες, αντικείμενα, έννοιες από entities
  - Κανόνες: QUEST -> INCITING -> DISCOVERY -> COMPLICATION -> RESOLUTION
    με φράσεις που χρησιμοποιούν τα πραγματικά terminals
  - DDA: συνδεδεμένο με pacing scores (αν δοθούν)
  - Mod schema: λίστα terminals για validation
"""

import json

def _terminals_from_entities(entities: dict):
    chars = [c.get("name","") for c in entities.get("characters",[]) if c.get("name")]
    locs = [c.get("name","") for c in entities.get("locations",[]) if c.get("name")]
    objs = [c.get("name","") for c in entities.get("objects",[]) if c.get("name")]
    concepts = [c.get("name","") for c in entities.get("concepts",[]) if c.get("name")]
    factions = [c.get("name","") for c in entities.get("factions",[]) if c.get("name")]
    # fallback αν άδεια
    if not chars:
        chars = ["Πρωταγωνιστής"]
    if not locs:
        locs = ["Κεντρική Τοποθεσία"]
    return chars, locs, objs, concepts, factions

def generate_expansion_engine(book_title_or_entities=None, entities: dict = None, pacing: dict = None) -> dict:
    """
    Συμβατό API:
      generate_expansion_engine("My Book")              — παλιό
      generate_expansion_engine(entities_dict)          — νέο
      generate_expansion_engine(book_title, entities)   — μεικτό
    """
    # αποκωδικοποίηση
    title = "Book"
    ents = {}
    if isinstance(book_title_or_entities, dict):
        ents = book_title_or_entities
        if entities and isinstance(entities, dict) and "characters" in entities:
            # δεύτερο όρισμα είναι pacing
            pacing = entities
        title = ents.get("_title", "Book")
    elif isinstance(book_title_or_entities, str):
        title = book_title_or_entities
        if isinstance(entities, dict):
            ents = entities
    if entities and isinstance(entities, dict) and not ents:
        ents = entities

    chars, locs, objs, concepts, factions = _terminals_from_entities(ents)

    # helpers για δείγματα (πρώτα 2-3 terminals)
    c1, c2 = (chars[0] if chars else "Χαρακτήρας"), (chars[1] if len(chars)>1 else chars[0])
    l1, l2 = (locs[0] if locs else "Τοποθεσία"), (locs[1] if len(locs)>1 else locs[0])
    o1 = objs[0] if objs else "αντικείμενο"
    k1 = concepts[0] if concepts else "μυστικό"
    f1 = factions[0] if factions else "φατρία"

    grammar = {
        "QUEST": ["<INCITING_INCIDENT> -> <DISCOVERY_PHASE> -> <COMPLICATION> -> <RESOLUTION>"],
        "INCITING_INCIDENT": [
            f"Μήνυμα για τον {c1} ανακαλύπτεται {f'στην {l1}' if l1 else ''}".strip(),
            f"Ο/Η {c2} ζητά βοήθεια υπό την απειλή {f'των {f1}' if f1!='φατρία' else 'άγνωστης φατρίας'}",
            f"Το {o1} εξαφανίζεται από {f'την {l1}' if l1 else 'το κέντρο'}"
        ],
        "DISCOVERY_PHASE": [
            f"Αποκρυπτογράφηση ενδείξεων για {f'το {k1}' if k1!='μυστικό' else 'το μυστικό'}",
            f"Μυστική συνάντηση {f'στην {l2}' if l2 else ''}".strip(),
            f"Συνομιλία με {c1} για την αλήθεια"
        ],
        "COMPLICATION": [
            f"Προδοσία από απρόσμενο σύμμαχο του {c1}",
            f"Χρονικός περιορισμός πριν επέμβουν {f'οι {f1}' if f1!='φατρία' else 'οι αντίπαλοι'}",
            f"Ηθικό δίλημμα: θυσία {o1} για σωτηρία"
        ],
        "RESOLUTION": [
            f"Αποκάλυψη για {f'το {k1}' if k1!='μυστικό' else 'το παρελθόν'} με επίδραση στις φατρίες",
            f"Απόκτηση {o1} ως κλειδί για το επόμενο κεφάλαιο",
            f"Νέο ισοζύγιο {f'στην {l1}' if l1 else 'στην περιοχή'}"
        ]
    }

    # DDA — αν υπάρχει pacing, σύνδεσέ το
    dda = {
        "evaluation_window_seconds": 90,
        "difficulty_tuning_knobs": {
            "player_performance_high": "Αύξηση πίεσης αντιπάλων, μείωση drops",
            "player_performance_low": "Εισαγωγή πλεονεκτημάτων περιβάλλοντος, μεγαλύτερο παράθυρο αντίδρασης",
            "target_flow_equilibrium": "Διατήρηση έντασης 0.40-0.75 (βάσει pacing curve)"
        }
    }
    if pacing and isinstance(pacing, dict):
        curve = pacing.get("tension_curve") or pacing.get("tension_samples") or []
        if curve:
            avg = sum(c.get("tension_score",0.5) for c in curve)/len(curve)
            dda["source_pacing_avg"] = round(avg, 3)
            dda["source_note"] = f"μέση ένταση βιβλίου {round(avg,2)} — ρύθμισε DDA γύρω από αυτό"

    mod_schema = {
        "schema_version": "2.0",
        "terminals": {
            "CHARACTER": chars[:8],
            "LOCATION": locs[:8],
            "OBJECT": objs[:8],
            "CONCEPT": concepts[:8],
            "FACTION": factions[:5] if factions else []
        },
        "validation_hook": "scripts/audit_lore_drift.py --mod-mode",
        "_note": "terminals = πραγματικά ονόματα από το βιβλίο — όχι placeholders <CHARACTER>"
    }

    return {
        "book_title": title,
        "story_grammar": grammar,
        "terminals_source": "entities.json (πραγματικά ονόματα από το κείμενο)",
        "dynamic_difficulty_adjustment": dda,
        "modding_extensibility_manifest": mod_schema,
        "_method": "terminals από entities + φράσεις με πραγματικά ονόματα",
        "_caveat": "Για procedural quests χρειάζεται LLM expansion πάνω στη γραμματική"
    }

if __name__ == "__main__":
    ents = {"characters":[{"name":"Αλέξανδρος"},{"name":"Ελένη"}], "locations":[{"name":"Ακρόπολη"}], "objects":[{"name":"Κουτί"}], "concepts":[{"name":"δύναμη"}], "factions":[{"name":"Γκρίζοι Φύλακες"}]}
    print(json.dumps(generate_expansion_engine(ents), ensure_ascii=False, indent=2))

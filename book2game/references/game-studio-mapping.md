# Game Studio Mapping — βιβλίο → Studio templates

## Τι περιμένει το Studio (7 φάσεις)

Το skill καλύπτει τη **Φάση 1: Concept**. Τα gates είναι:

- `design/gdd/game-concept.md` — 9 ενότητες (Elevator Pitch, MDA, SDT, Core Loop, Pillars, MVP)
- `design/gdd/systems-index.md` — πίνακας συστημάτων + dependencies
- `design/gdd/game-pillars.md`
- `design/art/art-bible.md`
- `production/stage.txt` = `concept`

Χωρίς αυτά, το `/gate-check concept` κάνει FAIL.

## Αντιστοίχιση

| Στοιχείο βιβλίου | Πού πάει στο Studio |
|---|---|
| Τίτλος + υπόθεση | game-concept.md: Elevator Pitch |
| Κεντρική σύγκρουση/θέμα | game-concept.md: Core Fantasy + Pillars |
| Ύφος/τόνος | art-bible.md (palette, rendering) + MDA ranking |
| Χαρακτήρες | entities.json → world-builder, writer |
| Τοποθεσίες | entities.json → world-builder, level-designer |
| Αντικείμενα/έννοιες | entities.json → economy-designer, systems-designer |
| Σχέσεις | entities.json → narrative-director |
| Κεφάλαια/σκηνές | systems-index.md (κάθε κεφάλαιο → πιθανό system/level) |
| Κανόνες κόσμου | lore/bible.md + cross-system dependencies |
| Πλοκή/χρονολόγιο | lore/bible.md + systems-index timeline |

## Agents που διαβάζουν τι

- `narrative-director + world-builder + writer` → `entities.json`, `lore/bible.md`, `chapters/`
- `systems-designer + economy-designer` → `systems-index.md`, `entities.json`
- `art-director + ux-designer` → `art-bible.md`, `game-concept.md` (MDA, pillars)
- `creative-director` → `game-concept.md` (vision guard)

## Κανόνες

- Μην ονομάσεις `game_blueprint.md` — αγνοείται από gates. Το canonical είναι `game-concept.md`.
- Κάθε system στο `systems-index.md` πρέπει να έχει `Status` και `Priority`.
- Το `full_text.md` μένει ως RAG source — οι agents δεν το διαβάζουν ολόκληρο, κάνουν grep.

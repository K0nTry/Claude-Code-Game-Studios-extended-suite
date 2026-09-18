# Game Project — minimal

> Αυτόματα δημιουργημένος φάκελος από το book2game. Έτοιμος για ανάπτυξη μέσα στο Claude Code Game Studio.

## Πώς να τον συνδέσεις με το Game Studio

1. **Προϋπόθεση:** Έχεις κλωνοποιήσει το template του Game Studio (Donchitos/Claude-Code-Game-Studios) και έχει ρυθμιστεί το `.claude/` (agents, skills, hooks).
2. **Τοποθέτηση:** Αντικατέστησε/συγχώνευσε αυτόν τον φάκελο στη ρίζα του Game Studio project. Κράτησε το `.claude/` του Studio ανέπαφο.
3. **Πρώτο gate:** Τρέξε `/gate-check concept`. Το output είναι ήδη δομημένο ώστε να περνάει (game-concept, systems-index, pillars, art-bible, stage.txt=concept).
4. **Συνέχεια:** Ο επόμενος agent ξεκινά από `roadmap.md` + `docs/studio-workflow.md`. Εκεί είναι ο νόμος του Studio.
5. **Resume after break:** Διάβασε `active.md` → συνέχισε την τρέχουσα φάση → τρέξε το gate της → ενημέρωσε `active.md`.

## Τι περιέχει

- `full_text.md` + `chapters/` + `index.json`: Πλήρες κείμενο βιβλίου, RAG-ready
- `entities.json` + `lore/bible.md`: Χαρακτήρες, κόσμος, κανόνες
- `game_blueprint.md`: Κεντρική εισαγωγή + Studio Execution Model
- `technical/engine.md`: Επιλεγμένη μηχανή + MCP servers
- `design/gdd/`: Concept, Systems, Pillars — ακριβώς τα templates του Studio
- `docs/studio-workflow.md`: Ο νόμος λειτουργίας μέσα στο Studio

## Σημείωση

Αυτός ο φάκελος ΔΕΝ αντικαθιστά το Game Studio. Είναι το **υλικό (bible, full text, analysis)** που τροφοδοτεί το Studio. Το workflow (φάσεις, gates, agents) ανήκει στο Studio.

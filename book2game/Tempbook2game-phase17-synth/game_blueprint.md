# Game Blueprint — synthetic_test_book

> Πηγή: synthetic_test_book.txt | Αρχείο: game_blueprint.md | Ημερομηνία: 2026-09-14

## Elevator Pitch

_Συμπληρώνεται από Claude ανάλυση. Ένα δυνατό pitch που συνδέει το βιβλίο με το gameplay._

## Σύνοψη

_Αυτό το αρχείο είναι η κεντρική εισαγωγή για κάθε agent του Game Studio που μπαίνει στο project._

## Studio Execution Model

> Όταν αυτός ο φάκελος ανοίγει μέσα στο Claude Code Game Studio, η ανάπτυξη ακολουθεί τον νόμο του Studio:
> 7 φάσεις με gates (`/gate-check <phase>`), agents με tiers (Directors → Leads → Specialists), templates από το `.claude/docs/templates/`.

### Πώς συνεχίζει ο επόμενος agent
1. Διάβασε **`roadmap.md`** — αυτό είναι το μόνο έγκυρο χρονοδιάγραμμα. Κάθε φάση έχει σημειωμένο το gate της.
2. Διάβασε **`docs/studio-workflow.md`** — ο νόμος λειτουργίας μέσα στο Studio (φάσεις, gates, ρόλοι, απαγορεύσεις).
3. Διάβασε **`active.md`** — τι πέρασε το τελευταίο session, τι εκκρεμεί.
4. Εκτέλεσε την τρέχουσα φάση ΜΟΝΟ μέσω των templates και gates του Studio.
5. Ποτέ μην εφεύρεις νέα δομή. Ό,τι δεν ορίζει το Studio, δεν υπάρχει.

## Δομή Φακέλου

- `full_text.md` + `chapters/` + `index.json`: Πλήρες κείμενο & RAG index
- `entities.json` + `lore/bible.md`: Χαρακτήρες & Κόσμος
- `design/gdd/`: Game Concept, Systems Index, Game Pillars
- `technical/engine.md`: Επιλογή μηχανής & MCP servers
- `docs/studio-workflow.md`: Νόμος λειτουργίας μέσα στο Game Studio
- `active.md` + `roadmap.md`: Multi-session track

## Genre Ranking & Engine Selection

- **Προτεινόμενο Genre:** _Adventure_ (βλ. `design/gdd/game-concept.md` — οριστικοποιείται από Claude)
- **Επιλεγμένο Engine:** _Godot 4.x_ (βλ. `technical/engine.md` — αιτιολόγηση βάσει είδους, ύφους, πλατφόρμας)

## Εκτέλεση

1. Άνοιγμα φακέλου στο Claude Code Game Studio
2. Τρέξιμο `/gate-check concept`
3. Συνέχιση από `roadmap.md`

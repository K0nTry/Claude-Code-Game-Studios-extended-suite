> **STATUS: IMPLEMENTED (2026-09-15), pending final real-book verification.** SKILL.md Βήμα 1.5 added, safety cap added (single point, covers a third O(N²) site found via twin-check: `mcts_balance_solver.py`), and `parse_book.py` got two new flags (`--stop-after-entities` / `--resume-entities`) so the agent has an actual pause/resume point to inject the refined `entities.json` between Βήμα 1 and Βήμα 2 — previously the script ran both in one unbroken call with no injection point, which would have made Βήμα 1.5 a no-op in practice. Verified end-to-end (stop → simulated agent edit → resume) on `tests/fixtures/minimal.pdf`: the agent-written `entities.json` survives untouched into `canon/entities.json`, GATE PASS, full unittest suite 9/9. Real Neuromancer re-run not yet done. Σχέδιο για να διορθωθεί το πρόβλημα ποιότητας entity extraction (1578 ψεύτικοι χαρακτήρες) και το επακόλουθό του (421MB projection blowup) που βρέθηκαν στο πραγματικό τρέξιμο Neuromancer στις 2026-09-15. Θα υλοποιηθεί πριν ξαναγίνει το comparative audit (βλ. `roadmap.md` → "TOMORROW", status BLOCKED). Δείτε επίσης το ξεχωριστό, άσχετο `2026-09-15-ccgs-handoff-plan.md`.

# Fix entity extraction: regex → agent-driven, + safety cap για το 421MB bug

## Context (γιατί το κάνουμε)

Στο τρέξιμο πάνω στο πραγματικό Neuromancer βρήκαμε δύο προβλήματα που, μετά από έρευνα, αποδείχτηκαν **ένα και το αυτό**:

1. `scripts/extract_entities.py` είναι καθαρό regex ("κάθε λέξη με κεφαλαίο μετά από άρθρο μετράει ως πιθανός χαρακτήρας") — παρήγαγε **1578 ψεύτικους "χαρακτήρες"** αντί για τους ~20-30 πραγματικούς, χωρίς κανένα όριο πλήθους και χωρίς fuzzy matching (γι' αυτό "Neuromancer" και "Neuro" έμειναν δύο ξεχωριστές οντότητες αντί να ενωθούν).
2. Το 421MB `views/projections/world-builder/derived.projection.json` **δεν είναι ξεχωριστό bug** — είναι επακόλουθο του #1: το `character_psychology.py` και το `simulate_knowledge_graph.py` κάνουν βρόχο "κάθε χαρακτήρας με κάθε άλλο χαρακτήρα" (O(N²)) σαρώνοντας ολόκληρο το κείμενο ανά ζευγάρι — με 1578 ψεύτικους χαρακτήρες αυτό εκρήγνυται σε ~1.2 εκατομμύρια ζευγάρια.

Άρα διορθώνοντας τη ρίζα (#1) διορθώνεται αυτόματα και το #2. Προσθέτουμε επιπλέον ένα μικρό "όριο ασφαλείας" ώστε το #2 να μην μπορεί να ξαναγίνει ποτέ, ό,τι κι αν παράγει το extraction στο μέλλον.

**Απόφαση που πήραμε:** το extraction θα γίνεται από **agent, όχι από πληρωμένο LLM API call** — επιβεβαιώθηκε ότι το `SKILL.md` του book2game *ήδη* προϋποθέτει agent να το τρέχει ("Ροή Εκτέλεσης — ο agent την εκτελεί, όχι ο χρήστης"), και στο τελικό, shipped στάδιο (μετά το CCGS merge) θα το τρέχει ούτως ή άλλως ο agent που χειρίζεται το CCGS. Άρα καμία αλλαγή αρχιτεκτονικής — απλά προσθήκη ενός βήματος στη ροή που ήδη υπάρχει, χωρίς API key, χωρίς κόστος ανά βιβλίο.

## Τι πρέπει να γίνει (implementation steps)

### 1. Νέο βήμα στο SKILL.md: "Βήμα 1.5 — Agent Entity Refinement"

Ανάμεσα στο σημερινό Βήμα 1 (`parse_book.py`, γράφει το πρόχειρο `entities.json` μέσω regex) και το Βήμα 2 (12-Cycle engine), προσθήκη βήματος όπου ο agent:

- Διαβάζει τα `chapters/*.md` σε παρτίδες (batches), με παράλληλα subagents (ίδιο pattern που χρησιμοποιήθηκε στην έρευνα αυτής της συζήτησης) ώστε να μη χρειάζεται να διαβάσει όλο το βιβλίο σε ένα κομμάτι.
- Για κάθε παρτίδα, εντοπίζει πραγματικούς χαρακτήρες/τοποθεσίες/αντικείμενα/έννοιες/σχέσεις/φατρίες, με πραγματικό νόημα — ενώνει μόνος του "Neuromancer" με "Neuro", αγνοεί τυχαίες κεφαλαιοποιημένες λέξεις που δεν είναι πρόσωπα.
- Χρησιμοποιεί το πρόχειρο regex `entities.json` **μόνο σαν λίστα υποψηφίων-υπενθύμιση** (να μην ξεχάσει κανέναν πραγματικό χαρακτήρα), όχι σαν αλήθεια.
- Γράφει έξοδο **στο ίδιο ακριβώς σχήμα** που ήδη περιμένει ο υπόλοιπος κώδικας (επιβεβαιωμένο μέσω exploration του `scripts/extract_entities.py`): dict με keys `characters, locations, objects, concepts, relationships, factions, timeline, stats`· κάθε character έχει `name/role/traits/evidence:[{quote,line}]`· κάθε relationship έχει `source/target/relation/type/evidence`. Έτσι δεν αλλάζει τίποτα σε `scripts/canon_helpers.py` ή `scripts/assemble_projection.py` — είναι σαν να ξαναγράφτηκε καλύτερα το ίδιο αρχείο.
- Προσθέτει επιπλέον `confidence` (0-1) και `method: "agent-semantic-extraction"` ανά entity — κλείνει ένα ξεχωριστό, προϋπάρχον κενό: το epistemic model του project (`standards/epistemic-model.md`, `standards/immutable-kernel-spec.md`) απαιτεί αυτά τα πεδία + `source_offsets`, αλλά σήμερα κανείς δεν τα γράφει (επιβεβαιωμένο — το `canon_helpers.py::assign_canonical_uuids` προσθέτει μόνο `_uuid`, `_epistemic`, `_category`).
- Αντικαθιστά το `entities.json` με το βελτιωμένο πριν ξεκινήσει το Βήμα 2.
- **Update:** αυτό απαίτησε δύο νέα flags στο `parse_book.py` (`--stop-after-entities`, `--resume-entities`) — χωρίς αυτά, το script έτρεχε Βήμα 1+2 σε μία αδιάσπαστη κλήση χωρίς σημείο παρέμβασης για τον agent. Βλ. `SKILL.md` → Βήμα 1 / Βήμα 1.5 για τις ακριβείς εντολές.

### 2. Όριο ασφαλείας (defensive cap) στο `scripts/parse_book.py`

Πριν τις δύο κλήσεις που τροφοδοτούν τους O(N²) βρόχους:
- γραμμή ~115: `character_psychology.generate_character_psychology(_real_chars, ...)`
- γραμμή ~182: `simulate_knowledge_graph.simulate_knowledge_graph(_real_chars, ...)`

Προσθήκη φίλτρου "κράτα μόνο τους top-N χαρακτήρες" (π.χ. top 40, με βάση πόσο evidence έχουν) πριν περάσουν στις δύο συναρτήσεις. Δύο σημεία, ίδιο μονόγραμμο fix (twin fix — το ίδιο πρόβλημα υπάρχει και στα δύο αρχεία, `scripts/character_psychology.py` και `scripts/simulate_knowledge_graph.py`). Έτσι, ακόμα κι αν κάποτε το extraction ξαναβγάλει πολλούς χαρακτήρες, δεν μπορεί ποτέ ξανά να δημιουργηθεί αρχείο εκατοντάδων MB.

### 3. Γρήγορο ξανα-δοκιμαστικό (να μην περιμένουμε ξανά μια ώρα)

Πρώτα δοκιμή του νέου Βήματος 1.5 σε μικρό, υπάρχον δοκιμαστικό αρχείο (`tests/fixtures/minimal.pdf` ή `minimal.epub`, δευτερόλεπτα να τρέξει), όχι σε ολόκληρο το Neuromancer. Μόνο αφού επιβεβαιωθεί ότι δουλεύει σωστά εκεί (λογικός αριθμός χαρακτήρων, σωστό merge ψευδωνύμων, κανένα τεράστιο αρχείο), μία **τελική** πλήρης δοκιμή στο πραγματικό βιβλίο.

## Αρχεία που θα αλλάξουν

- `SKILL.md` — νέα ενότητα "Βήμα 1.5" (οδηγίες προς τον agent, όχι κώδικας)
- `scripts/parse_book.py` — 2 μικρές προσθήκες (cap πριν τις γραμμές ~115 και ~182)
- `roadmap.md` — ενημέρωση του "TOMORROW" block όταν ολοκληρωθεί, ώστε να ξαναδοκιμαστεί το comparative audit

**Δεν αλλάζει:** `scripts/extract_entities.py` (μένει ως γρήγορο, δωρεάν πρώτο πέρασμα/λίστα υποψηφίων)· `scripts/canon_helpers.py` (το σχήμα εξόδου μένει συμβατό, δεν χρειάζεται fuzzy-matching κώδικας αφού το κάνει ήδη ο agent).

## Πώς θα το επαληθεύσουμε (όταν υλοποιηθεί)

1. Τρέξιμο σε `tests/fixtures/minimal.pdf` — έλεγχος ότι ο αριθμός χαρακτήρων είναι λογικός (όχι εκατοντάδες) και ότι το `entities.json` έχει το ίδιο σχήμα με πριν.
2. `python -m unittest discover tests` — να παραμείνουν 9/9 PASS (καμία παλινδρόμηση).
3. Μία τελική πλήρης δοκιμή στο Neuromancer PDF — έλεγχος ότι: (α) οι χαρακτήρες είναι ρεαλιστικός αριθμός, (β) "Neuromancer"/"Neuro" ενώθηκαν σε έναν, (γ) κανένα `derived.projection.json` δεν ξεπερνά μερικά MB, (δ) `validate_output.py` → GATE PASS.
4. Μετά, προχωράμε στο comparative audit (παλιό vs νέο) που είχε μπλοκαριστεί στο `roadmap.md`.

## Evidence (από exploration στις 2026-09-15)

- `extract_entities.py:126` `extract_entities_from_text()` — μόνο `re`/`Counter`, καμία ML/LLM βιβλιοθήκη (docstring: "Δεν χρησιμοποιεί LLM").
- `extract_entities.py:169-188` — η λογική μέτρησης: λέξη μετά από άρθρο (Ο/Η/Το/Οι/Τα) μετράει πάντα, πρώτη λέξη πρότασης παίρνει βάρος +500 (ξεπερνάει εύκολα το όριο confirm=2) — γι' αυτό υπερ-ταιριάζει.
- `canon_helpers.py:130-132` — το alias-map είναι exact-string (`name.lower().strip()`), καμία fuzzy/edit-distance λογική.
- `assemble_projection.py:393-461` — αντιγράφει verbatim ό,τι του δώσουν τα derived-layer αρχεία, καμία δική του ευθύνη για το μέγεθος.
- `parse_book.py:115` και `:182` — περνάνε `_real_chars` (unsliced, χωρίς όριο) στο `character_psychology.py` και `simulate_knowledge_graph.py`.
- `character_psychology.py:202-221`, `simulate_knowledge_graph.py:65-85` — και τα δύο κάνουν nested `for i / for j in range(i+1,len)` πάνω στους χαρακτήρες, σαρώνοντας το κείμενο ανά ζευγάρι (O(N²×L)).
- `SKILL.md:43` — "## Ροή Εκτέλεσης (ο agent την εκτελεί, όχι ο χρήστης)" — επιβεβαιώνει ότι η αρχιτεκτονική ήδη προϋποθέτει agent, όχι bare script.

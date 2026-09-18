> **STATUS: FIXED in source (2026-09-15), verified against already-extracted Neuromancer text —
> real Neuromancer_game_baseline / _v2 output directories NOT regenerated (out of scope, see below).**
> `/fable-judge` audit comparing `Neuromancer_game_baseline` vs `Neuromancer_game_v2`
> (`C:\Users\Kon_Try\Desktop\book_test_outputs`) found 4 open items. All 4 are now closed. See
> also `docs/plans/2026-09-15-entity-extraction-agent-fix-plan.md` (separate, earlier bug batch)
> and `roadmap.md` → "TOMORROW — FINAL VERIFICATION & COMPARATIVE AUDIT".

# fable-judge audit of book2game baseline vs v2 — findings & fixes

## Context (γιατί το κάνουμε)

Ζητήθηκε σύγκριση δύο runs του book2game skill πάνω στο ίδιο βιβλίο (Neuromancer),
χωρίς να διαβαστεί το πρωτότυπο PDF — μόνο τα ίδια τα outputs του skill. Η μεθοδολογία
fable-judge (claims vs evidence, όχι αφήγημα) βγήκε με verdict **"verified with caveats"**:
πραγματική βελτίωση στο canon/entity extraction (89,7% λιγότερος θόρυβος), αλλά 4 ανοιχτά σημεία.
Ο χρήστης ζήτησε να λυθούν όλα, χωρίς να σπάσει τίποτα. Αυτό το doc είναι το state sink —
τι βρέθηκε, τι αποδείχτηκε αληθινό/ψευδές, τι διορθώθηκε, πώς επαληθεύτηκε.

## 1. Chapter-title bug — ΔΙΟΡΘΩΘΗΚΕ

**Εύρημα:** 143/218 (65,6%) κεφαλαίων είχαν πανομοιότυπο τίτλο `"Πρόλογος / Εισαγωγή"`, ενώ
περιείχαν διαφορετικές, πραγματικές σκηνές του μυθιστορήματος.

**Ρίζα (επιβεβαιωμένη πάνω στο ίδιο το εξαγμένο `source/full_text.md`, όχι το PDF):** οι
πραγματικοί δείκτες κεφαλαίων του Neuromancer είναι μεμονωμένοι αριθμοί σε δική τους γραμμή
("1", "2", ... "24") — το heading regex στο `scripts/parse_book.py::chunk_text()` (γραμμή 649)
δεν είχε καμία εναλλακτική που να ταιριάζει bare αριθμό, άρα ΚΑΝΕΝΑ πραγματικό κεφάλαιο δεν
εντοπιζόταν ποτέ. Αντ' αυτού, μια πρόταση πεζογραφίας στο backmatter essay ("1948. But a lot
of the mainstream...") ταίριαζε ψευδώς με το υπάρχον `\d+\.\s+[Α-ΩA-Z].*` pattern και γινόταν
το πρώτο "heading" — άρα ολόκληρο το μυθιστόρημα (το κείμενο πριν από αυτό) έπεφτε στο
"prologue" branch (γραμμές 703-722), το οποίο hardcoded τον ίδιο τίτλο σε κάθε κομμάτι αντί
να αριθμεί (σε αντίθεση με το ήδη-δουλεμένο sibling branch 4 γραμμές πιο πάνω).

**Fix (`scripts/parse_book.py`):**
- Προστέθηκε bare-number heading alternative στο regex.
- Το prologue branch τώρα αριθμεί τα κομμάτια (`— μέρος N`, mirroring το sibling pattern) και
  μπαίνει στη σωστή σειρά (`chunks[0:0] = ...` αντί για append στο τέλος).
- Bonus defensive fix: `try_pandoc()` πήρε `encoding="utf-8"` στο `subprocess.run` (dormant
  cp1252-mojibake risk αν εγκατασταθεί ποτέ pandoc — σήμερα ανενεργό, pandoc δεν είναι
  εγκατεστημένο).
- Νέο regression guard: `scripts/validate_output.py` τώρα ελέγχει `index.json` για
  duplicate τίτλους κεφαλαίων.
- Νέο test: `tests/test_chunk_text.py` (4 tests).

**Verification:** `chunk_text()` πάνω στο πραγματικό `source/full_text.md` (baseline + v2) →
μηδέν duplicate τίτλοι, και τα 24 πραγματικά κεφάλαια σωστά εντοπισμένα ("1".."24"). Ο νέος
validator έλεγχος επιβεβαιωμένα πιάνει το ΠΑΛΙΟ (μη ξαναγεννημένο) output ως broken. Πλήρης
test suite: 17/17 PASS.

## 2. Mojibake στα ελληνικά πεδία — ΨΕΥΔΈΣ ΣΥΝΑΓΕΡΜΌ (verified, όχι πραγματικό bug)

Byte-level έλεγχος και στα 779 αρχεία (baseline + v2): μηδέν corrupted bytes, μηδέν replacement
characters. Το "mojibake" ήταν artifact εμφάνισης (τερματικό/font χωρίς σωστό Greek rendering),
όχι πρόβλημα εγγραφής. Δεν άγγιξα κανένα υπάρχον output αρχείο — δεν υπήρχε τι να διορθωθεί εκεί.
Το μόνο πραγματικό (αλλά αδρανές) εύρημα ήταν το `try_pandoc()` encoding gap, diορθωμένο μαζί
με #1 παραπάνω.

## 3. Benchmark reports "σαν stub" (nash-equilibrium-report, player-personas-simulation) — ΔΙΟΡΘΩΘΗΚΕ

**Εύρημα:** `total_conflicts_found: 0` και σε 41 χαρακτήρες `conflict_count: 0` παντού
(`nash-equilibrium-report.json`)· και τα 4 player-personas με **ακριβώς** το ίδιο
`compatibility_score: 0.15`, με άδεια `evidence`/`top_signals` (`player-personas-simulation.json`).

**Ρίζα (επιβεβαιωμένη διαβάζοντας τον πηγαίο κώδικα):** `scripts/mcts_balance_solver.py` και
`scripts/simulate_player_personas.py` έχουν λεξιλόγια (conflict/resource/persona words)
**αποκλειστικά στα ελληνικά**. Το Neuromancer είναι αγγλικό κείμενο → καμία λέξη δεν ταιριάζει
ποτέ → `_score()` πέφτει πάντα στο floor `0.15` (ακριβώς η τιμή που παρατηρήθηκε), και ο
conflict-detector δεν βρίσκει ποτέ ζεύγος χαρακτήρων σε γραμμή με λέξη σύγκρουσης. Δεν ήταν
fake/hardcoded data — ήταν πραγματική, λειτουργική μέθοδος χωρίς αγγλικό λεξιλόγιο.

**Fix:** τα lexicon sets έγιναν **αγγλικά-μόνο** (conflict/resource words στο
`mcts_balance_solver.py`· explorer/achiever/social/killer words στο `simulate_player_personas.py`).
Πρώτη προσέγγιση ήταν προσθετική (αγγλικά + ελληνικά μαζί), αλλά ο χρήστης αποφάσισε να αφαιρεθούν
τα ελληνικά — το πραγματικό context που περνάει από αυτά τα scripts είναι σχεδόν πάντα αγγλικό
κείμενο βιβλίων, οπότε δεν αξίζει να διατηρείται δίγλωσσο λεξιλόγιο εδώ. Το dialog-density metric
πλέον μετράει μόνο αγγλικά quote marks (`"` `"` `"`), όχι πια το ελληνικό `«»`. Τα `__main__`
self-test blocks και στα δύο scripts ενημερώθηκαν σε αγγλικό δείγμα κειμένου (πριν ήταν ελληνικό,
θα έδειχνε πλέον μηδενικό σήμα με το νέο, αγγλικό-μόνο λεξιλόγιο).

**Verification (πάνω στο πραγματικό εξαγμένο κείμενο v2, με entities.json):**
- Personas: σκορ πλέον διαφοροποιημένα με πραγματικό evidence — Socializer 0.35
  (`brother, love, partner, team, father`), Explorer 0.25, Achiever 0.25, Killer 0.24.
- Nash: **19 πραγματικές συγκρούσεις** εντοπίστηκαν με αποσπάσματα/κεφάλαιο (π.χ. Case vs
  Armitage, Case vs the Finn), 15/60 χαρακτήρες με καταγεγραμμένη σύγκρουση.
- Νέο test: `tests/test_english_lexicons.py` (2 tests) — αποτρέπει να ξαναπέσει το lexicon σε
  Greek-only χωρίς να το προσέξουμε.
- Πλήρης test suite μετά: **17/17 PASS**.

## Τι ΔΕΝ έγινε (σκόπιμα, out of scope)

- Δεν ξανατρέξαμε το πλήρες, ακριβό multi-stage pipeline πάνω στο πραγματικό βιβλίο — η
  επαλήθευση έγινε καλώντας τις διορθωμένες συναρτήσεις απευθείας πάνω στο ήδη-εξαγμένο κείμενο
  (`source/full_text.md`), όχι μέσω πλήρους re-run. Ένα τελικό πλήρες re-run (βλ.
  `roadmap.md` → "TOMORROW") θα επιβεβαιώσει end-to-end, αλλά δεν είναι μπλοκαρισμένο από
  τίποτα από τα παραπάνω πια.
- Δεν αγγίξαμε το προϋπάρχον, μικρότερης σοβαρότητας false-positive όπου το backmatter/afterword
  essay παίρνει μερικά λάθος-labeled (αλλά πλέον unique-titled) "Chapter 23 — μέρος N" κεφάλαια —
  ο χρήστης ρητά αποφάσισε να μην το κυνηγήσουμε.
- Δεν πειράξαμε τα ήδη υπάρχοντα αρχεία `book_test_outputs\Neuromancer_game_baseline` /
  `_v2` — παραμένουν όπως ήταν, μόνο ο πηγαίος κώδικας άλλαξε.

## Αρχεία που άλλαξαν

- `scripts/parse_book.py` — heading regex + prologue branch + pandoc encoding
- `scripts/validate_output.py` — duplicate chapter-title guard
- `scripts/mcts_balance_solver.py` — αγγλικό conflict/resource lexicon
- `scripts/simulate_player_personas.py` — αγγλικό persona lexicon + αγγλικά quote marks
- `tests/test_chunk_text.py` (νέο, 4 tests)
- `tests/test_english_lexicons.py` (νέο, 2 tests)

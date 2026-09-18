# Software Factory Handoff — book2game Integration Plan

## GOAL LOCK
Θέλεις book2game pipeline μπροστά από το Concept stage του CCGS workflow, με επιλογή στο /start και verification πριν προχωρήσει το project.

## ΑΠΟΦΑΣΗ
book2game πριν το Concept + επιλογή στο /start. Integration point κλειδώθηκε.

## BACKUP + ROLLBACK
**Outcome**: Ασφαλής αλλαγή 5+ αρχείων χωρίς κίνδυνο απώλειας.

- Backup πριν:
  - Path: `.claude/_backup_book2game_merge/`
  - Αρχεία: `.claude/skills/start/SKILL.md`, `README.md`, `CLAUDE.md`, `docs/WORKFLOW-GUIDE.md`, `.claude/docs/workflow-catalog.yaml`, `.claude/docs/agent-roster.md`
  - Commands:
    - `New-Item -ItemType Directory -Force -Path .claude\_backup_book2game_merge`
    - `Copy-Item -LiteralPath .\.claude\skills\start\SKILL.md -Destination .claude\_backup_book2game_merge\`
    - `Copy-Item -LiteralPath .\README.md -Destination .claude\_backup_book2game_merge\`
    - `Copy-Item -LiteralPath .\CLAUDE.md -Destination .claude\_backup_book2game_merge\`
    - `Copy-Item -LiteralPath .\docs\WORKFLOW-GUIDE.md -Destination .claude\_backup_book2game_merge\`
    - `Copy-Item -LiteralPath .\.claude\docs\workflow-catalog.yaml -Destination .claude\_backup_book2game_merge\`
    - `Copy-Item -LiteralPath .\.claude\docs\agent-roster.md -Destination .claude\_backup_book2game_merge\`
- Rollback plan:
  - Επαναφορά: `Copy-Item -Recurse -LiteralPath .claude\_backup_book2game_merge\*. .`
  - Trigger: αν σπάσει /start, αν αποτύχουν existing tests, αν fail gate-check
  - Success criterion: τα υπάρχοντα tests του repo περνούν μετά από merge
- VERIFICATION: backup folder exists, files count επαληθεύεται πριν τροποποίηση.

## ANTI-BLOCK CHECK
**Outcome**: Το υπάρχον workflow παραμένει λειτουργικό.

1. /start λειτουργεί και χωρίς book:
   - Επιλογή "I have a book" είναι optional
   - Αν δεν επιλεγεί → παραλείπεται book2game, συνεχίζει brainstorm
   - VERIFICATION: Εκτέλεση /start χωρίς book, φτάνει σε Concept gate
2. Τα 49 agents φορτώνουν κανονικά:
   - VERIFICATION: `dir /b .claude\agents\*.md | find /c /v ""`
   - Pass: επιστρέφει 49
3. Existing hooks δεν σπάνε:
   - Hooks: validate-commit, etc.
   - VERIFICATION: Εκτέλεση `bash .claude/hooks/validate-commit.sh` περνάει

## ΦΑΣΗ 1: skill user-invocable στο repo
**Outcome**: Το skill book2game-prep είναι διαθέσιμο μέσα στο CCGS repo για χρήση από χρήστη.
- Αντιγραφή του skill από `C:\Users\Kon_Try\.claude\skills\book2game-prep\SKILL.md` σε `.claude/skills/book2game-prep/SKILL.md` με repo-relative paths.
- Ενημέρωση `allowed-tools` ώστε να δείχνει σε repo paths.
- Ενημέρωση `argument-hint` σε `--out ./` relative.
- VERIFICATION: `read .claude/skills/book2game-prep/SKILL.md` υπάρχει και user-invocable: true.

## ΦΑΣΗ 2: scripts
**Outcome**: Handoff και validation scripts έτοιμα.

1. `scripts/handoff_to_ccgs.py`
   - Input: book2game output folder
   - Output: CCGS artifacts
   - Map:
     - `full_text.md` → `design/lore/source_text.md`
     - `chapters/` → `design/lore/chapters/`
     - `index.json` → `design/rag/index.json`
     - `entities.json` → `design/entities/entity-registry.md`
     - `design.md` → `design/gdd/game-concept.md`
   - VERIFICATION: script runs χωρίς error, παράγει non-empty game-concept.md.

2. `scripts/validate_book2game.py`
   - Checks: `full_text.md` exists & >0, `index.json` exists & valid JSON, `chapters/` έχει τουλάχιστον 1 file, entities έχουν citations.
   - VERIFICATION: exit code 0 όταν όλα OK, non-zero + message όταν λείπει κάτι.

## ΦΑΣΗ 3: hook book2game-gate.sh
**Outcome**: Post-run verification hook για book2game.

- Path: `.claude/hooks/book2game-gate.sh`
- Trigger: post-run, μετά από `/book2game-prep` invocation.
- Checks:
  1. Υπάρχει `full_text.md` και μέγεθος >0
  2. Υπάρχει `index.json` και είναι valid JSON
  3. Έχουν δημιουργηθεί κεφάλαια
  4. Υπάρχει `design/gdd/game-concept.md` μετά από handoff
- Behavior:
  - Αν όλα OK → pass silently
  - Αν λείπουν αρχεία → warn με μήνυμα, block Concept Gate, ΟΧΙ commit block
- VERIFICATION: hook τρέχει με dummy folder, επιστρέφει warning όταν λείπει αρχείο.

## ΦΑΣΗ 4: /start update
**Outcome**: Ο χρήστης μπορεί να επιλέξει "I have a book" στην αρχή.

- Τροποποίηση `.claude/skills/start/SKILL.md` Phase 2 Ask Where the User Is
- Προσθήκη επιλογής: "I have a book to adapt"
- Αν επιλεγεί → τρέξε book2game-prep prompt, μετά handoff_to_ccgs.py, μετά skip brainstorm
- VERIFICATION: /start παρουσιάζει νέα επιλογή.

## ΦΑΣΗ 5: references update
**Outcome**: 5 αρχεία ενημερωμένα.

1. `docs/WORKFLOW-GUIDE.md` — νέα ενότητα Book Adaptation Entry
2. `.claude/docs/workflow-catalog.yaml` — βήμα `book-adapt` πριν το `brainstorm`
3. `.claude/docs/agent-roster.md` — σημείωση για narrative-director/world-builder
4. `README.md` — αναφορά book-to-game pipeline
5. `CLAUDE.md` — link προς book2game οδηγίες
- VERIFICATION: κάθε αρχείο περιέχει αναφορά σε book2game.

## ΦΑΣΗ 6: tests
**Outcome**: Επαλήθευση ολοκλήρωσης.

- Path αρχείου: `tests/integration/book2game-integration.test.md`
- Command: `bash scripts/run-tests.ps1` ή `./tests/integration/book2game-integration.test.md`
- Αποθήκευση: `tests/results/book2game-integration-result.json`
- Tests:
  1. Skill user-invocable και φορτώνεται
  2. handoff_to_ccgs.py παράγει game-concept.md
  3. validate_book2game.py περνάει σε valid output
  4. book2game-gate.sh warn όταν λείπει αρχείο
  5. /gate-check concept περνάει μετά από book2game flow
- VERIFICATION: όλα τα tests pass.

## HANDOFF
SPEC:"[Built]+[Verified]+[Next]"
- Built: skill στο repo, scripts, hook, /start update, references
- Verified: tests pass, gate check ok, anti-block checks pass, backup exists
- Next: human merge

HANDOFF: SPEC:"[Built]+[Verified]+[Next]"

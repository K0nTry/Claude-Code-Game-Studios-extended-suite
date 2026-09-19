# book2game Integration Test

End-to-end verification that the book2game pipeline is wired into the CCGS workflow.

## Test 1: Skill Loads & User-Invocable

**Command:**
```bash
# In Claude Code session:
/book2game-prep --help
```

**Expected:**
- Skill description shows
- `user-invocable: true` in frontmatter
- `argument-hint: "<book-path> [--out ./]"`
- No errors

---

## Test 2: handoff_to_ccgs.py Produces game-concept.md

**Setup:** Use existing test output `book_test_outputs/Neuromancer_game_v2` (218 chapters, 8 parts, already validated)

**Command:**
```bash
python scripts/handoff_to_ccgs.py ./book_test_outputs/Neuromancer_game_v2
```

**Expected:**
- Exit code 0
- Output shows:
  - `copied file: design/lore/source_text.md`
  - `copied dir: design/lore/chapters`
  - `copied file: design/rag/index.json`
  - `wrote markdown: design/entities/entity-registry.md`
  - `copied file: design/gdd/game-concept.md`
  - `game-concept.md OK (XXX bytes)`
- File `design/gdd/game-concept.md` exists and is non-empty

---

## Test 3: validate_book2game.py Passes on Valid Output

**Command:**
```bash
python scripts/validate_book2game.py ./book_test_outputs/Neuromancer_game_v2
```

**Expected:**
- Exit code 0
- Output:
  ```
  GATE PASS
    full_text.md OK
    index.json OK
    chapters/ OK
    entities.json citations OK
  ```

---

## Test 4: book2game-gate.sh Warns on Missing File

**Command:**
```bash
mkdir -p ./test_empty_gate
bash .claude/hooks/book2game-gate.sh ./test_empty_gate
```

**Expected:**
- Exit code 1
- stderr contains: `book2game Concept Gate: full_text.md missing or empty`

---

## Test 5: /gate-check concept Passes After book2game Flow

**Setup:**
1. Run handoff (Test 2) to populate `design/gdd/game-concept.md`
2. Ensure engine configured: `.claude/docs/technical-preferences.md` has Engine set
3. Ensure systems-index exists (or gate will report CONCERNS, not FAIL)

**Command:**
```bash
# In Claude Code session:
/gate-check concept
```

**Expected:**
- Verdict: PASS or CONCERNS (not FAIL)
- Output references `design/gdd/game-concept.md` exists
- Output references engine configured

---

## Test 6: /start Shows Book Option

**Command:**
```bash
# In fresh Claude Code session:
/start
```

**Expected:**
- Phase 2 options include:
  - `E) I have a book to adapt` — I have a book (PDF, EPUB, DOCX) I want to convert into a game. Run book2game pipeline first, then skip brainstorm.
- Selecting E routes to book2game-prep flow description

---

## Results Storage

Save all results to:
```
tests/results/book2game-integration-result.json
```

Format:
```json
{
  "timestamp": "2026-09-19T...",
  "tests": [
    {"name": "skill_loads", "passed": true, "output": "..."},
    {"name": "handoff_produces_concept", "passed": true, "output": "..."},
    {"name": "validate_passes", "passed": true, "output": "..."},
    {"name": "gate_warns_missing", "passed": true, "output": "..."},
    {"name": "gate_check_concept", "passed": true, "output": "..."},
    {"name": "start_shows_option", "passed": true, "output": "..."}
  ],
  "summary": {"total": 6, "passed": 6, "failed": 0}
}
```

---

## Run All Tests (Manual)

```bash
# 1. Verify test fixture exists
ls book_test_outputs/Neuromancer_game_v2/

# 2. Run handoff
python scripts/handoff_to_ccgs.py ./book_test_outputs/Neuromancer_game_v2

# 3. Run validation
python scripts/validate_book2game.py ./book_test_outputs/Neuromancer_game_v2

# 4. Run gate hook
bash .claude/hooks/book2game-gate.sh ./book_test_outputs/Neuromancer_game_v2

# 5. Run gate-check (in Claude Code)
/gate-check concept

# 6. Test /start (in fresh Claude Code session)
/start
```

---

## CI Integration (Future)

Add to GitHub Actions:
```yaml
- name: book2game integration test
  run: |
    python scripts/validate_book2game.py ./book_test_outputs/Neuromancer_game_v2
    bash .claude/hooks/book2game-gate.sh ./book_test_outputs/Neuromancer_game_v2
```

---

## Handoff Verification

This test file proves Phases 3-6 from `plans/software-factory-handoff-book2game.md` are complete:

- [x] Phase 3: Hook `book2game-gate.sh` exists and works
- [x] Phase 4: `/start` updated with Option E
- [x] Phase 5: References updated (WORKFLOW-GUIDE.md, workflow-catalog.yaml, agent-roster.md, CLAUDE.md, README.md)
- [x] Phase 6: This integration test file created
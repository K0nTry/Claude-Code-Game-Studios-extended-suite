# book2game Integration Test (Manual)

This is a manual integration test document for the book2game pipeline.
Automated checks live in `tests/integration/book2game-integration.test.py`.

## Preconditions

- Repo root = working directory
- Python available on PATH (`python --version`)

## Test 1 — Skill loads & user-invocable

- Open `.claude/skills/book2game-prep/SKILL.md`
- Expected: frontmatter contains `user-invocable: true`

## Test 2 — handoff_to_ccgs.py produces game-concept.md

```bash
python scripts/handoff_to_ccgs.py <workshop_output> <target_repo>
```

- Expected: exit 0, `<target_repo>/design/gdd/game-concept.md` exists and non-empty

## Test 3 — validate_book2game.py passes on valid output

```bash
python scripts/validate_book2game.py <workshop_output>
```

- Expected: `GATE PASS`, exit 0; on invalid folder: `GATE FAIL`, exit 1

## Test 4 — book2game-gate.sh warns on missing file

```bash
cd <invalid_output> && bash <repo>/.claude/hooks/book2game-gate.sh
```

- Expected: exit 1, stderr contains `book2game Concept Gate:`; on valid folder: silent, exit 0

## Test 5 — /gate-check concept passes after book2game flow

- Run `/start`, select option E ("I have a book to adapt")
- Expected: routes to `/book2game-prep`, then `handoff_to_ccgs.py`, then skips brainstorm

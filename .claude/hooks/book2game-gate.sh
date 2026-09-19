#!/bin/bash
# book2game-gate.sh — post-run verification hook for book2game-prep.
# Pass: silent (exit 0). Fail: warn to stderr + block Concept Gate (exit 1).
# Checks: source/full_text.md >0, index.json valid JSON, chapters/ has .md,
#         design/gdd/game-concept.md exists.
# Handles new nested structure: full_text.md in source/, entities.json in canon/.

fail() {
    echo "book2game Concept Gate: $1" >&2
    exit 1
}

DIR="${1:-.}"

[ -s "$DIR/source/full_text.md" ] || fail "source/full_text.md missing or empty"
[ -f "$DIR/index.json" ] || fail "index.json missing"

# JSON sanity check — pure bash builtins, no python/jq dependency (WSL-safe).
# Verifies the file starts with '{' and ends with '}' (ignoring whitespace).
json_first=$(head -c 1 "$DIR/index.json" | tr -d '[:space:]')
if [ "$json_first" != "{" ]; then
    fail "index.json invalid JSON"
fi
if [ -z "$(tr -d '[:space:]' < "$DIR/index.json" | grep -o '}') " ]; then
    fail "index.json invalid JSON"
fi

[ -d "$DIR/chapters" ] || fail "chapters/ missing"
ls "$DIR"/chapters/*.md >/dev/null 2>&1 || fail "chapters/ has no .md files"
[ -f "$DIR/design/gdd/game-concept.md" ] || fail "design/gdd/game-concept.md missing"

exit 0

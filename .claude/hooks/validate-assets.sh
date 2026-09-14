#!/bin/bash
# Claude Code PreToolUse hook: Validates asset files before Write/Edit
# Checks naming conventions and JSON validity for files in assets/ directory
#
# Exit behavior:
#   exit 0 = allow (advisory warnings printed to stderr)
#   exit 2 = block (permissionDecision: "deny" on build-breaking errors)
#
# Input schema (PreToolUse for Write/Edit):
# { "tool_name": "Write", "tool_input": { "file_path": "assets/data/foo.json", "content": "..." } }

INPUT=$(cat)

# Parse file path and content -- use jq if available, fall back to grep
if command -v jq >/dev/null 2>&1; then
    FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
    CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty')
else
    FILE_PATH=$(echo "$INPUT" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/"file_path"[[:space:]]*:[[:space:]]*"//;s/"$//')
    CONTENT=""
fi

# Normalize path separators (Windows backslash to forward slash)
FILE_PATH=$(echo "$FILE_PATH" | sed 's|\\|/|g')

# Only check files in assets/
if ! echo "$FILE_PATH" | grep -qE '(^|/)assets/'; then
    exit 0
fi

FILENAME=$(basename "$FILE_PATH")
WARNINGS=""   # Style/convention issues -- exit 0 with advisory message
ERRORS=""     # Build-breaking issues -- exit 2 to block the operation before disk write

# ADVISORY: Check naming convention (lowercase with underscores only)
# Naming issues are style violations -- warn but do not block
if echo "$FILENAME" | grep -qE '[A-Z[:space:]-]'; then
    WARNINGS="$WARNINGS\n  NAMING: $FILE_PATH must be lowercase with underscores (got: $FILENAME)"
fi

# BLOCKING: Check JSON validity for data files
# Invalid JSON will break runtime loading -- this is a build-breaking error
if echo "$FILE_PATH" | grep -qE '(^|/)assets/data/.*\.json$'; then
    # Find a working Python command
    PYTHON_CMD=""
    for cmd in python python3 py; do
        if command -v "$cmd" >/dev/null 2>&1; then
            PYTHON_CMD="$cmd"
            break
        fi
    done

    if [ -n "$PYTHON_CMD" ]; then
        if [ -n "$CONTENT" ]; then
            if ! echo "$CONTENT" | "$PYTHON_CMD" -m json.tool > /dev/null 2>&1; then
                ERRORS="$ERRORS\n  FORMAT: Content for $FILE_PATH is not valid JSON — fix syntax errors before writing."
            fi
        elif [ -f "$FILE_PATH" ]; then
            if ! "$PYTHON_CMD" -m json.tool "$FILE_PATH" > /dev/null 2>&1; then
                ERRORS="$ERRORS\n  FORMAT: $FILE_PATH is not valid JSON — fix syntax errors before writing."
            fi
        fi
    fi
fi

# Report warnings (advisory -- non-blocking)
if [ -n "$WARNINGS" ]; then
    echo -e "=== Asset Validation: Warnings ===$WARNINGS\n==================================\n(Warnings are advisory. Fix before final commit.)" >&2
fi

# Report errors and block if any build-breaking issues found
if [ -n "$ERRORS" ]; then
    echo -e "=== Asset Validation: ERRORS (Blocked before write) ===$ERRORS\n=======================================================\nWrite blocked: fix these errors before proceeding." >&2
    echo "{\"permissionDecision\": \"deny\", \"message\": \"Asset validation blocked: invalid JSON or asset format error.\"}"
    exit 2
fi

exit 0

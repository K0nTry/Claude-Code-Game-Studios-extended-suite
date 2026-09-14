#!/bin/bash
# Claude Code PreToolUse hook: Validates skill changes before Write/Edit
# Fires when any file inside .claude/skills/ is written or edited.
#
# Exit behavior:
#   exit 0 = allow
#   exit 2 = block with permissionDecision: "deny" if invalid structure (e.g. flat skill file or missing frontmatter)
#
# Input schema (PreToolUse for Write|Edit):
# { "tool_name": "Write", "tool_input": { "file_path": "...", "content": "..." } }

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

# Only act on files inside .claude/skills/
if ! echo "$FILE_PATH" | grep -qE '(^|/)\.claude/skills/'; then
    exit 0
fi

# Check structural rule: skill files must be at .claude/skills/[name]/SKILL.md (or similar subdirectory)
if echo "$FILE_PATH" | grep -qE '\.claude/skills/[^/]+\.md$'; then
    echo "=== Skill Validation: ERROR (Blocked) ===" >&2
    echo "Skill files must live in subdirectories: .claude/skills/[skill-name]/SKILL.md (got flat: $FILE_PATH)" >&2
    echo "=========================================" >&2
    exit 2
fi

# If writing/editing SKILL.md, verify basic frontmatter name / description if content provided
if echo "$FILE_PATH" | grep -qE 'SKILL\.md$'; then
    if [ -n "$CONTENT" ]; then
        if ! echo "$CONTENT" | grep -qE '^---' || ! echo "$CONTENT" | grep -qE '^name:'; then
            echo "=== Skill Validation: ERROR (Blocked) ===" >&2
            echo "Skill file $FILE_PATH is missing required frontmatter (name:) or YAML frontmatter block." >&2
            echo "=========================================" >&2
            exit 2
        fi
    fi
fi

echo "=== Skill Modified: $FILE_PATH ===" >&2
echo "Pre-tool validation passed." >&2
echo "====================================" >&2

exit 0

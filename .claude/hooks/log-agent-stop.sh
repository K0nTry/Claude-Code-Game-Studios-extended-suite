#!/bin/bash
# Claude Code SubagentStop hook: Log agent completion for audit trail
# Tracks when agents finish and their outcome
#
# Input schema (SubagentStop) — per Claude Code hooks reference:
# { "session_id": "...", "agent_id": "agent-abc123", "agent_type": "Explore",
#   "agent_transcript_path": "...", "last_assistant_message": "...", ... }
#
# The agent name is in `agent_type`, NOT `agent_name`. Reading `.agent_name`
# returns null on every invocation, so the fallback "unknown" is always used
# and the audit trail captures nothing useful.

INPUT=$(cat)

# Parse session_id, agent_id, agent_type -- use jq if available (-s to handle streams), fall back to grep
if command -v jq >/dev/null 2>&1; then
    SESSION_ID=$(echo "$INPUT" | jq -s -r '(.[0] // {}) | .session_id // "unknown_session"' 2>/dev/null)
    AGENT_ID=$(echo "$INPUT" | jq -s -r '(.[0] // {}) | .agent_id // "unknown_agent_id"' 2>/dev/null)
    AGENT_TYPE=$(echo "$INPUT" | jq -s -r '(.[0] // {}) | .agent_type // "unknown"' 2>/dev/null)
else
    SESSION_ID=$(echo "$INPUT" | grep -oE '"session_id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -n 1 | sed 's/"session_id"[[:space:]]*:[[:space:]]*"//;s/"$//')
    AGENT_ID=$(echo "$INPUT" | grep -oE '"agent_id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -n 1 | sed 's/"agent_id"[[:space:]]*:[[:space:]]*"//;s/"$//')
    AGENT_TYPE=$(echo "$INPUT" | grep -oE '"agent_type"[[:space:]]*:[[:space:]]*"[^"]*"' | head -n 1 | sed 's/"agent_type"[[:space:]]*:[[:space:]]*"//;s/"$//')
fi

# Sanitize fields to guarantee single-line scalar values (prevent concurrency/newline/pipe injection)
sanitize_field() {
    local val="$1"
    local default="$2"
    val=$(echo "$val" | head -n 1 | tr -d '\r\n' | tr '|' '_' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
    if [ -z "$val" ] || [ "$val" = "null" ]; then
        val="$default"
    fi
    echo "$val"
}

SESSION_ID=$(sanitize_field "$SESSION_ID" "unknown_session")
AGENT_ID=$(sanitize_field "$AGENT_ID" "unknown_agent_id")
AGENT_TYPE=$(sanitize_field "$AGENT_TYPE" "unknown")

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SESSION_LOG_DIR="production/session-logs"

mkdir -p "$SESSION_LOG_DIR" 2>/dev/null

# Atomic lock using mkdir to prevent interleaved writes under concurrent execution
LOCK_DIR="$SESSION_LOG_DIR/audit.lock"
while ! mkdir "$LOCK_DIR" 2>/dev/null; do
    sleep 0.01
done

echo "$TIMESTAMP | STOP | session_id: $SESSION_ID | agent_id: $AGENT_ID | agent_type: $AGENT_TYPE" >> "$SESSION_LOG_DIR/agent-audit.log" 2>/dev/null

rmdir "$LOCK_DIR" 2>/dev/null

exit 0

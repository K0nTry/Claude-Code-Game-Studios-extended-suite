#!/usr/bin/env bash
# post-compact.sh — fires after conversation compaction
# Injects the bounded active.md session state directly into stdout per T-032.

ACTIVE="production/session-state/active.md"

echo "=== Context Restored After Compaction ==="

if [ -f "$ACTIVE" ]; then
  echo "=== ACTIVE SESSION STATE RE-INJECTED ==="
  cat "$ACTIVE"
  echo "=== END ACTIVE SESSION STATE ==="
else
  echo "No session state file found at $ACTIVE"
  echo "If you were mid-task, check production/session-logs/ for the last session audit."
fi

echo "========================================="

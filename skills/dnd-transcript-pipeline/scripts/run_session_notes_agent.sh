#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <session> <provider> [extra args...]"
  echo "Example: $0 15 codex --force"
  exit 1
fi

SESSION="$1"
PROVIDER="$2"
shift 2

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${DND_REPO_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"
ELLARA_ROOT="${ELLARA_ROOT:-$(cd "$REPO_ROOT/.." && pwd)/ellara}"
RUNNER_PY="$REPO_ROOT/scripts/transcription/run_session_notes_agent.py"
RAW_NOTES="$ELLARA_ROOT/Session Notes/Raw Session ${SESSION}.md"
OUTPUT_FILE="$ELLARA_ROOT/Session Notes/Session ${SESSION}.md"

if [ ! -f "$RUNNER_PY" ]; then
  echo "Session notes runner not found: $RUNNER_PY"
  exit 1
fi

if [ ! -f "$RAW_NOTES" ]; then
  echo "Raw session notes not found: $RAW_NOTES"
  exit 1
fi

python3 "$RUNNER_PY" "$SESSION" "$RAW_NOTES" "$OUTPUT_FILE" --provider "$PROVIDER" "$@"

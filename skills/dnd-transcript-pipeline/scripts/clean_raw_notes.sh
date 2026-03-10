#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <session>"
  echo "Example: $0 15"
  exit 1
fi

SESSION="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${DND_REPO_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"
ELLARA_ROOT="${ELLARA_ROOT:-$(cd "$REPO_ROOT/.." && pwd)/ellara}"
RAW_NOTES_PY="$REPO_ROOT/scripts/transcription/generate_raw_notes.py"
RAW_NOTES_FILE="$ELLARA_ROOT/Session Notes/Raw Session ${SESSION}.md"

if [ ! -f "$RAW_NOTES_PY" ]; then
  echo "Raw notes script not found: $RAW_NOTES_PY"
  exit 1
fi

if [ ! -f "$RAW_NOTES_FILE" ]; then
  echo "Raw session notes not found: $RAW_NOTES_FILE"
  exit 1
fi

python3 "$RAW_NOTES_PY" clean "$RAW_NOTES_FILE"

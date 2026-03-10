#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <session> <provider> [extra args...]"
  echo "Example: $0 15 codex --limit 10 --finalize"
  exit 1
fi

SESSION="$1"
PROVIDER="$2"
shift 2

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${DND_REPO_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"
ELLARA_ROOT="${ELLARA_ROOT:-$(cd "$REPO_ROOT/.." && pwd)/ellara}"
RUNNER_PY="$REPO_ROOT/scripts/transcription/run_raw_notes_subagents.py"
MANIFEST="$ELLARA_ROOT/Session Notes/Raw Session ${SESSION} Chunks/chunks_manifest.json"

if [ ! -f "$RUNNER_PY" ]; then
  echo "Runner script not found: $RUNNER_PY"
  exit 1
fi

if [ ! -f "$MANIFEST" ]; then
  echo "Chunk manifest not found: $MANIFEST"
  exit 1
fi

python3 "$RUNNER_PY" "$MANIFEST" --provider "$PROVIDER" "$@"

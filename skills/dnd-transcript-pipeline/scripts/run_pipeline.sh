#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <session> <audio_dir> [extra run_session_auto.py args...]"
  echo "Example: $0 22 /path/to/session-22 --dry-run"
  exit 1
fi

SESSION="$1"
AUDIO_DIR="$2"
shift 2

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -n "${DND_REPO_ROOT:-}" ]; then
  REPO_ROOT="$DND_REPO_ROOT"
elif REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null)"; then
  :
else
  REPO_ROOT="$SCRIPT_DIR"
  while [ "$REPO_ROOT" != "/" ] && [ ! -f "$REPO_ROOT/scripts/transcription/run_session_auto.py" ]; do
    REPO_ROOT="$(dirname "$REPO_ROOT")"
  done
fi

PIPELINE_PY="$REPO_ROOT/scripts/transcription/run_session_auto.py"
if [ ! -f "$PIPELINE_PY" ]; then
  echo "Pipeline script not found: $PIPELINE_PY" >&2
  exit 1
fi

PYTHON_BIN="$REPO_ROOT/.venv-transcription/bin/python3"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="python3"
fi

export PYTHONDONTWRITEBYTECODE=1
exec "$PYTHON_BIN" -B "$PIPELINE_PY" --session "$SESSION" --audio-dir "$AUDIO_DIR" "$@"

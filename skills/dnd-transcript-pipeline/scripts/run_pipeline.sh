#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <session> <audio_dir> [extra pipeline args...]"
  echo "Example: $0 15 /path/to/session-audio --skip-transcribe"
  exit 1
fi

SESSION="$1"
AUDIO_DIR="$2"
shift 2

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${DND_REPO_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"
PIPELINE_PY="$REPO_ROOT/scripts/transcription/run_transcript_pipeline.py"

if [ ! -f "$PIPELINE_PY" ]; then
  echo "Pipeline script not found: $PIPELINE_PY"
  exit 1
fi

python3 "$PIPELINE_PY" --session "$SESSION" --audio-dir "$AUDIO_DIR" "$@"

#!/bin/bash
set -euo pipefail

AUDIO_DIR="/home/babu/source/craig-GMNUKowRrjIC"
DND_DIR="/home/babu/source/dnd"
SESSION_ASSETS_DIR="/home/babu/source/dnd/src/assets/sessions/transcripts/Session 15"
ASSETS_COMBINED="/home/babu/source/dnd/src/assets/sessions/transcripts/session_15_raw.txt"
ELLARA_TRANSCRIPT="/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session 15.txt"

VENV_PATH="$HOME/.gemini/tmp/transcribe_env"
VENV_SITE="$VENV_PATH/lib/python3.12/site-packages"

if [ ! -d "$VENV_PATH" ]; then
  echo "Missing transcription venv at $VENV_PATH"
  exit 1
fi

cd "$DND_DIR"

# Refresh entity spellings used as the Whisper initial prompt.
node scripts/generate_entity_list.js

export LD_LIBRARY_PATH="$VENV_SITE/nvidia/cudnn/lib:$VENV_SITE/nvidia/cublas/lib:$VENV_SITE/nvidia/cudart/lib:${LD_LIBRARY_PATH:-}"

# Start from clean per-speaker outputs for this session.
find "$AUDIO_DIR" -maxdepth 1 -type f -name '*.aac.txt' -delete

# Transcribe all speaker-isolated Craig tracks.
WHISPER_BEAM_SIZE=1 "$VENV_PATH/bin/python3" -u scripts/transcription/transcribe.py "$AUDIO_DIR"

# Combine into one chronological transcript.
COMBINED_TMP="$AUDIO_DIR/session-15-combined.txt"
COMBINED_FINAL="$AUDIO_DIR/session-15-combined-normalized.txt"
"$VENV_PATH/bin/python3" scripts/transcription/combine_transcripts.py "$AUDIO_DIR" "$COMBINED_TMP"

# Match prior transcript naming style.
sed -E 's/Whitaker "Witty" Whitman VI/Witty/g' "$COMBINED_TMP" > "$COMBINED_FINAL"

mkdir -p "$SESSION_ASSETS_DIR"
cp "$AUDIO_DIR"/*.aac.txt "$SESSION_ASSETS_DIR"/
cp "$COMBINED_FINAL" "$ASSETS_COMBINED"
cp "$COMBINED_FINAL" "$ELLARA_TRANSCRIPT"

echo "Session 15 transcript pipeline complete."
echo "Per-speaker transcripts: $SESSION_ASSETS_DIR"
echo "Combined transcript: $ELLARA_TRANSCRIPT"

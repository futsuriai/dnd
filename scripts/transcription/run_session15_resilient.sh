#!/bin/bash
set -euo pipefail

AUDIO_DIR="/home/babu/source/craig-GMNUKowRrjIC"
DND_DIR="/home/babu/source/dnd"
SESSION_ASSETS_DIR="/home/babu/source/dnd/src/assets/sessions/transcripts/Session 15"
ASSETS_COMBINED="/home/babu/source/dnd/src/assets/sessions/transcripts/session_15_raw.txt"
ELLARA_TRANSCRIPT="/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session 15.txt"
STATE_LOG="$AUDIO_DIR/session-15-resilient.log"

VENV_PATH="$HOME/.gemini/tmp/transcribe_env"
VENV_SITE="$VENV_PATH/lib/python3.12/site-packages"
PY="$VENV_PATH/bin/python3"

if [ ! -d "$VENV_PATH" ]; then
  echo "Missing transcription venv at $VENV_PATH"
  exit 1
fi

mkdir -p "$SESSION_ASSETS_DIR"

cd "$DND_DIR"
node scripts/generate_entity_list.js

export LD_LIBRARY_PATH="$VENV_SITE/nvidia/cudnn/lib:$VENV_SITE/nvidia/cublas/lib:$VENV_SITE/nvidia/cudart/lib:${LD_LIBRARY_PATH:-}"

log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$*" | tee -a "$STATE_LOG"
}

is_good_output() {
  local f="$1"
  [ -s "$f" ] || return 1
  local lines
  lines=$(wc -l < "$f" || echo 0)
  [ "$lines" -ge 20 ]
}

transcribe_one() {
  local audio_file="$1"
  local out_file="$2"
  local base
  base=$(basename "$audio_file")
  local file_log="$AUDIO_DIR/${base}.transcribe.log"
  local tmp_out="${out_file}.tmp"

  local attempt=1
  while [ "$attempt" -le 6 ]; do
    local model="large-v3"
    local compute="float16"
    local device="cuda"

    if [ "$attempt" -ge 3 ]; then
      model="medium"
    fi
    if [ "$attempt" -ge 5 ]; then
      model="small"
    fi

    log "${base}: attempt ${attempt} (model=${model}, device=${device}, compute=${compute})"

    : > "$file_log"
    if WHISPER_MODEL_SIZE="$model" WHISPER_DEVICE="$device" WHISPER_COMPUTE_TYPE="$compute" WHISPER_BEAM_SIZE=1 \
      "$PY" -u scripts/transcription/transcribe.py "$audio_file" "$tmp_out" >> "$file_log" 2>&1; then
      if is_good_output "$tmp_out"; then
        mv "$tmp_out" "$out_file"
        log "${base}: success ($(wc -l < "$out_file") lines)"
        return 0
      fi
      log "${base}: run exited 0 but output is too small/empty"
    else
      log "${base}: run failed (exit=$?)"
    fi

    rm -f "$tmp_out"
    attempt=$((attempt + 1))
    sleep 3
  done

  log "${base}: FAILED after retries"
  return 1
}

log "Starting resilient Session 15 pipeline"

# Rebuild transcripts from scratch for this session
find "$AUDIO_DIR" -maxdepth 1 -type f -name '*.aac.txt' -delete

mapfile -t audio_files < <(find "$AUDIO_DIR" -maxdepth 1 -type f -name '*.aac' | sort -V)
if [ "${#audio_files[@]}" -eq 0 ]; then
  log "No .aac files found in $AUDIO_DIR"
  exit 1
fi

for audio in "${audio_files[@]}"; do
  out="${audio}.txt"
  transcribe_one "$audio" "$out"
done

COMBINED_TMP="$AUDIO_DIR/session-15-combined.txt"
COMBINED_FINAL="$AUDIO_DIR/session-15-combined-normalized.txt"

"$PY" scripts/transcription/combine_transcripts.py "$AUDIO_DIR" "$COMBINED_TMP" >> "$STATE_LOG" 2>&1
sed -E 's/Whitaker "Witty" Whitman VI/Witty/g' "$COMBINED_TMP" > "$COMBINED_FINAL"

cp "$AUDIO_DIR"/*.aac.txt "$SESSION_ASSETS_DIR"/
cp "$COMBINED_FINAL" "$ASSETS_COMBINED"
cp "$COMBINED_FINAL" "$ELLARA_TRANSCRIPT"

log "Session 15 pipeline complete"
log "Per-speaker transcripts: $SESSION_ASSETS_DIR"
log "Combined transcript: $ELLARA_TRANSCRIPT"

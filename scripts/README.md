# Scripts Directory

This directory contains utility scripts for managing the D&D Campaign Wiki, specifically for session transcription and data management.

## 🎙️ Session Transcription Workflow

The transcription system uses `faster-whisper` (AI-powered) to process multiple audio tracks (e.g., from Craig) and combine them into a single chronological script.

### 1. Setup Environment
Transcribing requires a Python environment with CUDA support. This is typically set up in `~/.gemini/tmp/transcribe_env`.

To run a job, use the helper script which sets up the necessary NVIDIA library paths:
```bash
# Usage: bash scripts/transcription/run_job.sh <audio_directory>
bash scripts/transcription/run_job.sh "/path/to/session-audio"
```

### 2. Speaker Mapping
Before or after transcription, ensure the usernames/filenames are mapped to character names in:
`scripts/transcription/speaker_map.json`

Example:
```json
{
  "pushanka": "Berridin",
  "icegecko": "Nyx",
  "aurus": "GM"
}
```

### 3. Transcribe (Multiple Files)
If you want to run it manually or in the background:
```bash
# Run in background
nohup bash scripts/transcription/run_job.sh "/path/to/audio" > transcription.log 2>&1 &
```
The script will generate a `.txt` file for every audio file in the directory.

### 4. Combine Transcripts
Once all `.txt` files are generated, merge them into a single sorted dialogue:
```bash
# Usage: python3 scripts/transcription/combine_transcripts.py <directory> <output_filename>
python3 scripts/transcription/combine_transcripts.py "/path/to/audio" "session_XX_transcript.txt"
```

---

## 📋 Entity Management

### Generate Entity List
To update `ENTITY_LIST.md` with the latest IDs and Names from the `src/store/*.js` files:

```bash
node scripts/generate_entity_list.js
```
*Note: This is automatically handled by the Copilot/Gemini prompts, but can be run manually to verify data.*

---

## Directory Structure
- `transcription/`
    - `run_job.sh`: Entry point for transcription jobs (handles CUDA paths).
    - `transcribe.py`: The AI transcription engine.
    - `combine_transcripts.py`: Logic to merge and sort multiple tracks.
    - `speaker_map.json`: Mapping of usernames to Character names.
    - `TRANSCRIPTION_GUIDE.md`: Detailed technical setup guide.
- `generate_entity_list.js`: Scans store files to build the master entity list.

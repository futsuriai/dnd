# Scripts Directory

This directory contains utility scripts for managing the D&D Campaign Wiki, specifically for session transcription, transcript reconciliation, and data management.

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

## 🔀 Transcript Reconciliation Workflow

When a session has multiple transcript sources (e.g., Zoom's built-in transcription + a Whisper run on the recording), they can be reconciled into a single high-quality diarized transcript. This is a 5-stage pipeline combining mechanical alignment with LLM-assisted refinement.

### Model Recommendation

All LLM-assisted stages (3, 4, 5) should use a strong reasoning model. **`gpt-5.2-codex`** is recommended — it handles speaker attribution, name correction, and prose summarization reliably across all stages. Lighter models (e.g., Sonnet-class) may silently fail on larger chunks or produce lower-quality speaker attribution.

When using Copilot CLI, specify the model explicitly:
```
task agent (general-purpose, model: gpt-5.2-codex)
```

### Why two sources?
| Source | Strengths | Weaknesses |
|--------|-----------|------------|
| **Zoom transcript** | Speaker labels (diarization), wall-clock timestamps | Garbles unusual names, misses words, fragments sentences |
| **Whisper transcript** | Better word accuracy, more complete sentences | No speaker labels, timestamps relative to recording start (00:00:00) |

Neither source alone produces a good transcript for a D&D session with fantasy names. Combining them yields speaker-labeled text with accurate wording.

### Stage 1: Timestamp Alignment

Whisper timestamps start at `00:00:00` (recording start) while Zoom uses wall-clock time. The alignment script finds matching dialogue lines between both files to compute the offset.

```bash
python3 scripts/transcription/align_whisper_timestamps.py \
    session-XX-zoom.txt \
    session-XX-whisper.txt
```

**How it works:**
1. Parses both files and normalizes text for comparison
2. Uses `difflib.SequenceMatcher` to find high-confidence content matches across the first ~60 Whisper segments
3. Computes the median offset across all matched pairs (typically consistent within ±6 seconds)
4. Rewrites Whisper timestamps in-place

Use `--dry-run` to preview the offset without modifying the file.

**Example:** For session 14, the offset was **49,152 seconds** (13:39:12) — Whisper's `00:00:00` corresponded to Zoom's `13:39:12`, confirmed by 4 triangulation points across 52 minutes of content.

### Stage 2: Mechanical Merge + Chunk Preparation

```bash
python3 scripts/transcription/merge_transcripts.py \
    session-XX-zoom.txt \
    session-XX-whisper.txt \
    ENTITY_LIST.md \
    output_dir/
```

This produces:
- `output_dir/chunks/` — Paired zoom/whisper files for each ~50-turn chunk
- `output_dir/merged_mechanical.txt` — A regex-only baseline merge (usable but not ideal)

**The mechanical merge** assigns Whisper segments to Zoom turns by timestamp overlap, then applies regex name corrections from `name_corrections.json`. This works for ~80% of content but fails when:
- A Whisper segment spans multiple speakers (Whisper doesn't know about speaker changes)
- Names are phonetically garbled in ways regex can't catch (e.g., "yesterday" → "Ysidor")
- Both sources have different errors for the same passage

### Stage 3: LLM-Assisted Refinement

Each chunk pair is processed through an LLM via Copilot CLI `task` agents (`general-purpose`, model: `gpt-5.2-codex`):

> Read the Zoom text (speaker labels) and Whisper text (better words) for this segment.
> Combine them: use Zoom for who is speaking, synthesize the best wording from both sources.
> Apply canonical name corrections. Merge consecutive same-speaker turns that are one thought.
> Drop garbled Whisper artifacts.

**Key prompt details:**
- Canonical speaker names provided: `GM, Ysidor, Ellara, Nyx, Berridin, Whitaker`
- Name correction table provided (from `name_corrections.json`)
- Output format: `[HH:MM:SS] Speaker: text`
- Chunks processed in parallel; ~50 turns per chunk keeps context manageable

For session 14, this was 32 LLM-processed chunks + 3 Zoom-only chunks (pre-recording period with no Whisper coverage), producing `session-14-diarized.txt`.

A final regex pass catches any remaining name variants the LLM missed.

### Stage 4: OOC Dialogue Filtering

The diarized transcript contains both in-game content and out-of-character (OOC) table talk. An LLM pass filters these apart.

```bash
# Split into chunks
python3 scripts/transcription/filter_ooc.py prepare session-XX-diarized.txt ./ooc_chunks

# View the prompt template
python3 scripts/transcription/filter_ooc.py prompt

# (Process each chunk through LLM — see prompt template)
# Save results as ooc_chunks/chunk_NN_filtered.txt

# Concatenate filtered chunks
python3 scripts/transcription/filter_ooc.py concat ./ooc_chunks session-XX-ingame.txt
```

**Removed as OOC:**
- Pre/post-game chatter (tech setup, scheduling, birthdays)
- Real-world tangents (Disney movie discussions, pet stories)
- Meta-commentary about the recording or game mechanics
- Player banter not spoken in-character

**Kept as in-game:**
- GM narration and world-building
- In-character dialogue (players speaking as their characters)
- NPC dialogue and descriptions
- Session recaps and in-game strategic discussion

**Session 14 results:**
| File | Entries | Size |
|------|---------|------|
| `session-14-diarized.txt` (full) | 1,056 | 120 KB |
| `session-14-ingame.txt` (filtered) | 583 | 80 KB |
| Removed (OOC) | 473 (45%) | — |

### Stage 5: Raw Session Notes Generation

The in-game transcript is converted into condensed prose-style session notes matching the format of Raw Sessions 1–4 in the campaign wiki.

```bash
# Split into narrative chunks
python3 scripts/transcription/generate_raw_notes.py prepare session-XX-ingame.txt ./notes_chunks

# View the prompt template
python3 scripts/transcription/generate_raw_notes.py prompt

# (Process each chunk through LLM — see prompt template)
# Save results as notes_chunks/chunk_N_notes.txt

# Concatenate and apply name corrections
python3 scripts/transcription/generate_raw_notes.py concat ./notes_chunks "Raw Session XX.md"
```

**Notes format:**
- Casual shorthand prose with `---` scene breaks
- All in-character dialogue preserved as `character: "quote"`
- GM narration condensed into descriptions
- Dice rolls/checks noted inline
- No timestamps in output
- ~120 entries per chunk (larger chunks = more narrative continuity)

The concat step applies canonical name corrections (e.g., `here's embrace` → `hýrda's embrace`, `heroterra` → `hieroterra`, `nites` → `nýtes`) automatically.

### Quick Reference: Full Pipeline

```bash
# Stage 1: Align Whisper timestamps to Zoom clock
python3 scripts/transcription/align_whisper_timestamps.py zoom.txt whisper.txt

# Stage 2: Prepare chunks for LLM merge
python3 scripts/transcription/merge_transcripts.py zoom.txt whisper.txt ENTITY_LIST.md ./merge_output

# Stage 3: LLM merge (via Copilot CLI, model: gpt-5.2-codex)
#    Process each chunk pair in merge_output/chunks/
#    Input:  cN_zoom.txt + cN_whisper.txt → cN_merged.txt
#    Concatenate all merged chunks → session-XX-diarized.txt
#    Run final regex pass for remaining name variants

# Stage 4: OOC filtering
python3 scripts/transcription/filter_ooc.py prepare session-XX-diarized.txt ./ooc_chunks
#    Process each chunk through LLM (model: gpt-5.2-codex)
python3 scripts/transcription/filter_ooc.py concat ./ooc_chunks session-XX-ingame.txt

# Stage 5: Raw session notes
python3 scripts/transcription/generate_raw_notes.py prepare session-XX-ingame.txt ./notes_chunks
#    Process each chunk through LLM (model: gpt-5.2-codex)
python3 scripts/transcription/generate_raw_notes.py concat ./notes_chunks "Raw Session XX.md"
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
    - `align_whisper_timestamps.py`: Stage 1 — aligns Whisper timestamps to a Zoom transcript's clock.
    - `merge_transcripts.py`: Stage 2 — mechanical merge + chunk preparation for LLM refinement.
    - `filter_ooc.py`: Stage 4 — chunking, prompts, and concatenation for OOC dialogue filtering.
    - `generate_raw_notes.py`: Stage 5 — chunking, prompts, and concatenation for raw session notes.
    - `speaker_map.json`: Mapping of usernames to Character names.
    - `name_corrections.json`: ASR mis-transcription → canonical name mappings.
    - `TRANSCRIPTION_GUIDE.md`: Detailed technical setup guide.
- `generate_entity_list.js`: Scans store files to build the master entity list.

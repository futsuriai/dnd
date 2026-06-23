# Scripts Directory

This directory contains utility scripts for managing the D&D Campaign Wiki, specifically for session transcription, transcript reconciliation, and data management.

## 🎙️ Session Transcription Workflow

The transcription system uses `faster-whisper` (AI-powered) to process multiple audio tracks (e.g., from Craig) and combine them into a single chronological script.

For the complete agent-readable workflow from raw audio through website updates, use:
`AGENT_SESSION_PIPELINE.md`.

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

### 5. VAD Compaction for Cloud Transcription
The local `faster-whisper` script already uses VAD and restores original timestamps before writing transcript lines. If a future transcription step sends audio to a cloud/serverless model, compact each speaker file first and keep the generated timeline manifest:

```bash
python3 scripts/transcription/vad_compact.py compact \
  "/path/to/speaker.aac" \
  "/path/to/speaker.vad.wav" \
  "/path/to/speaker.vad.json"
```

Send only `speaker.vad.wav` to the cloud model. After receiving a transcript with timestamps relative to the compact audio, remap it back to the original recording timeline:

```bash
python3 scripts/transcription/vad_compact.py remap \
  "/path/to/speaker.vad.json" \
  "/path/to/speaker.vad.txt" \
  "/path/to/speaker.aac.txt"
```

The compact audio keeps a short synthetic silence gap between retained VAD islands. This adds a small amount of billable audio, but prevents unrelated phrases from being smashed together in a way that can cause empty or over-merged cloud results. The remapped `speaker.aac.txt` is then safe to feed into `combine_transcripts.py`, because its timestamps are back in original session time.

For local `faster-whisper` runs, VAD can be tuned without editing code:

```bash
WHISPER_VAD_THRESHOLD=0.5 \
WHISPER_VAD_MIN_SILENCE_MS=2000 \
WHISPER_VAD_SPEECH_PAD_MS=400 \
python3 scripts/transcription/transcribe.py "/path/to/speaker.aac"
```

### 6. One-Command Session Pipeline (Recommended)
To run the full Session pipeline (entity refresh, transcription retries, combine, name fixes, final copies, OOC split, raw-note chunk prep, optional raw-note agents, optional polished-session generation, manifest):
Gladia/cloud transcription is the default provider. Store the key in `.env.local` before running audio transcription:

```bash
GLADIA_API_KEY=...
```

```bash
python3 scripts/transcription/run_transcript_pipeline.py \
  --session 15 \
  --audio-dir "/path/to/session-audio"
```

Each speaker file is locally compacted with VAD before upload, transcribed with Gladia custom vocabulary, remapped back to original timestamps, and then passed through the same combine/normalize/OOC/raw-note pipeline. If Gladia returns no utterances for non-empty compact speech, the script retries once with a less aggressive compact file before writing the final transcript.

Use local Whisper only when intentionally running a local fallback or provider comparison:

```bash
python3 scripts/transcription/run_transcript_pipeline.py \
  --session 15 \
  --audio-dir "/path/to/session-audio" \
  --transcription-provider whisper
```

For a provider baseline comparison, run the pipeline twice with `--stop-after-transcript`: once with `--transcription-provider whisper --clean`, archive `Transcript Session XX.txt` as `Transcript Session XX - Whisper Baseline.txt`, then run with `--transcription-provider gladia --clean` and archive `Transcript Session XX.txt` as `Transcript Session XX - Gladia Baseline.txt`. Compare the two archived normalized transcripts by timestamp windows before choosing which one becomes the canonical review transcript.

### 6a. Full End-to-End Checklist: Raw Audio -> Raw Session Candidate -> Session MD

`AGENT_SESSION_PIPELINE.md` is the authoritative runbook. At a high level, the sequence from Craig-style speaker audio streams to completed website notes is:

1. Put all speaker-isolated audio files for the session in one directory.
2. Make sure `scripts/transcription/speaker_map.json` is current.
3. Run the transcript pipeline with `--stop-after-transcript` and review the canonical transcript.
4. Run the annotation-first OOC cleanup when OOC chatter needs pruning, then approve `Transcript Session XX - Annotation Cleaned Candidate.txt`.
5. Resume the pipeline to generate raw-note chunks and `Raw Session XX Candidate.md`.
6. Run raw-note reconciliation into `Raw Session XX Reconciled Candidate.md`.
7. Review and promote the reconciled candidate to `Raw Session XX.md`.
8. Generate polished `Session XX.md`, sync it into `src/assets/sessions/session-XX.md`, update stores/views, and run `npm run sync-check`.

The pipeline can generate:
   - per-speaker transcripts
   - combined normalized transcript
   - OOC-filtered transcript variants
   - raw-note chunk files and `chunks_manifest.json`
   - raw-note candidate and pipeline manifest

Concrete commands:
```bash
# 1) Build transcript artifacts, then stop for review
python3 scripts/transcription/run_transcript_pipeline.py \
  --session 15 \
  --audio-dir "/path/to/session-audio" \
  --stop-after-transcript

# 2) After transcript/OOC review, generate the raw-note candidate
python3 scripts/transcription/run_transcript_pipeline.py \
  --session 15 \
  --audio-dir "/path/to/session-audio" \
  --resume-after-transcript \
  --run-ooc-annotation-provider codex \
  --raw-notes-source-mode annotation \
  --skip-raw-notes-prep

# 3) After cleaned transcript approval, generate the raw-note candidate
python3 scripts/transcription/run_transcript_pipeline.py \
  --session 15 \
  --audio-dir "/path/to/session-audio" \
  --resume-after-transcript \
  --raw-notes-source-mode canonical \
  --run-raw-notes-provider codex \
  --raw-notes-finalize \
  --raw-notes-output "/home/babu/source/ellara/Session Notes/Raw Session 15 Candidate.md" \
  --run-raw-notes-reconcile-provider codex \
  --raw-notes-reconciled-output "/home/babu/source/ellara/Session Notes/Raw Session 15 Reconciled Candidate.md"

# 4) After review, validate and promote the reconciled candidate
python3 scripts/transcription/validate_raw_notes.py \
  "/home/babu/source/ellara/Session Notes/Raw Session 15 Reconciled Candidate.md" \
  --session 15 \
  --allow-review-lines

cp "/home/babu/source/ellara/Session Notes/Raw Session 15 Reconciled Candidate.md" \
  "/home/babu/source/ellara/Session Notes/Raw Session 15.md"
```

If you already have the per-speaker `.txt` files and only want to rebuild the downstream artifacts:
```bash
python3 scripts/transcription/run_transcript_pipeline.py \
  --session 15 \
  --audio-dir "/path/to/session-audio" \
  --skip-transcribe
```

Useful flags:
```bash
# Reuse existing per-speaker transcripts and only rebuild final artifacts
python3 scripts/transcription/run_transcript_pipeline.py \
  --session 15 \
  --audio-dir "/path/to/session-audio" \
  --skip-transcribe

# Force fresh per-speaker transcript generation
python3 scripts/transcription/run_transcript_pipeline.py \
  --session 15 \
  --audio-dir "/path/to/session-audio" \
  --clean

# Skip raw-note chunk preparation if you only want transcript artifacts
python3 scripts/transcription/run_transcript_pipeline.py \
  --session 15 \
  --audio-dir "/path/to/session-audio" \
  --skip-raw-notes-prep

# After transcript review, prepare raw-note chunks and dispatch them through Codex
python3 scripts/transcription/run_transcript_pipeline.py \
  --session 15 \
  --audio-dir "/path/to/session-audio" \
  --resume-after-transcript \
  --run-raw-notes-provider codex \
  --raw-notes-finalize \
  --raw-notes-output "/home/babu/source/ellara/Session Notes/Raw Session 15 Candidate.md" \
  --run-raw-notes-reconcile-provider codex \
  --raw-notes-reconciled-output "/home/babu/source/ellara/Session Notes/Raw Session 15 Reconciled Candidate.md"

# After reviewing and promoting Raw Session 15 Candidate.md, generate polished notes
python3 scripts/transcription/run_session_notes_agent.py \
  15 \
  "/home/babu/source/ellara/Session Notes/Raw Session 15.md" \
  "/home/babu/source/ellara/Session Notes/Session 15.md" \
  --provider codex \
  --workspace-root /home/babu/source \
  --force

# Show planned raw-note dispatches without running the model
python3 scripts/transcription/run_transcript_pipeline.py \
  --session 15 \
  --audio-dir "/path/to/session-audio" \
  --skip-transcribe \
  --run-raw-notes-provider codex \
  --raw-notes-dry-run
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

### Stage 4: Annotation-First OOC Cleanup

The diarized transcript contains both in-game content and out-of-character (OOC) table talk. The current OOC cleanup flow is annotation-first: the LLM emits JSONL decisions, and `filter_ooc.py apply` deterministically rebuilds the cleaned transcript plus review artifacts.

```bash
# Split into chunks
python3 scripts/transcription/filter_ooc.py prepare session-XX-diarized.txt ./ooc_chunks

# View the prompt template
python3 scripts/transcription/filter_ooc.py prompt --chunk-file ./ooc_chunks/chunk_00.txt

# (Process each chunk through LLM — see prompt template)
# Save results as ooc_chunks/chunk_NN_annotations.jsonl

# Apply annotations into deterministic review outputs
python3 scripts/transcription/filter_ooc.py apply \
  ./ooc_chunks/annotation_manifest.json \
  ./ooc_chunks \
  "Transcript Session XX - Annotation Cleaned Candidate.txt" \
  "Transcript Session XX - Annotation Cleanup Report.md" \
  "Transcript Session XX - Annotation Ambiguous Review.md" \
  "Transcript Session XX - Annotation Cleaned Candidate.diff"
```

Or dispatch all annotation chunks through an agent and apply them:

```bash
python3 scripts/transcription/run_ooc_annotation_agents.py \
  ./ooc_chunks/annotation_manifest.json \
  --provider codex \
  --workspace-root /home/babu/source \
  --apply
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
- Recap continuity facts and in-game strategic discussion

Review the cleaned candidate diff before replacing the canonical transcript.

### Stage 5: Raw Session Candidate Generation

The cleaned transcript is converted into a raw-note candidate matching the rough style used in `Raw Session 7.md` and `Raw Session 8.md`: chronological scene/action notes, meaningful IC dialogue, stated character thoughts, checks/outcomes, GM revelations, and decisions. This is not another transcript-shaped cleanup artifact. Where possible, clear IC dialogue and thoughts should keep the character's actual wording instead of being paraphrased.

```bash
# Split into subagent-ready chunks
python3 scripts/transcription/generate_raw_notes.py prepare "Transcript Session XX.txt" ./notes_chunks \
    --chunk-size 100 \
    --overlap 12

# View the prompt template
python3 scripts/transcription/generate_raw_notes.py prompt

# (Process each chunk through LLM — see prompt template)
# Save results as notes_chunks/chunk_XXX_notes.txt

# Concatenate, apply name corrections, and clean seam artifacts into a review candidate
python3 scripts/transcription/generate_raw_notes.py concat ./notes_chunks "Raw Session XX Candidate.md"

# Reconcile chunk output into a scene-level review candidate
python3 scripts/transcription/reconcile_raw_notes.py \
  "Raw Session XX Candidate.md" \
  "Raw Session XX Reconciled Candidate.md" \
  --provider codex \
  --transcript "Transcript Session XX.txt" \
  --force

# After review, promote it to the approved raw notes
python3 scripts/transcription/validate_raw_notes.py "Raw Session XX Reconciled Candidate.md" --session XX --allow-review-lines
cp "Raw Session XX Reconciled Candidate.md" "Raw Session XX.md"
```

**Notes format:**
- Casual shorthand prose with `---` scene breaks
- Clear in-character dialogue preserved as `character: "quote"` with minimal paraphrase
- Stated character thoughts preserved as thoughts, preferably in the character's own words
- GM narration condensed into descriptions
- Dice rolls/checks noted inline
- No timestamps in output
- No low-impact OOC logistics or transcript-line formatting
- Chunk outputs must be reconciled before promotion to `Raw Session XX.md`
- Each chunk file contains:
  - `CONTEXT BEFORE`
  - `PRIMARY RANGE`
  - `CONTEXT AFTER`
- Subagents should write notes only for `PRIMARY RANGE`
- Remaining player chatter/meta should still be omitted even if it survives the OOC filter

The concat step applies canonical name corrections (e.g., `here's embrace` → `hýrda's embrace`, `heroterra` → `hieroterra`) and removes obvious seam artifacts automatically. `Nites` must remain `Nites`; do not convert it to `Nytes` or `Nýtes`.

### Stage 6: Polished Session Notes Generation

Once `Raw Session XX.md` exists, a second LLM pass can generate a polished `Session XX.md` in the style of the existing campaign notes.

```bash
python3 scripts/transcription/run_session_notes_agent.py \
    XX \
    "Raw Session XX.md" \
    "Session XX.md" \
    --provider codex
```

This stage is intended to match the existing `session-7.md` and `session-8.md` website-note format:
- markdown title with a session subtitle
- `Locales` and `Time`
- numbered sections
- cleaner narrative prose than the raw notes
- use `src/assets/sessions/session-7.md` and `src/assets/sessions/session-8.md` as the style guide for tone, structure, and level of detail

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

# Stage 4: OOC annotation cleanup
python3 scripts/transcription/filter_ooc.py prepare session-XX-diarized.txt ./ooc_chunks
#    Process each chunk through LLM into chunk_NN_annotations.jsonl
python3 scripts/transcription/filter_ooc.py apply \
  ./ooc_chunks/annotation_manifest.json \
  ./ooc_chunks \
  "Transcript Session XX - Annotation Cleaned Candidate.txt" \
  "Transcript Session XX - Annotation Cleanup Report.md" \
  "Transcript Session XX - Annotation Ambiguous Review.md" \
  "Transcript Session XX - Annotation Cleaned Candidate.diff"

# Stage 5: Raw session-note candidate
python3 scripts/transcription/generate_raw_notes.py prepare "Transcript Session XX.txt" ./notes_chunks
#    Process each chunk through LLM (model: gpt-5.2-codex)
python3 scripts/transcription/generate_raw_notes.py concat ./notes_chunks "Raw Session XX Candidate.md"
python3 scripts/transcription/reconcile_raw_notes.py \
  "Raw Session XX Candidate.md" \
  "Raw Session XX Reconciled Candidate.md" \
  --provider codex \
  --transcript "Transcript Session XX.txt" \
  --force

# Stage 6: Raw validation, polished notes, website sync, verification
python3 scripts/transcription/validate_raw_notes.py "Raw Session XX.md" --session XX
python3 scripts/transcription/run_session_notes_agent.py XX "Raw Session XX.md" "Session XX.md" --provider codex
python3 scripts/transcription/run_website_sync_agent.py --session XX --provider codex
npm run sync-check
```

---

## 📋 Entity Management

### Generate Entity List
To update `ENTITY_LIST.md` with the latest IDs and Names from the `src/store/*.js` files:

```bash
npm run generate-list
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
    - `filter_ooc.py`: Stage 4 — annotation-first OOC cleanup with deterministic apply/report/diff outputs.
    - `run_ooc_annotation_agents.py`: Stage 4 runner — dispatches OOC annotation chunks through Codex/Gemini and can apply results.
    - `generate_raw_notes.py`: Stage 5 — chunking, prompts, and concatenation for raw session-note candidates.
    - `reconcile_raw_notes.py`: Stage 5b — scene-level reconciliation before raw-note promotion.
    - `validate_raw_notes.py`: Raw-note quality gate before polished session generation.
    - `run_website_sync_agent.py`: Copies polished Ellara notes into website assets and dispatches store/view sync.
    - `validate_session_pipeline.py`: Cross-repo durable artifact validator.
    - `cleanup_session_artifacts.py`: Dry-run-first cleanup of intermediate session artifacts.
    - `speaker_map.json`: Mapping of usernames to Character names.
    - `name_corrections.json`: ASR mis-transcription → canonical name mappings.
    - `TRANSCRIPTION_GUIDE.md`: Detailed technical setup guide.
- `generate_entity_list.js`: Scans store files to build the master entity list.
- `verify_session_sync.js`: Website sync validator used by `npm run verify-session-sync`.

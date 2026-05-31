# Agent Session Pipeline

Use this file as the primary context for running a full session update from raw Craig-style speaker audio through website updates.

## Objective

Given a session number and a directory of speaker-isolated audio files, produce:

- normalized per-session transcript
- OOC-filtered transcript and ambiguous review file
- raw session notes
- polished session markdown
- website session asset
- updated website session index and world data
- verified production build

Do not stop when Ellara notes exist. The DnD website is updated only after the repo files under `src/` are updated and `npm run build` succeeds.

## Required Inputs

- Session number: `N`
- Audio directory with per-speaker files: `.flac`, `.aac`, `.mp3`, `.wav`, `.m4a`, or `.ogg`
- Current speaker mapping: `scripts/transcription/speaker_map.json`
- Local env file for Gladia if using Gladia: `.env.local`

The `.env.local` file is ignored by git. It should contain:

```bash
GLADIA_API_KEY=...
```

## Preferred Flow

Use the transcript checkpoint flow by default. It is more deterministic than asking an agent to clean transcript issues after raw notes already exist.

### 1. Prepare Canonical Terms

Run:

```bash
node scripts/generate_entity_list.js
```

Review `ENTITY_LIST.md` only if the campaign data stores recently changed.

### 2. Build Transcript And Stop

Whisper/local transcription:

```bash
python3 scripts/transcription/run_transcript_pipeline.py \
  --session N \
  --audio-dir "/path/to/session-audio" \
  --stop-after-transcript
```

Gladia/cloud transcription with local VAD compaction:

```bash
python3 scripts/transcription/run_transcript_pipeline.py \
  --session N \
  --audio-dir "/path/to/session-audio" \
  --transcription-provider gladia \
  --stop-after-transcript
```

This produces the review transcript:

```text
/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N.txt
```

It also copies the current normalized transcript to:

```text
src/assets/sessions/transcripts/session_N_raw.txt
```

### 2a. Optional Dual-Provider Baseline

Use this when the user asks to compare local Whisper against Gladia before choosing the transcript to review. Do not continue to raw notes until this comparison is complete and the user has selected a baseline.

Run Whisper first:

```bash
python3 scripts/transcription/run_transcript_pipeline.py \
  --session N \
  --audio-dir "/path/to/session-audio" \
  --transcription-provider whisper \
  --clean \
  --stop-after-transcript
```

Archive the normalized Whisper output:

```bash
cp "/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N.txt" \
  "/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N - Whisper Baseline.txt"
```

Run Gladia second:

```bash
python3 scripts/transcription/run_transcript_pipeline.py \
  --session N \
  --audio-dir "/path/to/session-audio" \
  --transcription-provider gladia \
  --clean \
  --stop-after-transcript
```

Archive the normalized Gladia output:

```bash
cp "/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N.txt" \
  "/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N - Gladia Baseline.txt"
```

Then compare the two transcripts directly and write the comparison report to:

```text
/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N - Provider Comparison.md
```

Read both baseline transcripts, `ENTITY_LIST.md`, `scripts/transcription/name_corrections.json`, and `scripts/transcription/speaker_map.json`.

Compare by timestamp windows rather than exact line numbers. Treat lines within roughly 3 seconds as candidates for the same moment. Focus on differences that matter for downstream notes:

- likely better baseline transcript: `Whisper`, `Gladia`, or `Mixed`
- interesting discrepancies where the providers heard materially different content
- missed lines or lines captured by only one provider
- recurring vocabulary/name wins and misses
- speaker-label differences
- repeated-line or timestamp pathologies
- long merged lines that span removed silence
- high-risk regions that need manual or audio review
- durable additions for `scripts/transcription/name_corrections.json`

The report should have these sections:

- `Recommendation`: which baseline should be the starting point and why
- `Provider Summary`: strengths, weaknesses, and major pathologies for each provider
- `Interesting Discrepancies`: timestamped content differences that may affect notes
- `Missed Or One-Sided Lines`: timestamped lines present in only one transcript
- `Vocabulary And Name Findings`: likely ASR misses and durable correction candidates
- `Speaker Attribution Findings`: likely speaker-label issues
- `Manual Review Windows`: timestamp ranges that need human attention

After comparison, stop and ask the user which baseline should become:

```text
/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N.txt
```

Only after the user chooses, copy that baseline to the canonical transcript path and proceed to the manual transcript review checkpoint.

### 3. Manual Transcript Review Checkpoint

Stop here for user review.

The user may:

- fix obvious ASR mistakes
- remove or shorten obvious OOC setup chatter
- repair speaker labels
- add missing names to `scripts/transcription/name_corrections.json`

Keep timestamps and the format:

```text
[HH:MM:SS] Speaker: text
```

Do not remove in-game uncertainty or table talk that may affect player intent. The next deterministic filter handles high-confidence OOC removal and writes an ambiguous review file.

### 4. Resume From Reviewed Transcript

After review, continue downstream without rebuilding the transcript:

```bash
python3 scripts/transcription/run_transcript_pipeline.py \
  --session N \
  --audio-dir "/path/to/session-audio" \
  --resume-after-transcript
```

Useful additions:

```bash
  --run-raw-notes-provider codex \
  --raw-notes-finalize \
  --run-session-notes-provider codex \
  --session-notes-force
```

On resume, the pipeline uses the reviewed Ellara transcript as source, copies it back to `src/assets/sessions/transcripts/session_N_raw.txt`, then runs:

- conservative OOC filter
- ambiguous-line report
- raw-note chunk preparation
- optional raw-note agents
- optional polished session-note generation
- manifest write

## OOC Handling

The deterministic pre-filter is:

```bash
scripts/transcription/filter_transcript_linewise.py
```

It removes only high-confidence OOC lines and writes:

```text
Transcript Session N - OOC Removed.txt
Transcript Session N - Ambiguous.txt
Transcript Session N - OOC Filter Report.txt
```

The manual checkpoint should be used for cleanup that is obvious to a human but too risky for regex, such as long setup/debug digressions. Do not depend on the LLM raw-note pass to remove all OOC chatter.

## Raw Notes

If not using the automatic provider flags, process chunks manually or through an agent:

```bash
python3 scripts/transcription/run_raw_notes_subagents.py \
  "/home/babu/source/ellara/Session Notes/Raw Session N Chunks/chunks_manifest.json" \
  --provider codex \
  --finalize
```

Expected output:

```text
/home/babu/source/ellara/Session Notes/Raw Session N.md
```

Then produce polished notes:

```bash
python3 scripts/transcription/run_session_notes_agent.py \
  N \
  "/home/babu/source/ellara/Session Notes/Raw Session N.md" \
  "/home/babu/source/ellara/Session Notes/Session N.md" \
  --provider codex \
  --workspace-root /home/babu/source \
  --force
```

Expected output:

```text
/home/babu/source/ellara/Session Notes/Session N.md
```

## Website Sync

Copy the polished note into the website session asset:

```bash
cp "/home/babu/source/ellara/Session Notes/Session N.md" \
  "src/assets/sessions/session-N.md"
```

Then apply the logic in:

```text
.copilot/prompts/process-latest-session.md
```

Required files to inspect:

- `src/assets/sessions/session-N.md`
- `src/store/sessions.js`
- `src/store/locations.js`
- `src/store/npcs.js`
- `src/store/lore.js`
- `ENTITY_LIST.md`

Required update policy:

- mark session `N` complete in `src/store/sessions.js`
- add `summaryFile: 'session-N.md'`
- add or update subtitle, description, and highlights
- create or verify upcoming session `N+1`
- add only significant history, connection, and entity updates
- do not create entities for incidental one-off mentions

Also review:

- `src/views/StorySoFarView.vue`
- `src/views/HomeView.vue`

Only update these views when the latest session changes the campaign state shown there.

After entity/store changes, regenerate:

```bash
node scripts/generate_entity_list.js
```

## Verification Gates

Run these before considering the job complete:

```bash
python3 -m json.tool scripts/transcription/name_corrections.json >/tmp/name_corrections.valid.json
node --check scripts/generate_entity_list.js
/home/babu/.gemini/tmp/transcribe_env/bin/python3 -m py_compile \
  scripts/transcription/run_transcript_pipeline.py \
  scripts/transcription/transcribe.py \
  scripts/transcription/transcribe_gladia.py \
  scripts/transcription/vad_compact.py
npm run build
```

Check expected artifacts:

- `src/assets/sessions/transcripts/session_N_raw.txt`
- `/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N.txt`
- `/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N - OOC Removed.txt`
- `/home/babu/source/ellara/Session Notes/Raw Session N.md`
- `/home/babu/source/ellara/Session Notes/Session N.md`
- `src/assets/sessions/session-N.md`
- `/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N - Pipeline Manifest.json`

## Determinism Notes

- Prefer `--stop-after-transcript` before downstream generation so transcript fixes happen once and feed every later artifact.
- Prefer `--resume-after-transcript` after user review; do not rerun transcription unless the audio or provider settings changed.
- Keep `name_corrections.json` as the durable ASR correction source. Do not hand-fix the same spelling issue in every transcript if it should be a reusable correction.
- For Gladia, audio is VAD-compacted before upload and remapped back to original timestamps before aggregation. The compact WAV intentionally keeps short silence gaps between retained VAD islands so cloud ASR has phrase boundaries.
- If Gladia returns no utterances for non-empty compact speech, `transcribe_gladia.py` retries once with less aggressive VAD settings. If Gladia merges words across removed silence, word-level timestamps are split after remapping so one line does not span minutes of missing audio.
- If Gladia returns too many tiny utterances, `transcribe_gladia.py` coalesces adjacent utterances after remapping to original time.
- If OOC filtering is too aggressive, use the ambiguous file and reviewed transcript rather than broadening regex removal rules blindly.

## One-Prompt Agent Instruction

When asking an agentic CLI to run everything, provide this file and say:

```text
Read AGENT_SESSION_PIPELINE.md. Run the DnD session pipeline for session N from /path/to/session-audio.
Use the transcript checkpoint flow. Stop after --stop-after-transcript and ask me to review the transcript.
After I confirm, resume with --resume-after-transcript, generate raw notes and polished notes, sync the website, apply .copilot/prompts/process-latest-session.md, and run verification.
```

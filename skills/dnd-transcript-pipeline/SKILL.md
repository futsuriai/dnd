---
name: dnd-transcript-pipeline
description: Run the end-to-end DnD transcript pipeline from speaker-isolated audio files to final transcript artifacts, then perform the required post-session repo sync: session summary asset, sessions index updates, world-data review, Story So Far refresh, and home-page blurb/current-state updates.
---

# Dnd Transcript Pipeline

Use the pipeline script at `scripts/transcription/run_transcript_pipeline.py`.

## Repo Roots

Assume:

- DnD repo root: the current repo
- Ellara repo root: sibling repo at `../ellara`

If needed, override with environment variables before running repo-local helper scripts:

- `DND_REPO_ROOT`
- `ELLARA_ROOT`

## Quick Start

From the DnD repo root:

```bash
python3 scripts/transcription/run_transcript_pipeline.py \
  --session 15 \
  --audio-dir /path/to/session-audio
```

Or use the repo-local wrapper:

```bash
skills/dnd-transcript-pipeline/scripts/run_pipeline.sh 15 /path/to/session-audio
```

## Inputs

- `--session`: Session label/number used for output file names.
- `--audio-dir`: Directory containing per-speaker audio files (`.aac`, `.flac`, `.mp3`, `.wav`, `.m4a`, `.ogg`).

## Canonical Character Pronouns

Apply this canon consistently in every note-generation pass: `chunk_XXX_notes.txt`, finalized `Raw Session <N>.md`, and polished `Session <N>.md`.

- Nyx: male, `he/him`
- Ellara: female, `she/her`
- Ysidor: male, `he/him`
- Berridin: male, `he/him`
- Witty / `Whitaker "Witty" Whitman VI`: male, `he/him`

If the transcript, voice, or an earlier draft uses the wrong pronoun for one of these characters, correct the notes to match the canon instead of carrying the mistake forward.

## Default Outputs

- Per-speaker transcripts copied to:
  `src/assets/sessions/transcripts/Session <N>/`
- Combined normalized transcript:
  `src/assets/sessions/transcripts/session_<N>_raw.txt`
- Ellara transcript:
  `../ellara/Session Notes/Transcripts/Transcript Session <N>.txt`
- OOC filtered variants:
  - `Transcript Session <N> - OOC Removed.txt`
  - `Transcript Session <N> - Ambiguous.txt`
  - `Transcript Session <N> - OOC Filter Report.txt`
- Raw-note chunk workspace:
  `../ellara/Session Notes/Raw Session <N> Chunks/`
- Final raw-session-note target:
  `../ellara/Session Notes/Raw Session <N>.md`
- Final polished session-note target:
  `../ellara/Session Notes/Session <N>.md`
- Manifest:
  `Transcript Session <N> - Pipeline Manifest.json`
- Website session summary asset target:
  `src/assets/sessions/session-<N>.md`

## Common Flags

- `--clean`: delete existing `*.ext.txt` per-speaker transcripts before transcribing.
- `--skip-transcribe`: reuse existing per-speaker transcript files.
- `--skip-ooc`: skip OOC/ambiguous output generation.
- `--skip-raw-notes-prep`: skip preparing raw-note chunk files.
- `--raw-notes-chunk-size`: primary transcript entries per raw-note chunk.
- `--raw-notes-overlap`: context entries before/after each raw-note chunk.
- `--run-raw-notes-provider`: dispatch raw-note chunks through `codex` or `gemini`.
- `--raw-notes-finalize`: concatenate chunk outputs into `Raw Session <N>.md`.
- `--raw-notes-dry-run`: print planned raw-note agent dispatches without running them.
- `--run-session-notes-provider`: dispatch polished session-note generation through `codex` or `gemini`.
- `--session-notes-force`: overwrite existing `Session <N>.md`.
- `--session-notes-dry-run`: print the planned polished session-note run without invoking the provider.
- `--keep-full-whitaker-name`: keep full speaker label instead of normalizing to `Witty`.
- `--attempt-models`: override retry model sequence.

## Workflow

1. Run `node scripts/generate_entity_list.js`.
2. Transcribe each speaker file with retry/fallback model sequence.
3. Combine transcripts in timestamp order.
4. Apply `name_corrections.json` text and speaker fixes.
5. Copy final artifacts into DnD and Ellara target locations.
6. Run `filter_transcript_linewise.py` for OOC removed and ambiguous outputs.
7. Run `generate_raw_notes.py prepare` to create chunk files with a primary range plus overlap context.
8. Optionally run `run_raw_notes_subagents.py` through `codex` or `gemini`.
9. `generate_raw_notes.py concat` performs seam cleanup automatically.
10. Optionally run `run_session_notes_agent.py` through `codex` or `gemini`.
11. Emit a manifest JSON with output paths and line counts.
12. Copy or sync the final polished note into `src/assets/sessions/session-<N>.md`.
13. Run the logic from `.copilot/prompts/process-latest-session.md` logically against the latest website session summary:
    - treat `src/assets/sessions/session-<N>.md` as the source summary
    - review `src/store/sessions.js`, `src/store/locations.js`, `src/store/npcs.js`, `src/store/lore.js`, and `ENTITY_LIST.md`
    - update session metadata for session `N`
    - create or verify the session `N+1` upcoming stub
    - add only significant history, connection, and entity updates
14. Refresh `src/views/StorySoFarView.vue` and `src/views/HomeView.vue`.
15. If entity/store changes were made, rerun `node scripts/generate_entity_list.js`.
16. Verify the site still builds with `npm run build`.

## End-to-End Path

1. Run `scripts/transcription/run_transcript_pipeline.py` on the audio directory.
2. Read `../ellara/Session Notes/Raw Session <N> Chunks/chunks_manifest.json`.
3. Produce every `chunk_XXX_notes.txt` from `chunk_XXX.txt`.
4. Finalize `Raw Session <N>.md`.
5. Generate polished `Session <N>.md`.
6. Sync `Session <N>.md` into `src/assets/sessions/session-<N>.md`.
7. Update `src/store/sessions.js` for session `N` and add or verify session `N+1`.
8. Review significant world-data changes using `.copilot/prompts/process-latest-session.md`.
9. Refresh Story So Far and the home-page blurb/current-state copy.
10. Build the site to verify nothing broke.

## Raw Notes Contract

After the main pipeline runs, read:
`../ellara/Session Notes/Raw Session <N> Chunks/chunks_manifest.json`

For each chunk:

- Read `chunk_XXX.txt`
- Use context sections only for continuity
- Write notes only for the `PRIMARY RANGE`
- Normalize the listed character pronouns to the canon above even if the transcript gets them wrong
- Save output as `chunk_XXX_notes.txt`

When all chunks are done, finalize with:
`skills/dnd-transcript-pipeline/scripts/finalize_raw_notes.sh`

To dispatch chunk work through an installed agent CLI, use:
`skills/dnd-transcript-pipeline/scripts/run_raw_notes_agents.sh`

To clean an already-generated raw file in place, use:
`skills/dnd-transcript-pipeline/scripts/clean_raw_notes.sh`

To generate polished `Session <N>.md` from `Raw Session <N>.md`, use:
`skills/dnd-transcript-pipeline/scripts/run_session_notes_agent.sh`

For the raw -> polished pass, use the existing files
`../ellara/Session Notes/Session 11.md`
through
`../ellara/Session Notes/Session 15.md`
as the style guide.

During the raw -> polished pass, preserve the canonical pronouns above even if the raw notes contain an earlier mistake.

## Post-Session Repo Sync

After transcript + notes generation, do not stop at the Ellara outputs. The DnD site reads session state from repo files, not from the transcript manifest alone.

Required follow-up:

1. Add or update the website session markdown asset:
   - Source: `../ellara/Session Notes/Session <N>.md`
   - Target: `src/assets/sessions/session-<N>.md`
2. Update `src/store/sessions.js`:
   - mark session `N` as `upcoming: false`
   - set `summaryFile: 'session-<N>.md'`
   - update subtitle, description, and highlights
   - create or verify session `N+1` as the top `upcoming: true` stub
3. Apply the world-data review from `.copilot/prompts/process-latest-session.md` logically:
   - only add entity/history/connection changes when the session caused a real canon change
   - do not create trivial entities for incidental tents, guards, or one-off scenery
   - prefer updating existing `history` arrays for places/NPCs like Hyrda, Meri, Ardwin, or the ducal encampment when the session materially changed their state
4. Update site copy surfaces outside the stores:
   - `src/views/StorySoFarView.vue`
   - `src/views/HomeView.vue`
5. Rebuild with `npm run build`.

## What The Site Actually Uses

- `src/assets/sessions/session-<N>.md` drives the latest session summary modal and is what `StorySoFarView.vue` scans to determine the latest completed session.
- `src/store/sessions.js` drives the home page cards, session list ordering, current quest, and upcoming-session state.
- `src/views/HomeView.vue` may contain hardcoded recap overrides for recent sessions.
- `src/views/StorySoFarView.vue` contains staged narrative text that often needs a new paragraph when the campaign meaningfully turns.

## Operational Notes

- The transcription stage may spend a long time on the first file if Whisper falls back to CPU. Check progress in `*.transcribe.log` or `*.txt.tmp`.
- The raw-notes and polished-notes provider stages require working `codex` or `gemini` CLI access. If they are unavailable, run transcript/OOC/chunk-prep first and resume later with `--skip-transcribe`.
- Do not assume the pipeline is done when `Session <N>.md` exists in Ellara. The website will not reflect the session until the DnD repo assets, views, and stores are updated.
- If there is no `src/assets/sessions/session-<N>.md`, the site can still behave as if an older session is latest even if `sessions.js` was updated.
- When a completed latest session is marked `upcoming: false`, also create the next upcoming session stub or the home page may show no next-session state.
- Reuse canonical IDs from the stores and `ENTITY_LIST.md` exactly, even when display names use corrected spelling.
- Keep chunk folders and transcript scratch output local-only via `.git/info/exclude` unless the repo intentionally starts tracking them.

## Verification

After a full run, verify:

- manifest exists
- chunk note count matches the manifest
- `Raw Session <N>.md` exists
- `Session <N>.md` exists
- `src/assets/sessions/session-<N>.md` exists
- site build succeeds

## Agent Prompt Template

For Claude/Codex/Gemini prompt text, use:
`references/portable-agent-prompt.md`

## Command Wrapper

Use:
`scripts/run_pipeline.sh`

---
name: dnd-transcript-pipeline
description: Run the end-to-end DnD transcript pipeline from speaker-isolated audio files to final transcript artifacts, then perform the required post-session repo sync: session summary asset, sessions index updates, world-data review, Story So Far refresh, and home-page blurb/current-state updates.
---

# Dnd Transcript Pipeline

Use `AGENT_SESSION_PIPELINE.md` as the full runbook for agentic end-to-end runs. Use the pipeline script at `scripts/transcription/run_transcript_pipeline.py`.

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
  --audio-dir /path/to/session-audio \
  --stop-after-transcript
```

Or use the repo-local wrapper:

```bash
skills/dnd-transcript-pipeline/scripts/run_pipeline.sh 15 /path/to/session-audio
```

## Inputs

- `--session`: Session label/number used for output file names.
- `--audio-dir`: Directory containing per-speaker audio files (`.aac`, `.flac`, `.mp3`, `.wav`, `.m4a`, `.ogg`).

## Canonical Character Pronouns

Apply this canon consistently in every note-generation pass: `chunk_XXX_notes.txt`, `Raw Session <N> Candidate.md`, finalized `Raw Session <N>.md`, and polished `Session <N>.md`.

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
- Chunk-extracted raw-session-note candidate target:
  `../ellara/Session Notes/Raw Session <N> Candidate.md`
- Reconciled raw-session-note candidate target:
  `../ellara/Session Notes/Raw Session <N> Reconciled Candidate.md`
- Approved raw-session-note target:
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
- `--stop-after-transcript`: write normalized transcript artifacts and stop for manual review.
- `--resume-after-transcript`: resume OOC filtering, raw notes, polished notes, and manifest generation from the reviewed Ellara transcript.
- `--transcription-provider`: choose `whisper` or `gladia`.
- `--gladia-artifact-dir`: directory for Gladia compact audio, manifests, and API JSON.
- `--skip-ooc`: skip OOC/ambiguous output generation.
- `--run-ooc-annotation-provider`: dispatch annotation-first OOC cleanup through `codex` or `gemini`.
- `--raw-notes-source-mode`: choose `canonical`, `annotation`, `legacy-ooc`, or `custom` as the raw-note source mode.
- `--skip-raw-notes-prep`: skip preparing raw-note chunk files.
- `--raw-notes-chunk-size`: primary transcript entries per raw-note chunk.
- `--raw-notes-overlap`: context entries before/after each raw-note chunk.
- `--run-raw-notes-provider`: dispatch raw-note chunks through `codex` or `gemini`.
- `--raw-notes-finalize`: concatenate chunk outputs into `Raw Session <N> Candidate.md`.
- `--raw-notes-output`: override the raw-note candidate output path.
- `--run-raw-notes-reconcile-provider`: reconcile chunk output through `codex` or `gemini`.
- `--raw-notes-reconciled-output`: override the reconciled raw-note candidate output path.
- `--raw-notes-dry-run`: print planned raw-note agent dispatches without running them.
- `--promote-raw-notes`: copy the reconciled raw candidate to canonical `Raw Session <N>.md`.
- `--run-session-notes-provider`: dispatch polished session-note generation through `codex` or `gemini`.
- `--session-notes-force`: overwrite existing `Session <N>.md`.
- `--session-notes-dry-run`: print the planned polished session-note run without invoking the provider.
- `--sync-website`: copy polished notes into `src/assets/sessions/session-<N>.md`.
- `--website-sync-provider`: dispatch website store/view sync through `codex` or `gemini`.
- `--cleanup-scratch`: remove intermediate artifacts after durable outputs are produced.
- `--validate`: run durable output validation and, when website markdown exists, npm website sync/build checks before finishing.
- `--keep-full-whitaker-name`: keep full speaker label instead of normalizing to `Witty`.
- `--attempt-models`: override retry model sequence.

## Workflow

1. Run `npm run generate-list`.
2. Transcribe each speaker file with retry/fallback model sequence, or Gladia VAD-compaction upload when `--transcription-provider gladia` is selected. The Gladia path keeps small phrase-boundary gaps in compact audio, retries once on empty non-empty results, and remaps/splits word timestamps back onto the original session timeline.
3. Combine transcripts in timestamp order.
4. Apply `name_corrections.json` text and speaker fixes.
5. Copy final artifacts into DnD and Ellara target locations.
6. If `--stop-after-transcript` is set, stop here for user transcript cleanup.
7. On `--resume-after-transcript`, copy the reviewed Ellara transcript back to the DnD raw transcript asset and continue.
8. Run `filter_transcript_linewise.py` for legacy OOC removed and ambiguous outputs.
9. Optionally run annotation-first OOC cleanup with `filter_ooc.py` plus `run_ooc_annotation_agents.py`.
10. Run `generate_raw_notes.py prepare` to create larger chunk files with a primary range plus overlap context.
11. Optionally run `run_raw_notes_subagents.py` through `codex` or `gemini`.
12. `generate_raw_notes.py concat` performs cleanup automatically into `Raw Session <N> Candidate.md`.
13. Run `reconcile_raw_notes.py` into `Raw Session <N> Reconciled Candidate.md`; this pass is required before promotion.
14. Validate and promote the reconciled candidate to `Raw Session <N>.md`.
15. Optionally run `run_session_notes_agent.py` through `codex` or `gemini`.
16. Sync the final polished note into `src/assets/sessions/session-<N>.md`.
17. Emit a manifest JSON with output paths and line counts.
18. Run the logic from `.copilot/prompts/process-latest-session.md` logically against the latest website session summary:
    - treat `src/assets/sessions/session-<N>.md` as the source summary
    - review `src/store/sessions.js`, `src/store/locations.js`, `src/store/npcs.js`, `src/store/lore.js`, and `ENTITY_LIST.md`
    - update session metadata for session `N`
    - create or verify the session `N+1` upcoming stub
    - add only significant history, connection, and entity updates
19. Refresh `src/views/StorySoFarView.vue` and `src/views/HomeView.vue`.
20. If entity/store changes were made, rerun `npm run generate-list`.
21. Verify with `python3 scripts/transcription/validate_session_pipeline.py --session <N>` and `npm run sync-check`.

## Dual-Provider Baseline

If the user asks to compare local Whisper and Gladia before choosing the review transcript:

1. Run the pipeline with `--transcription-provider whisper --clean --stop-after-transcript`.
2. Copy `../ellara/Session Notes/Transcripts/Transcript Session <N>.txt` to `Transcript Session <N> - Whisper Baseline.txt`.
3. Run the pipeline with `--transcription-provider gladia --clean --stop-after-transcript`.
4. Copy `../ellara/Session Notes/Transcripts/Transcript Session <N>.txt` to `Transcript Session <N> - Gladia Baseline.txt`.
5. Compare both baselines directly by timestamp windows, not exact line numbers.
6. Write `Transcript Session <N> - Provider Comparison.md` with recommendation, provider summary, interesting discrepancies, missed or one-sided lines, vocabulary/name findings, speaker attribution findings, and manual-review windows.
7. Stop and ask the user which baseline should become the canonical `Transcript Session <N>.txt`.

Do not create a separate prompt file for this. The comparison is part of the orchestration step before manual transcript cleanup.

## End-to-End Path

1. Run `scripts/transcription/run_transcript_pipeline.py` on the audio directory and stop for transcript review.
2. Run annotation-first OOC cleanup and show the cleaned transcript comparison.
3. After approval, generate raw-note chunks from the approved cleaned transcript.
4. Produce every `chunk_XXX_notes.txt` from `chunk_XXX.txt`.
5. Finalize `Raw Session <N> Candidate.md`.
6. Reconcile into `Raw Session <N> Reconciled Candidate.md`.
7. Validate, review, and promote it to `Raw Session <N>.md`.
8. Generate polished `Session <N>.md`.
9. Run `run_website_sync_agent.py` to sync `Session <N>.md` into `src/assets/sessions/session-<N>.md` and update stores/views.
10. Run `npm run sync-check` and `validate_session_pipeline.py`.
11. Dry-run and then apply `cleanup_session_artifacts.py` when the planned removals are correct.

## Raw Notes Contract

After the main pipeline runs, read:
`../ellara/Session Notes/Raw Session <N> Chunks/chunks_manifest.json`

For each chunk:

- Read `chunk_XXX.txt`
- Use context sections only for continuity
- Write notes only for the `PRIMARY RANGE`
- Preserve clear IC dialogue as `character: "quote"` with minimal paraphrase.
- Preserve stated character thoughts, preferably in the character's own words when clear.
- Normalize the listed character pronouns to the canon above even if the transcript gets them wrong
- Save output as `chunk_XXX_notes.txt`

When all chunks are done, finalize the chunk-extracted candidate with:
`skills/dnd-transcript-pipeline/scripts/finalize_raw_notes.sh`

Then reconcile the candidate with `scripts/transcription/reconcile_raw_notes.py`.

After review, validate and promote `Raw Session <N> Reconciled Candidate.md` to `Raw Session <N>.md`.

To dispatch chunk work through an installed agent CLI, use:
`skills/dnd-transcript-pipeline/scripts/run_raw_notes_agents.sh`

To clean an already-generated raw file in place, use:
`skills/dnd-transcript-pipeline/scripts/clean_raw_notes.sh`

To generate polished `Session <N>.md` from `Raw Session <N>.md`, use:
`skills/dnd-transcript-pipeline/scripts/run_session_notes_agent.sh`

For the raw -> polished pass, use `src/assets/sessions/session-7.md` and `src/assets/sessions/session-8.md` as the style guide.

During the raw -> polished pass, preserve the canonical pronouns above even if the raw notes contain an earlier mistake.

## Post-Session Repo Sync

After transcript + notes generation, do not stop at the Ellara outputs. The DnD site reads session state from repo files, not from the transcript manifest alone.

Required follow-up:

1. Run `python3 scripts/transcription/run_website_sync_agent.py --session <N> --provider codex` to copy the session markdown asset and dispatch the website-sync pass.
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
5. Run `npm run sync-check`.

## What The Site Actually Uses

- `src/assets/sessions/session-<N>.md` drives the latest session summary modal and is what `StorySoFarView.vue` scans to determine the latest completed session.
- `src/store/sessions.js` drives the home page cards, session list ordering, current quest, and upcoming-session state.
- `src/views/HomeView.vue` may contain hardcoded recap overrides for recent sessions.
- `src/views/StorySoFarView.vue` contains staged narrative text that often needs a new paragraph when the campaign meaningfully turns.
- `scripts/transcription/entity_metadata.json` is regenerated from `ENTITY_LIST.md` and feeds future ASR name prompts.
- `scripts/transcription/name_corrections.json` is the durable place for recurring ASR/name substitutions and pronunciation-like variants.

## Operational Notes

- The transcription stage may spend a long time on the first file if Whisper falls back to CPU. Check progress in `*.transcribe.log` or `*.txt.tmp`.
- The raw-notes and polished-notes provider stages require working `codex` or `gemini` CLI access. If they are unavailable, run transcript/OOC/chunk-prep first and resume later with `--skip-transcribe`.
- Do not assume the pipeline is done when `Session <N>.md` exists in Ellara. The website will not reflect the session until the DnD repo assets, views, and stores are updated.
- If there is no `src/assets/sessions/session-<N>.md`, the site can still behave as if an older session is latest even if `sessions.js` was updated.
- When a completed latest session is marked `upcoming: false`, also create the next upcoming session stub or the home page may show no next-session state.
- Reuse canonical IDs from the stores and `ENTITY_LIST.md` exactly, even when display names use corrected spelling.
- Inspect and update `src/views/HomeView.vue` every full latest-session sync when the latest session changes. Prefer a hardcoded recap override over generic extracted prose if extraction lowercases proper nouns or promotes an incidental detail.
- Inspect and update `src/views/StorySoFarView.vue` every full latest-session sync. Add a new staged paragraph when the latest session materially changes the back-cover campaign state.
- Canonical spelling check: use `Nites` exactly, pronounced knee-tes. Do not use `Nytes` or `Nýtes`.
- Before finishing, grep generated notes and website copy for known bad spellings, incorrect party-name capitalization, and wrong-name substitutions.
- Keep chunk folders and transcript scratch output local-only via `.git/info/exclude` unless the repo intentionally starts tracking them.
- Clean intermediate artifacts with `scripts/transcription/cleanup_session_artifacts.py` after showing a dry run.

## Verification

After a full run, verify:

- manifest exists
- chunk note count matches the manifest
- `Raw Session <N> Candidate.md` exists
- `Raw Session <N> Reconciled Candidate.md` exists
- approved `Raw Session <N>.md` exists
- `Session <N>.md` exists
- `src/assets/sessions/session-<N>.md` exists
- `npm run sync-check` succeeds
- `python3 scripts/transcription/validate_session_pipeline.py --session <N> --check-clean` succeeds or reports only expected scratch warnings before cleanup

## Agent Prompt Template

For Claude/Codex/Gemini prompt text, use:
`references/portable-agent-prompt.md`

## Command Wrapper

Use:
`scripts/run_pipeline.sh`

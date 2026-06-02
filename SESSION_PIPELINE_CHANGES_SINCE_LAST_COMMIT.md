# Session Pipeline Changes Since Last Commit

Baseline commit: `c0c74f2`

This document summarizes the working-tree changes made after the last commit to improve the flow from speaker-isolated audio files to mostly in-character website updates with an intermediate raw notes/dialogue artifact.

## What Changed

- Added deterministic final gates for website sync and cross-repo session artifacts.
- Added dry-run-first cleanup tooling for intermediate transcript/raw-note artifacts.
- Added an annotation-first OOC agent runner so the JSONL cleanup process is runnable from the pipeline instead of only documented manually.
- Added raw-note validation so transcript-shaped notes, unresolved review markers, bad name drift, and table-process language are caught before polished session notes.
- Changed raw-note extraction defaults from very small chunks to larger scene-oriented windows.
- Changed the main pipeline so it can continue from transcript review through OOC cleanup, raw-note extraction, reconciliation, promotion, polished notes, website sync, validation, and cleanup by explicit flags.
- Updated prompts and runbooks so the target artifact is a raw evidence ledger with IC dialogue/thoughts preserved, not a recap or cleaned transcript.

## New Scripts

- `scripts/transcription/run_ooc_annotation_agents.py`
  Dispatches `filter_ooc.py` annotation chunks through Codex or Gemini, writes `chunk_XX_annotations.jsonl`, and can apply the annotations into cleaned transcript/report/diff outputs.

- `scripts/transcription/validate_raw_notes.py`
  Validates `Raw Session N.md` before polished note generation. It rejects timestamps, chunk IDs, headings/code fences, unresolved `review:` lines, known bad name variants, table-process wording like `GM clarifies`, and low-quality recap leakage.

- `scripts/transcription/run_website_sync_agent.py`
  Copies polished Ellara notes into `src/assets/sessions/session-N.md` and optionally dispatches a website-update agent using `.copilot/prompts/process-latest-session.md`.

- `scripts/transcription/validate_session_pipeline.py`
  Checks durable outputs across the Ellara and DnD repos: canonical transcript, approved raw notes, polished notes, website markdown, session-store state, public spelling pitfalls, entity metadata, Home/Story coverage, and optional cleanup state.

- `scripts/transcription/cleanup_session_artifacts.py`
  Removes intermediate artifacts for one session after durable outputs are kept. It is dry-run by default and preserves the canonical transcript, raw notes, polished notes, website markdown, and pipeline manifest.

- `scripts/verify_session_sync.js`
  Website-specific verifier used by `npm run verify-session-sync`. It checks latest session markdown, `sessions.js`, upcoming stub state, Home/Story coverage, generated entity drift, public bad-name patterns, and current-session transcript leaks.

## Main Pipeline

`scripts/transcription/run_transcript_pipeline.py` now supports:

- `--run-ooc-annotation-provider`
- `--raw-notes-source-mode canonical|annotation|legacy-ooc|custom`
- larger raw-note defaults: chunk size `100`, overlap `12`
- `--promote-raw-notes`
- `--skip-raw-notes-validation`
- `--sync-website`
- `--website-sync-provider`
- `--cleanup-scratch`
- `--validate`

It also now:

- writes a manifest at the transcript checkpoint
- records annotation, website, validation, promotion, and cleanup outputs in the final manifest
- reconciles raw notes against the actual raw-note source instead of the unfiltered full transcript
- can run npm website verification/build as part of `--validate` when website markdown exists

## Prompt And Rule Updates

- Added shared `RAW_NOTE_CONTRACT` and `CANONICAL_EVIDENCE_POLICY` in `note_generation_guidance.py`.
- Updated raw-note chunk and reconciliation prompts to preserve meaningful IC dialogue/thoughts and avoid `GM says`/`GM clarifies` process phrasing.
- Updated OOC annotation guidance to treat opening recaps as removable unless they contain necessary continuity facts.
- Updated polished-note generation to validate raw notes by default before invoking an agent.
- Updated website-sync prompt to end autofix runs with entity-list generation, session sync verification, and build.

## Website Tooling

- Added npm scripts:
  - `npm run generate-list`
  - `npm run verify-session-sync`
  - `npm run sync-check`
- Narrowed `loadSessionMarkdown()` to load only `session-*.md` files from session assets.
- Updated raw imports in `markdownLoader.js` from deprecated `as: 'raw'` to `query: '?raw', import: 'default'`.

## Documentation Updated

- `AGENT_SESSION_PIPELINE.md`
- `scripts/README.md`
- `skills/dnd-transcript-pipeline/SKILL.md`
- `.copilot/prompts/process-latest-session.md`

The docs now describe the new staged flow:

1. audio to transcript checkpoint
2. annotation-first OOC cleanup and user comparison
3. raw-note candidate extraction
4. raw-note reconciliation
5. raw-note validation and promotion
6. polished session notes
7. website sync
8. verification
9. scratch cleanup after dry run

## Verification Run

Completed successfully:

- Python compile check for the changed transcription scripts
- `node --check scripts/verify_session_sync.js`
- `python3 scripts/transcription/run_website_sync_agent.py --session 17 --dry-run`
- `python3 scripts/transcription/cleanup_session_artifacts.py --session 17 --include-dnd-transcript-assets --include-repo-scratch`
- `python3 scripts/transcription/validate_session_pipeline.py --session 17`
- `npm run sync-check`

Known current-state signal:

- `validate_raw_notes.py` intentionally flags existing `Raw Session 17.md` in warn-only testing because that artifact predates the new stricter raw-note standard. It contains table-process phrasing, unresolved review lines, and a bad `Netus` variant. Future polished-note generation now blocks on those issues unless explicitly skipped.

Build note:

- The production build passes. It still emits existing Vue `::v-deep` deprecation warnings unrelated to this work.

## Changed Files

Modified:

- `.copilot/prompts/process-latest-session.md`
- `AGENT_SESSION_PIPELINE.md`
- `package.json`
- `scripts/README.md`
- `scripts/transcription/filter_ooc.py`
- `scripts/transcription/generate_raw_notes.py`
- `scripts/transcription/note_generation_guidance.py`
- `scripts/transcription/reconcile_raw_notes.py`
- `scripts/transcription/run_raw_notes_subagents.py`
- `scripts/transcription/run_session_notes_agent.py`
- `scripts/transcription/run_transcript_pipeline.py`
- `skills/dnd-transcript-pipeline/SKILL.md`
- `src/utils/markdownLoader.js`

Added:

- `scripts/transcription/cleanup_session_artifacts.py`
- `scripts/transcription/run_ooc_annotation_agents.py`
- `scripts/transcription/run_website_sync_agent.py`
- `scripts/transcription/validate_raw_notes.py`
- `scripts/transcription/validate_session_pipeline.py`
- `scripts/verify_session_sync.js`
- `SESSION_PIPELINE_CHANGES_SINCE_LAST_COMMIT.md`

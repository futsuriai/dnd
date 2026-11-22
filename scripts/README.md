# Scripts Directory

This directory contains the automated post-session pipeline, website verification tools, and entity-list generators for the DnD Campaign Wiki.

## Canonical Session Pipeline (`run_session_auto.py`)

For the full runbook, read [`AGENT_SESSION_PIPELINE.md`](../AGENT_SESSION_PIPELINE.md).

```bash
# End-to-end: speaker audio -> ASR -> Gemini 4 Neon arbitration -> fusion ->
# raw notes -> audit -> polished notes -> website sync -> ellara-state -> verify
python3 -B scripts/transcription/run_session_auto.py \
  --session N \
  --audio-dir /path/to/session-N

# Preview resolved paths, provider/model routing, and stage DAG without executing
python3 -B scripts/transcription/run_session_auto.py \
  --session N \
  --audio-dir /path/to/session-N \
  --dry-run
```

### Environment & Path Resolution
- `scripts/transcription/pipeline_paths.py` automatically resolves:
  - DnD root (`--dnd-dir` -> `$DND_REPO_ROOT` -> repo root)
  - Ellara vault root (`--ellara-root` -> `$ELLARA_ROOT` -> sibling `../ellara`)
  - Python venv (`--python` -> `.venv-transcription/bin/python3` -> `~/.gemini/tmp/transcribe_env/bin/python3` -> active `python3`)
- All pipeline invocations run with `PYTHONDONTWRITEBYTECODE=1` (`python3 -B`).
- Speaker filenames are mapped to character names in `scripts/transcription/speaker_map.json`.
- API keys and optional overrides live in git-ignored `.env.local` (see `.env.example`).

### Standalone Stage & Validation Commands

```bash
# Regenerate ENTITY_LIST.md + scripts/transcription/entity_metadata.json
npm run generate-list

# Full website check (generate-list + verify_session_sync.js + vite build)
npm run sync-check

# Generate polished Session N.md from Raw Session N.md (with raw + output validation)
python3 -B scripts/transcription/run_session_notes_agent.py N \
  "../ellara/Session Notes/Raw Session N.md" \
  "../ellara/Session Notes/Session N.md" \
  --provider agy --force

# Sync Session N.md -> website & update stores (with parity guard + sync-check)
python3 -B scripts/transcription/run_website_sync_agent.py --session N --provider agy

# Run Ellara Campaign State analysis + IC/OOC audit + deterministic validation
python3 -B scripts/transcription/run_ellara_analysis_agent.py --session N --provider agy

# Cross-repo durable output validation (reads scripts/shared_sync_rules.json + Ellara validator)
python3 -B scripts/transcription/validate_session_pipeline.py --session N --check-clean

# Dry-run cleanup of intermediate artifacts (add --apply to delete)
python3 -B scripts/transcription/cleanup_session_artifacts.py --session N --audio-dir /path/to/session-N
```

## Directory Layout

### Root (`scripts/`)
- `generate_entity_list.js`: Scans `src/store/*.js` to build `ENTITY_LIST.md` and `scripts/transcription/entity_metadata.json`.
- `verify_session_sync.js`: Website sync, store integrity, and shared canon-rule verifier (`npm run verify-session-sync`).
- `shared_sync_rules.json`: Single source of truth for bad public patterns and session-specific canon rules, shared by Python and JS validators.

### Active Pipeline (`scripts/transcription/`)
- `run_session_auto.py`: **Canonical** 14-stage unattended pipeline orchestrator (`entities -> asr -> gemini -> transcript -> dice -> fuse -> diagnostics -> raw-notes -> audit -> notes -> website -> ellara-state -> verify -> publish`).
- `pipeline_paths.py`: Portable path, venv Python, bytecode-suppression, and agent-invocation helpers.
- `agent_cli.py`: Shared CLI wrapper for `agy` (Gemini 4 Neon), `claude`, `codex`, and `gemini`.
- `run_asr_engines.py`, `vad_compact.py`, `transcribe_gladia.py`, `asr_whisper.py`, `asr_common.py`: Per-speaker VAD compaction and multi-engine ASR.
- `asr_gemini_windows.py`: Multimodal Gemini 4 Neon audio arbitration on disputed and one-sided speech segments.
- `assemble_transcript.py`, `ddb_rolls.py`, `fuse_transcript.py`, `asr_diagnostics.py`: Chronological assembly, D&D Beyond roll interleaving, multi-engine LLM fusion, and diagnostics.
- `name_normalizer.py`, `name_corrections.json`, `speaker_map.json`, `note_generation_guidance.py`: Campaign vocabulary, normalization, and canon prompt rules.
- `raw_notes_auto.py`, `audit_raw_notes.py`, `validate_raw_notes.py`: Scene-based raw note extraction, surgical IC/OOC audit, and validation.
- `run_session_notes_agent.py`, `session_facts.py`, `run_website_sync_agent.py`, `run_ellara_analysis_agent.py`: Downstream polished-notes, website-sync, and Ellara Campaign State agents.
- `validate_session_pipeline.py`, `cleanup_session_artifacts.py`: Cross-repo verification and intermediate artifact cleanup.
- `test_pipeline_orchestration.py`: Unit tests for orchestration, path portability, parity guards, validators, and Ellara state integration.

### Legacy Scripts (`scripts/transcription/`)
The following scripts belong to the older manual-checkpoint / Zoom+Whisper / 100-line chunking workflow and are kept only for backward reference (do not use for new sessions):
- `run_transcript_pipeline.py` *(legacy checkpointed orchestrator)*
- `transcribe.py`, `combine_transcripts.py`, `align_whisper_timestamps.py`, `merge_transcripts.py` *(legacy Zoom/Whisper helpers)*
- `filter_ooc.py`, `filter_transcript_linewise.py`, `run_ooc_annotation_agents.py` *(legacy OOC chunking)*
- `generate_raw_notes.py`, `run_raw_notes_subagents.py`, `reconcile_raw_notes.py` *(legacy 100-line raw-note chunking)*

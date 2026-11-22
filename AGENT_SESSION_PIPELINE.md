# Agent Session Pipeline

Speaker audio in, website and Ellara campaign state updated out, with no human checkpoints.

```bash
# Run from the DnD repo root (sibling ../ellara is auto-detected, or set ELLARA_ROOT / --ellara-root)
python3 -B scripts/transcription/run_session_auto.py \
  --session N \
  --audio-dir /path/to/session-N
```

That runs every stage below, records stage statuses (`done` / `skipped` / `failed`) in `<audio-dir>/pipeline/manifest.json`, and leaves both `ellara` and `dnd` changes uncommitted. Add `--publish` to preflight-check, explicitly stage session files, and commit both repos (plus `--push` to push). Rerunning the same command skips finished stages; add `--dry-run` to preview the resolved paths, providers, models, and stage DAG without executing anything.

## Paths & Local Setup (macOS / Linux Portable)

Path resolution is centralized in `scripts/transcription/pipeline_paths.py`:

- **DnD repo root:** auto-detected from script location (`--dnd-dir` or `$DND_REPO_ROOT` to override).
- **Ellara vault root:** `--ellara-root` -> `$ELLARA_ROOT` -> sibling `../ellara`.
- **Transcription Python venv:** `--python` -> `<dnd>/.venv-transcription/bin/python3` -> `~/.gemini/tmp/transcribe_env/bin/python3` -> active `python3`.
- **Bytecode hygiene:** all pipeline subprocesses run with `python3 -B` and `PYTHONDONTWRITEBYTECODE=1` so neither repo accumulates `__pycache__/`.

## Inputs

- One audio file per speaker (Craig export: `1-aurusoriale.flac`, `2-ellanelle.flac`, ...), mapped to characters in `scripts/transcription/speaker_map.json`.
- `dnd/.env.local` (git-ignored; see `.env.example`):

```bash
GLADIA_API_KEY=...
# optional overrides:
ELLARA_ROOT=...
AGY_MODEL=gemini-4-neon-medium
# optional, enables dice import from the D&D Beyond game log:
DDB_COBALT_SESSION=...
DDB_CAMPAIGN_ID=...
```

- Agent CLIs logged in with subscriptions:
  - **`agy`** (default, first-class): Gemini 4 Neon tiers (`gemini-4-neon-low`, `gemini-4-neon-medium`, `gemini-4-neon-high`, `gemini-4-neon-xhigh`) — used for multimodal audio arbitration, fusion, raw/polished notes, website sync, and Ellara campaign-state analysis.
  - **`claude`**: Claude Code CLI (`--provider claude`, or per-stage `--notes-provider` / `--website-provider` / `--ellara-provider` / `--fuse-provider`).
  - **`codex`**: Codex CLI (`--provider codex`).

## Stages

| stage | what it does | durable / operational output |
|---|---|---|
| `entities` | `npm run generate-list` (ASR vocabulary comes from `entity_metadata.json`) | `ENTITY_LIST.md`, `entity_metadata.json` |
| `asr` | each engine transcribes each track; silence is cut via VAD before upload | `<audio>/asr/<engine>/<track>.json` (+ raw Gladia JSON) |
| `gemini` | Gemini 4 Neon (`agy`, default `gemini-4-neon-medium`) arbitrates disputed & one-sided audio clips with candidate context & concurrent-speaker bleed checks | `<audio>/asr/gemini/` |
| `transcript` | assemble one chronological transcript from the primary engine and snapshot unfused pre-fuse baseline | `ellara/Session Notes/Transcripts/Transcript Session N.txt` + `.lines.jsonl` (+ `<audio>/pipeline/*.pre_fuse.*`) |
| `dice` | fetch D&D Beyond rolls, align to recording timeline, re-assemble with `DICE:` lines, refresh pre-fuse baseline | `<audio>/ddb/` |
| `fuse` | restores pre-fuse snapshot for idempotency; LLM judge picks/combines engine readings per line (with optional audio escalation) | `<audio>/pipeline/session_N_fusion_report.md` |
| `diagnostics` | compares engines (coverage, agreement, dice/entity metrics, loops; optional `--judge` audio check) | `<audio>/pipeline/session_N_asr_diagnostics.md` |
| `raw-notes` | scene plan + per-scene extraction in hand-written evidence style | `ellara/Session Notes/Raw Session N.md` |
| `audit` | per-scene LLM audit vs transcript (OOC leaks, missing beats, misattributions, game content in `ooc` scenes); patches scene files surgically in place and generates + re-audits any `ooc -> play` reclassified scenes | `<audio>/pipeline/session_N_raw_notes_audit.md` |
| `notes` | validates raw notes first, generates polished `Session N.md`, and runs post-generation structure/canon validation | `ellara/Session Notes/Session N.md` |
| `website` | derives played/next dates (`session_facts.py`), safely syncs `Session N.md` -> `src/assets/sessions/session-N.md` with parity protection, updates `src/store/sessions.js` (including `homeRecap`, `nextSteps`, `storyBeat`) and impacted world stores, runs `npm run sync-check` | `src/assets/sessions/session-N.md`, `src/store/*.js`, `<audio>/pipeline/session_facts.json` |
| `ellara-state` | runs `run_ellara_analysis_agent.py` against `ellara/.agents/skills/ellara-session-analysis`: updates `Ellara/Campaign State/`, runs clean-context IC/OOC & quote audit pass, validates with `check_session_delta.py --validate`, saves Prep Brief | `ellara/Ellara/Campaign State/*`, `<audio>/pipeline/ellara_prep_brief_session_N.md` |
| `verify` | hard gate running ALL validators: `validate_raw_notes.py`, `npm run sync-check`, `validate_session_pipeline.py`, and `check_session_delta.py --validate --session N` | manifest `verify` status (aborts on any failure) |
| `publish` | only with `--publish`: verifies `verify` passed, checks git repos, explicitly stages ONLY session outputs in `ellara` (notes + `Ellara/Campaign State/` + transcript) and `dnd`, commits cleanly (and pushes only with `--push`) | git commits |

### Useful Flags

- Stage selection: `--only STAGE`, `--from-stage STAGE`, `--stop-after STAGE`, `--force`, `--dry-run`, `--sandbox DIR`
- Provider & model routing (per-stage model overrides never leak across different providers):
  - `--provider agy|claude|codex|gemini`, `--model MODEL`
  - `--gemini off|disputed|all`, `--gemini-model MODEL` (default `gemini-4-neon-medium`)
  - `--fuse-provider`, `--fuse-model`, `--no-fuse`
  - `--notes-provider`, `--notes-model`, `--no-audit`
  - `--website-provider`, `--website-model`
  - `--ellara-provider`, `--ellara-model`, `--no-ellara`, `--no-ellara-audit`
- ASR & dates: `--engines`, `--primary`, `--judge`, `--session-date YYYY-MM-DD`, `--ellara-root PATH`, `--dnd-dir PATH`

## Standalone Stage Runners

Each post-transcript agent can also be run standalone (e.g., after hand-editing notes):

```bash
# Polished Session N.md from Raw Session N.md
python3 -B scripts/transcription/run_session_notes_agent.py N \
  "../ellara/Session Notes/Raw Session N.md" \
  "../ellara/Session Notes/Session N.md" \
  --provider agy --force

# Website store sync (bidirectional parity guard; pass --prefer ellara|dnd if files differ)
python3 -B scripts/transcription/run_website_sync_agent.py --session N --provider agy

# Ellara Campaign State update + IC/OOC audit + Prep Brief
python3 -B scripts/transcription/run_ellara_analysis_agent.py --session N --provider agy

# Cross-repo validation (reads scripts/shared_sync_rules.json + checks Ellara state)
python3 -B scripts/transcription/validate_session_pipeline.py --session N --check-clean
npm run sync-check
```

## Names, Canon & Shared Validation Rules

- `scripts/transcription/name_corrections.json`: tiered ASR name normalization (`text_fixes`, `capitalized_only_fixes` with sentence-start protection, `context_hints`, `aliases`).
- `scripts/shared_sync_rules.json`: single source of truth for forbidden public patterns and session-specific canon checks, shared by both Python (`validate_session_pipeline.py`, `validate_raw_notes.py`, `run_session_notes_agent.py`) and Node (`scripts/verify_session_sync.js`).
- Canon rules enforced across prompts and validators (`note_generation_guidance.py`):
  - Party pronouns: Nyx (`he/him`), Ellara (`she/her`), Ysidor (`he/him`), Berridin (`he/him`), Witty / Whitaker "Witty" Whitman VI (`he/him`).
  - `Nites` exactly (knee-tes), never `Nytes`/`Nýtes`; `Hýr` in prose, `Hyr` in stores; `Hýrda`.
  - Roll attribution: credit a roller only when the transcript or a `DICE:` line explicitly identifies them.
  - Website stores use `history` (never `updatedInSessions`), connections use `reason` (never `relationship`), and `sessions.js` carries `homeRecap`, `nextSteps`, and `storyBeat` directly (no manual `HomeView.vue` / `StorySoFarView.vue` edits).

## Report Hygiene & Cleanup

Operational debug reports (`session_N_fusion_report.md`, `session_N_asr_diagnostics.md`, `session_N_raw_notes_audit.md`, `ellara_prep_brief_session_N.md`, and `*.pre_fuse.*`) are written inside `<audio-dir>/pipeline/` rather than `ellara/Session Notes/`, so Ellara's GitHub Wiki publishing workflow never syncs debug reports.

```bash
python3 -B scripts/transcription/cleanup_session_artifacts.py --session N --audio-dir /path/to/session-N \
  --include-dnd-transcript-assets --include-repo-scratch   # dry run; add --apply
```

Cleanup deletes reproducible compact VAD audio and any leftover intermediate files while preserving `asr/` raw engine JSON, `ddb/`, `<audio-dir>/pipeline/`, durable notes, and `.lines.jsonl`.

## Legacy Checkpointed Flow

Older manual-checkpoint scripts (`run_transcript_pipeline.py`, `filter_ooc.py`, `generate_raw_notes.py`, `reconcile_raw_notes.py`, `run_raw_notes_subagents.py`, `run_ooc_annotation_agents.py`) remain in `scripts/transcription/` for reference only; `run_session_auto.py` is the canonical workflow.

---
name: dnd-transcript-pipeline
description: Run the end-to-end DnD session pipeline from per-speaker audio to polished notes, website store updates (sessions.js homeRecap/nextSteps/storyBeat, lore/locations/npcs), Ellara Campaign State analysis, and cross-repo verification.
---

# DnD Transcript & Session Pipeline

Use `AGENT_SESSION_PIPELINE.md` as the authoritative runbook. The canonical orchestrator is `scripts/transcription/run_session_auto.py` (with Gemini 4 Neon via `agy` as the default provider).

## Repo Roots & Portability

`scripts/transcription/pipeline_paths.py` auto-detects:
- **DnD repo root:** current repo (override via `--dnd-dir` or `$DND_REPO_ROOT`)
- **Ellara vault root:** sibling `../ellara` (override via `--ellara-root` or `$ELLARA_ROOT`)
- **Python venv:** `.venv-transcription/bin/python3` -> `~/.gemini/tmp/transcribe_env/bin/python3` -> active `python3`

Always pass `python3 -B` (or `PYTHONDONTWRITEBYTECODE=1`) so neither repo accumulates `__pycache__/`.

## Quick Start

From the DnD repo root:

```bash
# Full unattended run (entities -> asr -> gemini -> transcript -> dice -> fuse ->
# diagnostics -> raw-notes -> audit -> notes -> website -> ellara-state -> verify)
python3 -B scripts/transcription/run_session_auto.py \
  --session <N> \
  --audio-dir /path/to/session-<N>
```

Or use the repo-local wrapper (works from both `skills/` and `.agents/skills/`):

```bash
.agents/skills/dnd-transcript-pipeline/scripts/run_pipeline.sh <N> /path/to/session-<N>
```

Add `--dry-run` to inspect resolved paths, providers, models, and stages before running. Add `--publish` to preflight-check, explicitly stage session outputs in both repos, and commit (plus `--push` to push).

## Pipeline Stages

1. `entities`: `npm run generate-list` -> refreshes `ENTITY_LIST.md` & `entity_metadata.json`.
2. `asr`: per-speaker VAD compaction + ASR (`gladia,whisper-large-v3` by default).
3. `gemini`: Gemini 4 Neon (`agy`, default `gemini-4-neon-medium`) audio arbitration on disputed & one-sided clips.
4. `transcript`: chronological assembly + unfused pre-fuse baseline snapshot in `<audio-dir>/pipeline/`.
5. `dice`: optional D&D Beyond roll fetch/alignment (`DDB_COBALT_SESSION` + `DDB_CAMPAIGN_ID` in `.env.local`).
6. `fuse`: restores pre-fuse baseline for idempotency; LLM judge reconciles engine readings and writes report to `<audio-dir>/pipeline/`.
7. `diagnostics`: multi-engine diagnostics report in `<audio-dir>/pipeline/` (optional `--judge`).
8. `raw-notes`: scene-based extraction into `../ellara/Session Notes/Raw Session <N>.md`.
9. `audit`: per-scene IC/OOC & attribution audit patching scene files in place (report in `<audio-dir>/pipeline/`).
10. `notes`: validates raw notes, generates polished `../ellara/Session Notes/Session <N>.md`, and enforces post-generation structural/canon validation (`# Session <N>`, `**Locales:**`, `**Time:**`, `## 1)`, shared spelling/fact rules).
11. `website`: runs `session_facts.py` + `run_website_sync_agent.py` (parity guard, `MODE: autofix`, updates `src/store/sessions.js` including `homeRecap`/`nextSteps`/`storyBeat`, updates impacted stores using `history` + `reason:`, runs `npm run sync-check`).
12. `ellara-state`: runs `run_ellara_analysis_agent.py` against `../ellara/.agents/skills/ellara-session-analysis/` (updates `Ellara/Campaign State/`, runs clean-context IC/OOC & quote audit pass, validates with `check_session_delta.py --validate`, saves Prep Brief to `<audio-dir>/pipeline/`).
13. `verify`: hard gate requiring ALL validators to exit 0 (`validate_raw_notes.py`, `npm run sync-check`, `validate_session_pipeline.py`, and `check_session_delta.py --validate --session <N>`).
14. `publish`: only with `--publish`; requires `verify` `done`, stages explicit session file allowlists in both repos, and commits cleanly.

## Common Flags

- Stage control: `--only STAGE`, `--from-stage STAGE`, `--stop-after STAGE`, `--force`, `--dry-run`, `--sandbox DIR`
- Providers & models (per-stage overrides never leak across providers):
  - `--provider agy|claude|codex|gemini`, `--model MODEL`
  - `--gemini off|disputed|all`, `--gemini-model gemini-4-neon-medium`
  - `--fuse-provider`, `--fuse-model`, `--no-fuse`
  - `--notes-provider`, `--notes-model`, `--no-audit`
  - `--website-provider`, `--website-model`
  - `--ellara-provider`, `--ellara-model`, `--no-ellara`, `--no-ellara-audit`
- ASR & paths: `--engines`, `--primary`, `--whisper-offload auto|local|myne` (auto offloads Whisper to MYNE CUDA GPU from macOS when reachable), `--judge`, `--session-date YYYY-MM-DD`, `--ellara-root`, `--dnd-dir`

## Canonical Character Pronouns & Spelling

Apply consistently across raw notes, polished notes, website stores, and Ellara state:
- **Nyx:** male, `he/him`
- **Ellara:** female, `she/her`
- **Ysidor:** male, `he/him`
- **Berridin:** male, `he/him`
- **Witty / Whitaker "Witty" Whitman VI:** male, `he/him`

Canon spellings & rules (`scripts/shared_sync_rules.json` + `scripts/transcription/note_generation_guidance.py`):
- `Nites` exactly (pronounced knee-tes); never `Nytes` or `Nýtes`.
- `Hýr` in prose, `Hyr` in data stores; `Hýrda` for the village.
- Never treat PCs (`Nyx`, `Ellara`, `Ysidor`, `Berridin`, `Witty`/`Whitaker`, or former PC `Tsi'nyra`) as NPCs.
- Preserve roll attribution exactly; omit the roller rather than guessing if uncertain.
- Use `history` (never `updatedInSessions`) and `reason` (never `relationship`) in `src/store/*.js`.
- Populate `homeRecap`, `nextSteps`, and `storyBeat` directly on `src/store/sessions.js` (do not manually edit `HomeView.vue` or `StorySoFarView.vue`).

## Verification & Cleanup

```bash
# Cross-repo validation
npm run sync-check
python3 -B scripts/transcription/validate_session_pipeline.py --session <N> --check-clean

# Ellara Campaign State standalone validation
python3 -B ../ellara/.agents/skills/ellara-session-analysis/scripts/check_session_delta.py --validate --session <N>

# Dry-run artifact cleanup (add --apply to delete scratch/VAD audio)
python3 -B scripts/transcription/cleanup_session_artifacts.py --session <N> --audio-dir /path/to/session-<N>
```

## References & Wrapper

- Portable agent prompt: `references/portable-agent-prompt.md`
- Wrapper script: `scripts/run_pipeline.sh`
- Legacy fallback: `scripts/transcription/run_transcript_pipeline.py` (deprecated; kept for historical reference only).

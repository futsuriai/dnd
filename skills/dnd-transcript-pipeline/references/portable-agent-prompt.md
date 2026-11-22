Use this prompt with Antigravity (`agy`), Claude Code, or Codex when you want the full end-to-end session pipeline from per-speaker audio through polished notes, website store updates, Ellara Campaign State analysis, and cross-repo verification.

```text
Read AGENT_SESSION_PIPELINE.md first and follow it as the source of truth.

Run the unified DnD session pipeline for Session <SESSION> from audio directory:
<AUDIO_DIR>

1. Preview the resolved paths, providers, and stages first:
   python3 -B scripts/transcription/run_session_auto.py \
     --session <SESSION> \
     --audio-dir "<AUDIO_DIR>" \
     --dry-run

2. Run the full unattended pipeline (entities -> asr -> gemini -> transcript -> dice -> fuse -> diagnostics -> raw-notes -> audit -> notes -> website -> ellara-state -> verify):
   python3 -B scripts/transcription/run_session_auto.py \
     --session <SESSION> \
     --audio-dir "<AUDIO_DIR>"

   Optional flags:
   - Override sibling Ellara repo path: --ellara-root "<ELLARA_ROOT>"
   - Override providers/models: --provider agy|claude|codex, --gemini-model gemini-4-neon-medium, --notes-provider, --website-provider, --ellara-provider
   - Resume or target specific stages: --from-stage <STAGE>, --only <STAGE>, --stop-after <STAGE>
   - Free local ASR only: --engines whisper-large-v3 --primary whisper-large-v3
   - Commit both repos after `verify` passes: --publish (add --push only if explicitly requested)

Requirements:
- Do not rewrite pipeline orchestration manually; run `run_session_auto.py` and inspect `<AUDIO_DIR>/pipeline/manifest.json` and reports under `<AUDIO_DIR>/pipeline/`.
- Always invoke Python with `python3 -B` so neither `dnd` nor `ellara` accumulates `__pycache__/`.
- Preserve canonical character pronouns across raw notes, polished notes, website stores, and Ellara state:
  Nyx (he/him), Ellara (she/her), Ysidor (he/him), Berridin (he/him), Witty / Whitaker "Witty" Whitman VI (he/him).
- Preserve canonical spellings (`Nites` exact, `Hýr` in prose / `Hyr` in stores, `Hýrda`) and use `scripts/transcription/name_corrections.json` for durable ASR fixes.
- In `dnd/src/store/`: update `sessions.js` (`homeRecap`, `nextSteps`, `storyBeat`, and the `session-(N+1)` upcoming stub) plus impacted world stores using `history` (never `updatedInSessions`) and `reason:` connections (never `relationship:`). Do not manually edit `HomeView.vue` or `StorySoFarView.vue`.
- In `ellara/Ellara/Campaign State/`: enforce strict IC vs. OOC separation, verbatim quotes, exact check scopes, unique `.md` stems, and valid `[[WikiLinks]]`.
- Confirm all verification gates exit 0 (`validate_raw_notes.py`, `npm run sync-check`, `validate_session_pipeline.py --session <SESSION>`, and `check_session_delta.py --validate --session <SESSION>`).
- Report the summary of outputs, the Ellara Prep Brief path (`<AUDIO_DIR>/pipeline/ellara_prep_brief_session_<SESSION>.md`), and any dry-run cleanup candidates from `cleanup_session_artifacts.py`.
```

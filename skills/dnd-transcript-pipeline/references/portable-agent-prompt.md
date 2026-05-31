Use this with Codex, Claude Code, or Gemini CLI when you want transcript generation, raw-session-note generation, polished session-note generation, and DnD website sync.

```text
Read AGENT_SESSION_PIPELINE.md first and follow it as the source of truth.

Run the DnD session pipeline for session <SESSION> from audio directory:
<AUDIO_DIR>

Use the checkpoint workflow:
1. From the DnD repo root, run transcription only and stop:
   python3 scripts/transcription/run_transcript_pipeline.py \
     --session <SESSION> \
     --audio-dir <AUDIO_DIR> \
     --stop-after-transcript

   If Gladia should be used instead of local Whisper, add:
     --transcription-provider gladia

   If asked to compare providers first, run both stop-after-transcript paths before manual cleanup:
     a. Run with --transcription-provider whisper --clean --stop-after-transcript.
     b. Copy the resulting Ellara transcript to:
        /home/babu/source/ellara/Session Notes/Transcripts/Transcript Session <SESSION> - Whisper Baseline.txt
     c. Run with --transcription-provider gladia --clean --stop-after-transcript.
     d. Copy the resulting Ellara transcript to:
        /home/babu/source/ellara/Session Notes/Transcripts/Transcript Session <SESSION> - Gladia Baseline.txt
     e. Compare the two baselines directly by timestamp windows, looking for interesting discrepancies, missed lines, speaker-label differences, repeated-line/timestamp pathologies, vocabulary/name misses, and high-risk manual-review windows. Write:
        /home/babu/source/ellara/Session Notes/Transcripts/Transcript Session <SESSION> - Provider Comparison.md
     f. Stop and ask which baseline should become the canonical review transcript.

2. Report the transcript path and stop for user review:
   /home/babu/source/ellara/Session Notes/Transcripts/Transcript Session <SESSION>.txt

3. After the user confirms transcript cleanup is complete, resume without retranscribing:
   python3 scripts/transcription/run_transcript_pipeline.py \
     --session <SESSION> \
     --audio-dir <AUDIO_DIR> \
     --resume-after-transcript \
     --run-raw-notes-provider codex \
     --raw-notes-finalize \
     --run-session-notes-provider codex \
     --session-notes-force

Requirements:
- Do not rewrite pipeline logic manually.
- Wait for long-running transcription/provider jobs to finish.
- Preserve timestamps and speaker labels in transcript review.
- Use `scripts/transcription/name_corrections.json` for durable ASR fixes, not one-off repeated transcript edits.
- Use only `PRIMARY RANGE` when producing raw-note chunk outputs; context is for continuity only.
- Normalize character pronouns to canon in both the raw and polished notes:
  Nyx he/him, Ellara she/her, Ysidor he/him, Berridin he/him, Witty/Whitaker he/him.
- If the transcript, voice, or a draft note conflicts with that canon, fix the pronouns in the notes instead of preserving the error.
- Sync `/home/babu/source/ellara/Session Notes/Session <SESSION>.md` to `src/assets/sessions/session-<SESSION>.md`.
- Apply `.copilot/prompts/process-latest-session.md` against that session summary.
- Update `src/store/sessions.js`, significant world data, `src/views/StorySoFarView.vue`, and `src/views/HomeView.vue` only where warranted by the session.
- Regenerate `ENTITY_LIST.md` if store/entity data changed.
- Finish with the verification gates from AGENT_SESSION_PIPELINE.md, including `npm run build`.

If per-speaker transcripts already exist and the user explicitly wants to reuse them, use:
  --skip-transcribe

If raw notes need manual chunk processing instead of provider dispatch, read:
  /home/babu/source/ellara/Session Notes/Raw Session <SESSION> Chunks/chunks_manifest.json
and write each `chunk_XXX_notes.txt`, then run:
  skills/dnd-transcript-pipeline/scripts/finalize_raw_notes.sh <SESSION>
```
```

Use this with Codex, Claude Code, or Gemini CLI when you want transcript generation, raw-session-note generation, polished session-note generation, and the DnD repo sync steps.

```text
Run the DnD transcript pipeline for session <SESSION>.

Command from the DnD repo root:
python3 scripts/transcription/run_transcript_pipeline.py \
  --session <SESSION> \
  --audio-dir <AUDIO_DIR>

Requirements:
- Do not rewrite the pipeline manually.
- Wait for long-running transcription to finish.
- If transcription fails for one speaker, retry with the built-in fallback sequence.
- Report the final output file paths from the manifest file:
  ../ellara/Session Notes/Transcripts/Transcript Session <SESSION> - Pipeline Manifest.json
- After the main pipeline runs, read:
  ../ellara/Session Notes/Raw Session <SESSION> Chunks/chunks_manifest.json
- Process each `chunk_XXX.txt` into `chunk_XXX_notes.txt`.
- Use only the `PRIMARY RANGE` for output; use surrounding context only for continuity.
- Normalize character pronouns to canon in both the raw and polished notes:
  Nyx he/him, Ellara she/her, Ysidor he/him, Berridin he/him, Witty/Whitaker he/him.
- If the transcript, voice, or a draft note conflicts with that canon, fix the pronouns in the notes instead of preserving the error.
- When all chunks are complete, run:
  skills/dnd-transcript-pipeline/scripts/finalize_raw_notes.sh <SESSION>
- If a raw-session file already exists but has seam artifacts, run:
  skills/dnd-transcript-pipeline/scripts/clean_raw_notes.sh <SESSION>
- To produce polished markdown notes after raw notes are ready, run:
  skills/dnd-transcript-pipeline/scripts/run_session_notes_agent.sh <SESSION> codex --force
- Use `../ellara/Session Notes/Session 11.md` through `Session 15.md` as the formatting guide for the raw -> polished pass.
- Then sync `../ellara/Session Notes/Session <SESSION>.md` into `src/assets/sessions/session-<SESSION>.md`.
- Apply the logic from `.copilot/prompts/process-latest-session.md` logically against the new session summary.
- Update `src/store/sessions.js`, significant world data, `src/views/StorySoFarView.vue`, and `src/views/HomeView.vue`.
- Finish by running `npm run build`.

You can automate the chunk loop with:
skills/dnd-transcript-pipeline/scripts/run_raw_notes_agents.sh <SESSION> codex --finalize

Or with Gemini:
skills/dnd-transcript-pipeline/scripts/run_raw_notes_agents.sh <SESSION> gemini --finalize

If per-speaker transcripts already exist and should be reused, append:
--skip-transcribe
```

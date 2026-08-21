# Agent Session Pipeline

Use this file as the primary context for running a full session update from raw Craig-style speaker audio through website updates.

## Objective

Given a session number and a directory of speaker-isolated audio files, produce:

- normalized per-session transcript
- annotation-cleaned transcript candidate and review artifacts
- legacy OOC-filtered transcript and ambiguous review file
- raw session-note candidate
- approved raw session notes
- polished session markdown
- website session asset
- updated website session index and world data
- verified production build

Do not stop when Ellara notes exist. The DnD website is updated only after the repo files under `src/` are updated and `npm run build` succeeds.

## Required Inputs

- Session number: `N`
- Audio directory with per-speaker files: `.flac`, `.aac`, `.mp3`, `.wav`, `.m4a`, or `.ogg`
- Current speaker mapping: `scripts/transcription/speaker_map.json`
- Local env file for default Gladia/cloud transcription: `.env.local`

The `.env.local` file is ignored by git. It should contain:

```bash
GLADIA_API_KEY=...
```

## Preferred Flow

Use the transcript checkpoint flow by default. Gladia/cloud transcription is the default ASR path; use local Whisper only when the user explicitly asks for a local fallback or a dual-provider comparison. The checkpoint flow is more deterministic than asking an agent to clean transcript issues after raw notes already exist.

### 1. Prepare Canonical Terms

Run:

```bash
npm run generate-list
```

Review `ENTITY_LIST.md` only if the campaign data stores recently changed.

### 2. Build Transcript And Stop

Default Gladia/cloud transcription with local VAD compaction:

```bash
python3 scripts/transcription/run_transcript_pipeline.py \
  --session N \
  --audio-dir "/path/to/session-audio" \
  --stop-after-transcript
```

Explicit Whisper/local fallback:

```bash
python3 scripts/transcription/run_transcript_pipeline.py \
  --session N \
  --audio-dir "/path/to/session-audio" \
  --transcription-provider whisper \
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

### 2b.1 Optional Comparison-Informed Merge

Use this after the user chooses a baseline from the dual-provider comparison. The goal is not to blend both transcripts wholesale. Start from the selected baseline and copy in only clearly better fragments from the other provider when the comparison report identifies a concrete gain.

Good candidates:

- the selected baseline has a hallucination, prompt echo, repeated-character pathology, or obvious ASR substitution
- the other provider has the same timestamp window with clearer campaign nouns, names, or rules terms
- the replacement preserves the same timestamp and speaker, or can be trimmed without inventing content

Bad candidates:

- speculative rewrites
- changes that alter player intent
- replacing a whole scene just because the other provider has different wording
- removing table uncertainty that explains a choice

Write these review artifacts:

```text
/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N - Provider Merge Candidate.txt
/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N - Provider Merge Report.md
/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N - Provider Merge.diff
```

If there are no useful fragments to salvage from the other provider, say so in the merge report and copy the chosen baseline unchanged to the merge candidate.

After approval, copy the merge candidate to:

```text
/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N.txt
```

### 3. OOC Cleanup Review Checkpoint

Before downstream notes, run the chosen or merged transcript through the annotation-first OOC cleanup process. This produces one transcript artifact for audit and review:

- an audit-friendly cleaned transcript, for transcript review and canonical replacement

The annotation-first flow is the default. Do not use a freeform LLM transcript rewrite for OOC cleanup; the LLM should emit JSONL annotations and `scripts/transcription/filter_ooc.py` should apply them deterministically.

Expected review artifacts:

```text
/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N - Annotation Cleaned Candidate.txt
/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N - Annotation Cleanup Report.md
/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N - Annotation Ambiguous Review.md
/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N - Annotation Cleaned Candidate.diff
```

Runnable orchestration:

```bash
python3 scripts/transcription/run_transcript_pipeline.py \
  --session N \
  --audio-dir "/path/to/session-audio" \
  --resume-after-transcript \
  --run-ooc-annotation-provider codex \
  --raw-notes-source-mode annotation \
  --skip-raw-notes-prep
```

This prepares annotation chunks, runs clean-context annotation agents, applies `filter_ooc.py`, and stops before raw-note generation. Show the user the VS Code comparison between `Transcript Session N.txt` and `Transcript Session N - Annotation Cleaned Candidate.txt` before approving it.

After approval, copy the cleaned candidate to:

```text
/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N.txt
```

Raw-note generation is a separate stage. It should convert the approved cleaned transcript into a rough chronological raw-note candidate, not another transcript-shaped file.

### 4. Manual Transcript Review Checkpoint

Stop here for user review.

The user may:

- review the provider merge and annotation-cleaned diffs
- fix remaining obvious ASR mistakes
- remove or shorten any obvious OOC setup chatter missed by the cleanup pass
- repair speaker labels
- add missing names to `scripts/transcription/name_corrections.json`

Keep timestamps and the format:

```text
[HH:MM:SS] Speaker: text
```

Do not remove in-game uncertainty or table talk that may affect player intent. The next deterministic filter still handles high-confidence OOC removal and writes an ambiguous review file, but the reviewed transcript should already have obvious setup chatter removed.

### 5. Raw Session Candidate Extraction

Generate a rough raw-session-note candidate from the approved cleaned transcript. This is the interstitial artifact that should resemble `Raw Session 7.md` and `Raw Session 8.md`: chronological notes, scene/action beats, meaningful IC dialogue, stated character thoughts, checks and outcomes, GM revelations, resource state, and open hooks. It should not preserve timestamped speaker-line transcript shape.

Where possible, preserve IC dialogue and stated thoughts in the character's own wording. The raw artifact should compress logistics, repeated planning loops, and OOC chatter, but it should not paraphrase away clear character speech just to make the notes smoother.

Use clean subagents for this step when possible. Each chunk agent should receive only the chunk, adjacent context, entity references, and the raw-note instructions, so it is not biased by the prior cleanup conversation.

Prepare chunks:

```bash
python3 scripts/transcription/generate_raw_notes.py prepare \
  "/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N.txt" \
  "/home/babu/source/ellara/Session Notes/Raw Session N Chunks" \
  --chunk-size 100 \
  --overlap 12
```

Run chunk agents and finalize to a chunk-extracted candidate file:

```bash
python3 scripts/transcription/run_raw_notes_subagents.py \
  "/home/babu/source/ellara/Session Notes/Raw Session N Chunks/chunks_manifest.json" \
  --provider codex \
  --workspace-root /home/babu/source \
  --finalize \
  --output-file "/home/babu/source/ellara/Session Notes/Raw Session N Candidate.md"
```

Expected output:

```text
/home/babu/source/ellara/Session Notes/Raw Session N Candidate.md
```

### 6. Raw Session Reconciliation

The chunk-extracted candidate is not promotable by itself. It must go through a scene-level reconciliation pass before becoming the approved raw artifact. Fixed chunks are useful for local fidelity and quote capture, but they are too local to make final decisions about repeated planning loops, scene boundaries, cross-scene continuity, and what belongs in the final raw notes.

Run:

```bash
python3 scripts/transcription/reconcile_raw_notes.py \
  "/home/babu/source/ellara/Session Notes/Raw Session N Candidate.md" \
  "/home/babu/source/ellara/Session Notes/Raw Session N Reconciled Candidate.md" \
  --provider codex \
  --workspace-root /home/babu/source \
  --transcript "/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N.txt" \
  --force
```

Expected output:

```text
/home/babu/source/ellara/Session Notes/Raw Session N Reconciled Candidate.md
```

Review the reconciled candidate against the goal:

- remove transcript timestamps and transcript-line formatting
- keep chronological scene/action beats separated with `---`
- preserve meaningful IC dialogue and stated character thoughts, especially direct wording when clear
- preserve player intent and tactical planning when it affects action or outcomes
- preserve GM instructions, rulings, lore, descriptions, revelations, checks, and outcomes
- merge duplicated overlap from adjacent chunks
- compress repeated planning loops into final options, choices, and outcomes
- compress recap/setup chatter into only continuity facts needed for this session
- drop OOC logistics and low-impact process chatter
- keep uncertainty when the table uncertainty affected a choice

After approval, copy the reconciled candidate to the canonical raw notes:

```bash
cp "/home/babu/source/ellara/Session Notes/Raw Session N Reconciled Candidate.md" \
  "/home/babu/source/ellara/Session Notes/Raw Session N.md"
```

Before polished-note generation, validate the approved raw artifact:

```bash
python3 scripts/transcription/validate_raw_notes.py \
  "/home/babu/source/ellara/Session Notes/Raw Session N.md" \
  --session N
```

### 7. Final Session Notes

Generate the polished session markdown only after `Raw Session N.md` has been reviewed and approved:

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

The final file should follow the style of `src/assets/sessions/session-7.md` and `src/assets/sessions/session-8.md`: title, `Locales`, `Time`, numbered story sections, and `Where We Stand` / `Next Steps` sections when useful. It should read as mostly in-character story summary with GM discoveries and consequences folded in.

### 8. Resume From Reviewed Transcript

After transcript review, continue downstream without rebuilding the transcript:

```bash
python3 scripts/transcription/run_transcript_pipeline.py \
  --session N \
  --audio-dir "/path/to/session-audio" \
  --resume-after-transcript
```

Useful additions for generating the raw candidate:

```bash
  --run-raw-notes-provider codex \
  --raw-notes-finalize \
  --run-raw-notes-reconcile-provider codex \
  --raw-notes-source-mode canonical
```

On resume, the pipeline uses the reviewed Ellara transcript as source and copies it back to `src/assets/sessions/transcripts/session_N_raw.txt`. Raw-note chunk preparation uses `--raw-notes-source-mode canonical` by default; use `annotation` for an annotation-cleaned candidate, `legacy-ooc` only for the old linewise output, or `--raw-notes-source` for an explicit custom path. Use `--raw-notes-output` to name the candidate explicitly:

```bash
python3 scripts/transcription/run_transcript_pipeline.py \
  --session N \
  --audio-dir "/path/to/session-audio" \
  --resume-after-transcript \
  --raw-notes-source-mode canonical \
  --run-raw-notes-provider codex \
  --raw-notes-finalize \
  --raw-notes-output "/home/babu/source/ellara/Session Notes/Raw Session N Candidate.md" \
  --run-raw-notes-reconcile-provider codex \
  --raw-notes-reconciled-output "/home/babu/source/ellara/Session Notes/Raw Session N Reconciled Candidate.md"
```

Do not use `--run-session-notes-provider` until after the reconciled raw candidate has been reviewed and copied to `Raw Session N.md`.

For a user-approved one-pass continuation after raw review, use explicit promotion:

```bash
python3 scripts/transcription/run_transcript_pipeline.py \
  --session N \
  --audio-dir "/path/to/session-audio" \
  --resume-after-transcript \
  --promote-raw-notes \
  --run-session-notes-provider codex \
  --session-notes-force \
  --sync-website \
  --website-sync-provider codex \
  --validate
```

On resume, the pipeline runs:

- legacy conservative OOC filter and ambiguous-line report
- optional annotation-first OOC cleanup
- raw-note chunk preparation
- optional raw-note agents to `Raw Session N Candidate.md`
- optional raw-note reconciliation to `Raw Session N Reconciled Candidate.md`
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

Classify banter by fictional context, not by casual tone or speaker identity.
Preserve IC jokes, teasing, reactions, scene descriptions, and small character
beats even when they are not plot-critical. Remove banter only when it is
clearly about real-world topics, players' lives, or session/recording logistics.
When context cannot distinguish IC speech from OOC chatter, keep it in the
candidate as `REVIEW` rather than deleting it.

For sessions with substantial table chatter, use the annotation-first OOC review pass before accepting the final reviewed transcript. This pass produces a cleaned candidate transcript, reports, and a diff before replacing the canonical transcript.

Prepare annotation chunks from the chosen transcript or provider-merge candidate:

```bash
python3 scripts/transcription/filter_ooc.py prepare \
  "/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N - Provider Merge Candidate.txt" \
  "/home/babu/source/ellara/Session Notes/Transcripts/Session N OOC Annotation Chunks" \
  --chunk-size 80 \
  --overlap-lines 8
```

If there is no provider-merge candidate, use:

```bash
python3 scripts/transcription/filter_ooc.py prepare \
  "/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N.txt" \
  "/home/babu/source/ellara/Session Notes/Transcripts/Session N OOC Annotation Chunks" \
  --chunk-size 80 \
  --overlap-lines 8
```

For each chunk, print the prompt and ask the agent/LLM to write JSONL annotations:

```bash
python3 scripts/transcription/filter_ooc.py prompt \
  --chunk-file "/home/babu/source/ellara/Session Notes/Transcripts/Session N OOC Annotation Chunks/chunk_00.txt"
```

Save the output beside the chunk:

```text
chunk_XX_annotations.jsonl
```

Each annotation file must contain one JSON object per editable line. The schema is:

```json
{
  "line_id": "L000001",
  "action": "KEEP | REMOVE | TRIM | REVIEW",
  "category": "IC_DIALOGUE | GM_NARRATION | SCENE_DESCRIPTION | CHARACTER_THOUGHT | PLAYER_INTENT | TACTICS | RULES_OR_ROLL | RESOURCE_STATE | LORE_OR_CONTINUITY | RECAP_CONTINUITY | RECAP_REDUNDANT | OOC_TECH | OOC_LOGISTICS | OOC_SOCIAL | OOC_TANGENT | MIXED | UNCERTAIN",
  "importance": "HIGH | MEDIUM | LOW | NONE",
  "replacement": null,
  "reason": "short reason"
}
```

The LLM may use context lines but must emit records only for editable lines. `replacement` must be post-colon text only; the script preserves timestamps and speakers.

Then apply the annotations:

```bash
python3 scripts/transcription/filter_ooc.py apply \
  "/home/babu/source/ellara/Session Notes/Transcripts/Session N OOC Annotation Chunks/annotation_manifest.json" \
  "/home/babu/source/ellara/Session Notes/Transcripts/Session N OOC Annotation Chunks" \
  "/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N - Annotation Cleaned Candidate.txt" \
  "/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N - Annotation Cleanup Report.md" \
  "/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N - Annotation Ambiguous Review.md" \
  "/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N - Annotation Cleaned Candidate.diff"
```

Or dispatch and apply through the orchestration helper:

```bash
python3 scripts/transcription/run_ooc_annotation_agents.py \
  "/home/babu/source/ellara/Session Notes/Transcripts/Session N OOC Annotation Chunks/annotation_manifest.json" \
  --provider codex \
  --workspace-root /home/babu/source \
  --apply
```

Review with a side-by-side comparison:

```bash
code --diff \
  "/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N - Provider Merge Candidate.txt" \
  "/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N - Annotation Cleaned Candidate.txt"
```

If there is no provider-merge candidate, compare against `Transcript Session N.txt`.

Only after approval, copy the cleaned candidate back to:

```text
/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N.txt
```

Then generate the raw-note candidate from the approved cleaned transcript, either with the commands in `Raw Session Candidate Extraction` or by resuming:

```bash
python3 scripts/transcription/run_transcript_pipeline.py \
  --session N \
  --audio-dir "/path/to/session-audio" \
  --resume-after-transcript \
  --raw-notes-source-mode canonical \
  --run-raw-notes-provider codex \
  --raw-notes-finalize \
  --raw-notes-output "/home/babu/source/ellara/Session Notes/Raw Session N Candidate.md" \
  --run-raw-notes-reconcile-provider codex \
  --raw-notes-reconciled-output "/home/babu/source/ellara/Session Notes/Raw Session N Reconciled Candidate.md"
```

## Raw Notes

The raw-note stage is candidate-first and reconciliation-required. It is not an OOC cleanup transcript and should not be timestamped. It should preserve clear IC dialogue and stated thoughts with minimal paraphrase where possible. If not using the pipeline resume command, process chunks manually or through an agent:

```bash
python3 scripts/transcription/run_raw_notes_subagents.py \
  "/home/babu/source/ellara/Session Notes/Raw Session N Chunks/chunks_manifest.json" \
  --provider codex \
  --workspace-root /home/babu/source \
  --finalize \
  --output-file "/home/babu/source/ellara/Session Notes/Raw Session N Candidate.md"
```

Expected output:

```text
/home/babu/source/ellara/Session Notes/Raw Session N Candidate.md
```

Then reconcile:

```bash
python3 scripts/transcription/reconcile_raw_notes.py \
  "/home/babu/source/ellara/Session Notes/Raw Session N Candidate.md" \
  "/home/babu/source/ellara/Session Notes/Raw Session N Reconciled Candidate.md" \
  --provider codex \
  --workspace-root /home/babu/source \
  --transcript "/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N.txt" \
  --force
```

After review, promote the reconciled raw candidate:

```bash
cp "/home/babu/source/ellara/Session Notes/Raw Session N Reconciled Candidate.md" \
  "/home/babu/source/ellara/Session Notes/Raw Session N.md"
```

Validate the approved raw artifact:

```bash
python3 scripts/transcription/validate_raw_notes.py \
  "/home/babu/source/ellara/Session Notes/Raw Session N.md" \
  --session N
```

Then produce polished notes with the `Final Session Notes` command above.

## Website Sync

Sync the polished note into the website session asset and optionally dispatch a website-update agent:

```bash
python3 scripts/transcription/run_website_sync_agent.py \
  --session N \
  --provider codex
```

This copies `/home/babu/source/ellara/Session Notes/Session N.md` to `src/assets/sessions/session-N.md`, then applies the logic in:

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
- update `src/views/HomeView.vue` hardcoded recap/next-step overrides when the generic extracted recap would be awkward, would lowercase a proper noun, or would surface an incidental detail instead of the session's main turn
- update `src/views/StorySoFarView.vue` with a new staged paragraph whenever the latest completed session materially changes the campaign state

Also review:

- `src/views/StorySoFarView.vue`
- `src/views/HomeView.vue`

Do not treat these view checks as optional for latest-session processing. Inspect both files every time and either update them or explicitly record that no update was needed.

Canonical-name QA:

- Use `ENTITY_LIST.md`, `src/store/lore.js`, and `scripts/transcription/name_corrections.json` as the spelling source of truth.
- `Nites` is spelled exactly `Nites` and pronounced knee-tes. Do not write `Nytes` or `Nýtes`.
- Preserve `Ellara`, `Nyx`, `Ysidor`, `Berridin`, and `Witty` capitalization in website copy and generated blurbs.
- If a generated note says a character asked about the wrong named person or concept, verify against the transcript/raw notes before syncing website data.
- For Session 17's Hýr/static-name beat, do not write that Hýr did not recognize `Jacinta`; that is a bad substitution for the Nites/unknown censored-name context. `Lady Jacinta` remains valid in her own Bastion sessions.
- For Session 17's Hýr/static-name beat, the Arcana natural 20 was Nyx's roll, not Berridin's. The follow-on realization that the voice was familiar also belongs to Nyx.
- Before final verification, grep the generated session and website copy for known bad forms such as `Nýtes`, `Nytes`, lowercase party names in sentence-leading blurbs, and accidental generated substitutions.

Roll/check attribution QA:

- Preserve important rolls/checks, but only name the roller when the transcript speaker, GM address, or approved raw notes explicitly identify them.
- If a roll matters but the roller is ambiguous, write `check: <skill> = <result> (roller uncertain)` in the raw notes and omit the roller in polished/public summaries.
- Do not transfer credit for natural 20s or lore-unlocking checks while polishing raw notes or reducing them into `sessions.js`, lore entries, HomeView copy, or Story So Far text.

After entity/store changes, regenerate:

```bash
npm run generate-list
```

Regenerating `ENTITY_LIST.md` also refreshes `scripts/transcription/entity_metadata.json`, which feeds future Whisper/Gladia name prompting. If new durable name/pronunciation issues were found, update `scripts/transcription/name_corrections.json` before this regeneration.

## Verification Gates

Run these before considering the job complete:

```bash
python3 -m json.tool scripts/transcription/name_corrections.json >/tmp/name_corrections.valid.json
/home/babu/.gemini/tmp/transcribe_env/bin/python3 -m py_compile \
  scripts/transcription/run_transcript_pipeline.py \
  scripts/transcription/filter_ooc.py \
  scripts/transcription/run_ooc_annotation_agents.py \
  scripts/transcription/validate_raw_notes.py \
  scripts/transcription/validate_session_pipeline.py \
  scripts/transcription/cleanup_session_artifacts.py \
  scripts/transcription/run_website_sync_agent.py \
  scripts/transcription/transcribe.py \
  scripts/transcription/transcribe_gladia.py \
  scripts/transcription/vad_compact.py
python3 scripts/transcription/validate_raw_notes.py "/home/babu/source/ellara/Session Notes/Raw Session N.md" --session N
python3 scripts/transcription/validate_session_pipeline.py --session N --check-clean
npm run sync-check
```

Check expected artifacts:

- `src/assets/sessions/transcripts/session_N_raw.txt`
- `/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N.txt`
- `/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N - OOC Removed.txt`
- `/home/babu/source/ellara/Session Notes/Raw Session N Candidate.md`
- `/home/babu/source/ellara/Session Notes/Raw Session N Reconciled Candidate.md`
- `/home/babu/source/ellara/Session Notes/Raw Session N.md`
- `/home/babu/source/ellara/Session Notes/Session N.md`
- `src/assets/sessions/session-N.md`
- `/home/babu/source/ellara/Session Notes/Transcripts/Transcript Session N - Pipeline Manifest.json`

## Ellara Repository Publication

After the approved raw notes and polished notes pass validation and the polished
notes match `src/assets/sessions/session-N.md`, commit and push the two durable
note files to the `ellara` repository:

```bash
git -C /home/babu/source/ellara fetch origin
git -C /home/babu/source/ellara add \
  "Session Notes/Raw Session N.md" \
  "Session Notes/Session N.md"
git -C /home/babu/source/ellara commit -m "Publish Session N notes"
git -C /home/babu/source/ellara push origin main
```

Do not include transcript scratch files, review candidates, diffs, or other
pipeline intermediates in this commit. Confirm the two published note paths
have no uncommitted changes and the local branch matches `origin/main` before
considering publication complete.

After durable outputs are reviewed and synced, clean scratch artifacts with a dry run first:

```bash
python3 scripts/transcription/cleanup_session_artifacts.py \
  --session N \
  --audio-dir "/path/to/session-audio" \
  --include-dnd-transcript-assets \
  --include-repo-scratch
```

Then apply when the planned removals are correct:

```bash
python3 scripts/transcription/cleanup_session_artifacts.py \
  --session N \
  --audio-dir "/path/to/session-audio" \
  --include-dnd-transcript-assets \
  --include-repo-scratch \
  --apply
```

## Determinism Notes

- Prefer `--stop-after-transcript` before downstream generation so transcript fixes happen once and feed every later artifact.
- Gladia is the default transcription provider in `run_transcript_pipeline.py`; pass `--transcription-provider whisper` only for intentional local fallback runs.
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
Use the transcript checkpoint flow with the default Gladia/cloud transcription provider unless I explicitly ask for Whisper/local. Stop after --stop-after-transcript and ask me to review the transcript.
After I confirm, run the annotation-first OOC cleanup checkpoint and show me the cleaned transcript comparison. After I approve the cleaned transcript, generate Raw Session N Candidate.md with clean raw-note subagents, run the raw-note reconciliation pass into Raw Session N Reconciled Candidate.md, validate it, and stop for review. After I approve or promote the reconciled candidate to Raw Session N.md, generate polished Session N.md, sync the website with run_website_sync_agent.py, run npm run sync-check plus validate_session_pipeline.py, publish Raw Session N.md and Session N.md to the ellara repository, and then run cleanup_session_artifacts.py after showing the dry run.
```

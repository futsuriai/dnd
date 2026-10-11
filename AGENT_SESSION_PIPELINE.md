# Agent Session Pipeline

Speaker audio in, website updated out, with no human checkpoints.

```bash
cd /home/babu/source/dnd
python3 scripts/transcription/run_session_auto.py --session N --audio-dir /home/babu/source/session-N
```

That runs every stage below, records progress in `<audio-dir>/pipeline/manifest.json`,
and leaves the Ellara notes and dnd site changes uncommitted. Add `--publish` to commit
both repos (and `--push` to push). Rerunning the same command skips finished stages.

## Inputs

- One audio file per speaker (Craig export: `1-aurusoriale.flac`, `2-ellanelle.flac`, ...).
  Tracks are mapped to characters by `scripts/transcription/speaker_map.json`.
- `dnd/.env.local` (git-ignored):

```bash
GLADIA_API_KEY=...
# optional, enables dice import from the D&D Beyond game log:
DDB_COBALT_SESSION=...   # CobaltSession cookie from www.dndbeyond.com (a login credential)
DDB_CAMPAIGN_ID=...      # number in https://www.dndbeyond.com/campaigns/<id>
```

- Agent CLIs logged in with the subscriptions: `codex` (default for notes/website),
  `claude` (`--provider claude`), `agy` (Gemini; only for optional audio checks).

## Stages

| stage | what it does | output |
|---|---|---|
| entities | `npm run generate-list` (ASR vocabulary comes from `entity_metadata.json`) | `ENTITY_LIST.md` |
| asr | each engine transcribes each track; silence is cut before upload | `<audio>/asr/<engine>/<track>.json` (+ raw Gladia JSON in `raw/`) |
| gemini | Gemini (via `agy`) listens to the lines Gladia and Whisper disagree on, in small parallel blocks | `<audio>/asr/gemini/` |
| transcript | assemble one chronological transcript from the primary engine | `Transcripts/Transcript Session N.txt` + `.lines.jsonl` |
| dice | fetch D&D Beyond rolls, find the recording start, insert `DICE:` lines | `<audio>/ddb/` |
| fuse | LLM judge reads every line's Gladia/Whisper/Gemini readings in context and picks or combines them | `Transcript Session N - Fusion Report.md` |
| diagnostics | engine comparison (coverage, disagreement, names, loops) | `Transcript Session N - ASR Diagnostics.md` |
| raw-notes | scene plan, then one notes call per scene, in the hand-written style | `Raw Session N.md` |
| notes | polished website notes | `Session N.md` |
| website | copy to `src/assets/sessions/`, agent updates stores and views | `src/` |
| verify | raw-note validator, `npm run sync-check`, pipeline validator | console |
| publish | only with `--publish` | git commits |

Useful flags: `--only STAGE`, `--from-stage STAGE`, `--stop-after STAGE`, `--force`,
`--provider claude`, `--fuse-provider claude` (judge only), `--engines`, `--primary`,
`--gemini off|disputed|all`, `--gemini-model`, `--judge`, `--no-fuse`.

## Transcription engines

- `gladia` (default primary): cloud. Uploads only detected speech; a session's billable
  audio is the sum of speech per track (Session 18: 58 min of speech from 6 × 65 min tracks).
  Custom vocabulary = every entity name that is not plain English, plus nicknames.
- `whisper-large-v3` (default second engine): local GPU, free, ~2× realtime on speech
  on the GTX 1660 Ti. `whisper-turbo` is faster with somewhat lower accuracy.
- Free-only run: `--engines whisper-large-v3 --primary whisper-large-v3`.
  Fusion then has no second engine and only fixes names from context.
- `gemini` (via `agy`, subscription): an extra reading, not a timeline. Only utterances
  where Gladia and Whisper disagree are sent, ~15 per clip (each from its speaker's own
  track, beep-separated), several calls in parallel on `gemini-3.8-flash-low`. Gemini's
  numbering can slip, so its words are attached to utterances by aligning them with the
  Gladia/Whisper words of the same clip; that is bookkeeping only and decides nothing.

`fuse` is the judge, and where most quality comes from. For each line it shows the
primary text plus every other engine's reading of the same moment, with the surrounding
conversation and campaign names, and lets the model take the best reading or combine
pieces (a name from Gemini, a number from Whisper). Examples it fixes: the GM saying "Hýr"
that every engine hears as "here", Gladia boosting "night" into "nites". A guard rejects
edits containing words no engine heard. The fusion report lists every edit with the
readings it chose from.

## Names and canon

`scripts/transcription/name_corrections.json` has four tiers:

- `text_fixes`: unambiguous misspellings, replaced everywhere and sent to Gladia.
- `capitalized_only_fixes`: real words or names (Mary, Nick, Laura) replaced only when
  capitalized and not after an article or title, so "the Baron" or "a nick" survive.
- `context_hints`: never auto-replaced; shown to the fusion and notes prompts.
- `aliases`: nicknames kept as spoken (Din = Berridin, Little Hill = Ysidor).

When a new recurring mishearing shows up in a fusion report or the diagnostics "near
misses", add it to the right tier rather than hand-fixing transcripts.

Canon rules the prompts enforce (`note_generation_guidance.py`):

- `Nites` exactly (knee-tes), never Nytes/Nýtes; `Hýr` in prose, `Hyr` in stores; `Hýrda`.
- Roll attribution: name the roller only when the transcript or a `DICE:` line says who
  rolled. With D&D Beyond configured, `DICE:` lines are authoritative.
- Session 17: the Hýr/static Arcana natural 20 was Nyx's, and the censored name is not
  Jacinta (the validator checks this).

## Website sync

`run_website_sync_agent.py` follows `.copilot/prompts/process-latest-session.md`: mark
session N complete in `src/store/sessions.js` and add the N+1 stub, add only significant
entity history and connections, and update the `HomeView.vue` and `StorySoFarView.vue`
copy. It then runs `npm run generate-list`, `npm run verify-session-sync -- --session latest`
and `npm run build`.

## Diagnostics for a new setup

```bash
# compare engines on a session (add --judge to let Gemini listen to the worst clips)
python3 scripts/transcription/run_session_auto.py --session N --audio-dir ... \
  --engines gladia,whisper-large-v3,whisper-turbo --stop-after diagnostics
```

Read `Transcript Session N - ASR Diagnostics.md`. Switch `--primary` if another engine
wins clearly on names and coverage.

## Cleanup

```bash
python3 scripts/transcription/cleanup_session_artifacts.py --session N --audio-dir ... \
  --include-dnd-transcript-assets   # dry run; add --apply
```

Cleanup deletes the compact VAD audio but keeps `asr/` (raw Gladia JSON, per-word engine
JSON), `ddb/`, the diagnostics, and `.lines.jsonl`, so later improvements can reprocess
old sessions without paying for transcription again.

## Legacy checkpointed flow

`run_transcript_pipeline.py` (manual transcript review, OOC annotation, 100-line chunk
notes, reconcile) still works and now uses the same name normalizer and Gladia fixes. See
git history of this file for its full instructions.

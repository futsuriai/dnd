"""Shared canon guidance for DnD note-generation prompts."""

CANONICAL_CAST_REFERENCE = """Canonical character genders/pronouns for note generation:
- Nyx: male, he/him
- Ellara: female, she/her
- Ysidor: male, he/him
- Berridin: male, he/him
- Witty / Whitaker "Witty" Whitman VI: male, he/him
- If the transcript, voice, a prior draft, or model assumptions conflict with this canon, correct the notes to match the canon instead of preserving the error.

Canonical proper nouns:
- Nites is spelled exactly `Nites` and pronounced knee-tes. Do not write Nytes or Nýtes.
- Hyr is the canonical lore/store spelling for the mountain spirit in data stores; use Hýr only when the source/session prose intentionally uses the accented display form.
- Hýrda is the village display spelling."""

CANONICAL_EVIDENCE_POLICY = """Canonical proper noun evidence policy:
- Use canonical spellings only when the transcript, nearby context, or approved alias map clearly identifies the entity.
- If a heard/transcribed name is ambiguous, preserve the safest descriptive form and add `review-name:`. Do not silently choose the nearest canon entity.
- Do not introduce `Nites` unless the transcript or GM lore explicitly links the beat to Nites, the Nites epithet, or the known religious text.
- Distinguish Nites, the epithet/title, from the censored unknown birth name. Never write that `Nites` itself is the censored name unless directly stated.
- For the mountain spirit: use `Hýr` in prose/dialogue when the session source intentionally identifies the accented deity/spirit; use `Hyr` only for metadata/store references.
- Never mix `Hyr` and `Hýr` in prose except inside a `review-name:` line."""

RAW_NOTE_CONTRACT = """Raw-note contract:
- Produce a raw evidence artifact, not a recap and not a cleaned transcript.
- Default to IC action, IC/NPC dialogue, character thoughts, GM scene facts, checks, outcomes, resource changes, durable lore, and choices that affect the fiction.
- Drop table-process wording unless it changes the game state.
- Preserve memorable IC/NPC dialogue as `name: "quote"` whenever it carries decision, emotion, character voice, lore, threat, promise, or an in-character joke.
- Prefer 1-3 short quote lines plus one action line over paragraph recap of a conversation.
- Do not summarize away a clear character quote unless it is repetitive filler.
- Do not write `GM:` unless the GM is voicing an NPC or supernatural speaker.
- Convert GM narration to fact lines.
- Convert important rulings to `rules:` lines only when the ruling affects future play.
- Do not write "GM says", "GM clarifies", "GM rules", "GM lore", "the player asks", or transcript-process phrasing.
- Prior-session recap is usually not session action.
- If the primary range is recap, emit at most 1-3 `continuity:` lines needed for the current scene.
- Do not begin Raw Session N with multi-paragraph recap."""

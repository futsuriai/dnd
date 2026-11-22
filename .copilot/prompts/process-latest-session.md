You are processing the latest game session to update world data stores.

Context
- This prompt is the website/world-data sync step. It assumes transcript cleanup and session-note generation are already complete.
- For the full raw-audio-to-website-and-Ellara workflow, read `AGENT_SESSION_PIPELINE.md`.
- Use the polished website session markdown (`src/assets/sessions/session-<N>.md`) as your primary narrative source, not the raw transcript, unless you need to verify ambiguity.
- Do not update website stores from an unreviewed transcript.
- End every autofix run with `npm run sync-check` (which runs `npm run generate-list`, `npm run verify-session-sync -- --session latest`, and `npm run build`) unless the user explicitly asked for report-only mode.

Inputs you must use:
1) Latest session summary: Determine the highest-numbered session file in `src/assets/sessions/session-*.md`
2) World data stores:
   - Sessions index (including homepage recap/next-steps and Story So Far beats): `src/store/sessions.js`
   - Lore: `src/store/lore.js`
   - Locations: `src/store/locations.js`
   - NPCs: `src/store/npcs.js`
3) Canonical entity list: `ENTITY_LIST.md`

Mode
- MODE: `autofix` (default for editing agents such as `run_website_sync_agent.py`) | `report`
  - `autofix`: Edit the target store files directly in place, run `npm run sync-check`, and print a concise processing report listing changed files and validation results. (Do not print a unified diff instead of editing files.)
  - `report`: Produce a processing report only, no file edits.

History-first policy (important)
- Treat an entity's `history` array (items like `{ session: N, note: '<cause/change>' }`) as the single source of truth for "this entity was modified/referenced in session N".
- Do NOT introduce or maintain `updatedInSessions`; `src/store/config.js` and `src/store/worldData.js` derive session highlights directly from `history`.
- Only add history entries for significant events. A mere mention of a place or person does not warrant history. Examples of significance:
  - State change (rescued, captured, killed, promoted, moved, discovered)
  - New connection added or clarified (NPC at Location, faction affiliation, location containment)
  - New lore revealed or corrected (technological breakthrough, political action, divine insight)
  - First introduction to the campaign (if the entity becomes part of the canon data store)
  - A notable scene occurred there (battle, heist, negotiation) that impacts the world model

Source of Truth (Entity Names)
- `ENTITY_LIST.md`: This file contains the canonical list of all IDs and Display Names.
- ALWAYS consult this file first. Do not guess IDs. Match the existing ID exactly.
- If a name is similar but not identical, assume it is the existing entity unless context clearly dictates otherwise.
- Always run `npm run generate-list` (or `npm run sync-check`) after editing any store file so `ENTITY_LIST.md` and `scripts/transcription/entity_metadata.json` stay in sync.

Task
1) Identify the latest session N by finding the highest-numbered `src/assets/sessions/session-*.md` file.
2) Parse the session summary and extract referenced entities:
   - Locations/POIs: places, roads, bridges, taverns/inns, landmarks, dungeons, workshops, shrines.
   - NPCs: named individuals with roles or titles.
     - Do NOT treat party members as NPCs: `Nyx`, `Ellara`, `Ysidor`, `Berridin`, `Witty` (`Whitaker "Witty" Whitman VI`), and former PC `Tsi'nyra`.
   - Lore: factions, councils, orders, technologies, divine aspects, processes.
3) Normalize each reference into a canonical id (kebab-case, see ID Rules) and check `ENTITY_LIST.md` first.
4) For each genuinely impacted entity (typically 3–8 entities for a normal session):
   - If missing from data stores and clearly significant: create a minimal entity stub (see Stub Rules).
   - If existing and materially changed in session N: append `{ session: N, note: '...' }` to `history`.
   - If new relationships were revealed: add `connections` entries using `{ type, id, reason }` (ALWAYS `reason:`, NEVER `relationship:`).
   - Only update `description` non-destructively when new permanent facts about what the entity *is* were revealed (never put pending party plans or open tasks into `description`).
5) Update `src/store/sessions.js` for session N and session N+1:
   - Update the `session-N` object:
     - `upcoming: false`
     - `summaryFile: 'session-N.md'`
     - `subtitle`, `location`, `date`, and `description`
     - `highlights`: 5–8 concise, plain-English bullet strings (under ~220 chars each)
     - `homeRecap`: concise 2–3 sentence homepage recap string for "Where We Left Off"
     - `nextSteps`: concise array of next-step strings (or string) for "What Comes Next"
     - `storyBeat`: narrative chronicle paragraph for `StorySoFarView.vue` when session N materially advances the campaign arc
   - Create or verify the `session-(N+1)` upcoming stub at the top of the `sessions` array:
     - `id: 'session-N+1'`, `title: 'Session N+1'`, `subtitle`, `location`, `date` (provided next-session date or `'TBD'`), `upcoming: true`, non-placeholder `description`, `highlights: []`
6) Do NOT manually edit `src/views/HomeView.vue` or `src/views/StorySoFarView.vue`:
   - Both views read `homeRecap`, `nextSteps`, and `storyBeat` directly from `src/store/sessions.js`.
7) Run deterministic verification:
   - `npm run sync-check` (runs `npm run generate-list`, `npm run verify-session-sync -- --session latest`, and `npm run build`).

Output
Print a concise Markdown processing report:
- Latest Session: N
- Files Changed
- Session Index Updated (`session-N` fields including `homeRecap`/`nextSteps`/`storyBeat`, plus `session-(N+1)` stub)
- New Entities Created (with short evidence quote)
- History Entries Added (with short evidence quote)
- Connections Added (`reason:` key only)
- Descriptions Updated
- Verification Commands Run & Exit Status

Constraints
- Non-destructive: do not remove or rewrite existing descriptions or connection reasons unless clearly factually wrong.
- Keep exports intact (`export const ...` and default export where present); preserve code style and array order.
- Do not touch router, views, or components from this prompt.
- When unsure (low confidence), omit the speculative edit and note it in the report.
- Never introduce `updatedInSessions` or `relationship:` connection keys.
- Focus on the latest session only — do not retroactively rewrite historical sessions.
- Do not infer major canon changes from ASR noise or raw-note uncertainty; rely on explicit events in `session-N.md`.
- Canonical spelling QA: consult `ENTITY_LIST.md`, `src/store/lore.js`, `scripts/transcription/name_corrections.json`, and `scripts/shared_sync_rules.json`. Preserve party-name capitalization (`Ellara`, `Nyx`, `Ysidor`, `Berridin`, `Witty`). Use `Nites` exactly (pronounced knee-tes; never `Nytes` or `Nýtes`). Use `Hyr` in data stores (and `Hýr` only when quoting accented prose).
- Roll attribution QA: when public copy credits a named character with a natural 20, skill check, or lore-unlocking roll, `session-N.md` must explicitly support that exact roller. If ambiguous, omit the roller name rather than guessing.

Heuristics & Mapping
- NPC cues: "met <Name>", "<Name>, the <role>", titles (Proctor, Captain, Smith), speech acts.
- Location cues: "at/in/near <Place>", suffixes/keywords (road, bridge, tavern, inn, lighthouse, workshop, shrine, district).
- Lore cues: capitalized collectives (Lightkeepers, Council), technologies (warforged, crystals), divine concepts.
- Connections (always use `reason:`):
  - NPC at/in Location => `{ type: 'location', id: '<locId>', reason: 'present at' }`
  - NPC member/agent of Lore => `{ type: 'lore', id: '<loreId>', reason: 'affiliation' }`
  - NPC related to NPC => `{ type: 'npc', id: '<npcId>', reason: '<relation>' }`
  - NPC related to PC => `{ type: 'character', id: '<charId>', reason: '<relation>' }`
  - Location within Province/City => `{ type: 'location', id: '<parentId>', reason: 'within' }`

ID Rules
- Lowercase, kebab-case; strip punctuation; collapse spaces to `-`.
- Keep meaningful suffixes: road, bridge, tavern, inn, lighthouse, workshop, shrine.
- Examples: `"Old Trade Road"` => `old-trade-road`; `"Proctor Eduard"` => `proctor-eduard`.

Stub Rules (`autofix` only; minimal and safe)
- Locations: `{ id, name, type: 'poi', description: '...', connections: [], history: [{ session: N, note: '...' }] }`
- NPCs: `{ id, name, role: '<from text|"Unknown">', location: '<if clear|"Unknown">', description: '...', connections: [], history: [{ session: N, note: '...' }] }`
- Lore: `{ id, term, description: '...', connections: [], history: [{ session: N, note: '...' }] }`

Quality gates
- No syntax errors in modified files.
- No duplicate `history.session` values within an entity; keep `history` sorted ascending by `session`.
- All `connections` reference valid existing IDs (or newly added stubs in the same edit) and use `reason:`.
- Reruns must be idempotent: verify an already-processed `session-N` and `session-(N+1)` stub instead of duplicating entries.

You are processing the latest game session to update world data stores.

Context
- This prompt is the website/world-data sync step. It assumes transcript cleanup and session-note generation are already complete.
- For the full raw-audio-to-website workflow, read `AGENT_SESSION_PIPELINE.md`.
- Use the polished website session markdown as your primary narrative source, not the raw transcript, unless you need to verify ambiguity.
- Do not update website stores from an unreviewed transcript.
- End every autofix run with `npm run generate-list`, `npm run verify-session-sync -- --session latest`, and `npm run build` unless the user explicitly asked for report-only mode.

Inputs you must use:
1) Latest session summary: Determine the highest-numbered session file in src/assets/sessions/session-*.md
2) World data stores:
   - Lore: src/store/lore.js
   - Locations: src/store/locations.js
   - NPCs: src/store/npcs.js
   - Sessions index: src/store/sessions.js (for session metadata and numbering)
3) Canonical entity list: ENTITY_LIST.md

Mode
- MODE: report (default) | autofix
  - report: Produce a processing report only, no code changes.
  - autofix: In addition to the report, output a minimal, safe patch to implement changes (see Autofix Scope).

History-first policy (important)
- Treat an entity's history array (items like { session: N, note: '<cause/change>' }) as the source of truth for "this entity was modified/referenced in session N".
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
- If you add a NEW entity to the data stores, you must also update `ENTITY_LIST.md` in your autofix (or instruct the user to run `npm run generate-list`).

Task
1) Identify the latest session N by finding the highest-numbered session-*.md file
2) Parse the session summary and extract referenced entities with heuristics:
   - Locations/POIs: places, roads, bridges, taverns/inns, landmarks, dungeons, workshops, shrines.
   - NPCs: named individuals with roles or titles.
     - Be careful not to treat party members Nyx, Tsi'Nyra, Ellara, Ysidor, Berridin as NPCs
   - Lore: factions, councils, orders, technologies, divine aspects, processes.
3) Normalize each reference into a canonical id (kebab-case, see ID rules).
   - Consult `ENTITY_LIST.md` to match existing names/IDs first.
4) For each entity:
   - If missing from data stores: Create new entity stub (see Stub Rules)
     - NOTE: If you add a new entity, you must also update `ENTITY_LIST.md` with the new ID and Name in your autofix patch.
   - If exists but no history for session N: Add appropriate history entry
   - If missing connections revealed in session: Add connections
   - If description needs updating based on new information: Update description
5) Update sessions.js for session N:
   - Check if session N already has upcoming: false and populated highlights
   - If no, update session N entry with:
     - Set upcoming: false
     - Add summaryFile: 'session-N.md'
     - Update subtitle if needed based on session content
     - Update description with brief summary
     - Populate highlights array with 5-10 key events
   - If yes, verify added highlights properly convey what happened and match the session but don't duplicate data
  - Create or verify session N+1 stub at top of array:
     - id: 'session-N+1'
     - title: 'Session N+1'
     - subtitle: '<something fitting for where we left off>'
     - date: '<today\'s date>'
     - upcoming: true
     - Empty highlights array
   - Placeholder description
6) Review latest-session website copy:
   - Inspect `src/views/HomeView.vue`
   - Inspect `src/views/StorySoFarView.vue`
   - Add or update hardcoded latest-session recap / next-step copy when generic extracted prose would lowercase proper nouns, surface incidental details, or miss the main session turn
   - Add a new Story So Far staged paragraph when the session materially changes the campaign state
   - If no update is needed, state why in the report
7) Run deterministic verification:
   - `npm run generate-list`
   - `npm run verify-session-sync -- --session latest`
   - `npm run build`

Output
1) Processing Report (Markdown):
   - Latest Session: N
   - Session Index Updated
     - Updated session N metadata (upcoming, highlights, description, summaryFile)
     - Created session N+1 stub (if applicable)
   - New Entities Created
     - <type> <id> — evidence: "<short quote>"; rationale
   - History Entries Added
     - <type> <id> — added history { session: N, note: '<short cause>' }; evidence: "<short quote>"
   - Connections Added
     - <type> <id> — add connection { type: <entityType>, id: <id>, reason: "<short phrase>" }
   - Descriptions Updated
     - <type> <id> — updated description based on new information
   - View Copy Updated
     - HomeView / StorySoFarView changes, or explicit reason no update was needed
   - Confidence: low/medium/high per bullet.

2) If MODE=autofix, append a Unified Diff (patch) that:
   - Updates sessions.js for session N (unless already processed):
     - Mark session N as upcoming: false
     - Add summaryFile reference
     - Populate highlights with key events
     - Update description with session summary
     - Create session N+1 stub with upcoming: true and today's date at the top of the array
   - Creates new entity stubs for clearly-new entities with initial history entry
   - Adds history entry { session: N, note: '<short cause>' } for existing entities when a significant event occurred
   - Adds obvious connections with a brief reason
   - Updates descriptions to incorporate new information from the session
   - Updates `HomeView.vue` and `StorySoFarView.vue` when required by the latest-session state
   - Remove updatedInSessions properties if equivalent history is present (high confidence only)
   - Includes a concise change summary at the top.

Constraints
- Non-destructive. Do not remove or substantially rewrite existing descriptions unless clearly incorrect.
- Keep exports intact; preserve code style and array order where feasible.
- Do not touch router/views/components from this prompt except when explicitly asked to refresh Story So Far or Home copy. If you do, keep those edits scoped to current-state/session-recap text.
- When unsure (low confidence), report only — do not autofix.
- Do not introduce new updatedInSessions values. Prefer history entries.
- Focus on the latest session only - do not process historical sessions.
- Session index updates: Only update session N if it has upcoming: true or empty highlights. If already processed (upcoming: false and populated highlights), skip session update.
- Do not infer major canon changes from ASR noise or raw-note uncertainty. Prefer explicit events in the polished summary.
- Canonical spelling QA: use `ENTITY_LIST.md`, lore/store entries, and `name_corrections.json` as spelling sources. Preserve party-name capitalization in blurbs. Use `Nites` exactly, pronounced knee-tes; do not write `Nytes` or `Nýtes`.
- Do not rely on generic first/last-sentence extraction for public copy if it produces lowercase proper nouns or highlights a low-priority lore aside over the session's main state change.
- Roll attribution QA: when public copy credits a named character with a natural 20, skill check, or lore-unlocking roll, the polished session summary must explicitly support that exact roller. If the source is ambiguous, omit the character name rather than guessing.

Heuristics & Mapping
- NPC cues: "met <Name>", "<Name>, the <role>", titles (Proctor, Captain, Smith), speech acts.
- Location cues: "at/in/near <Place>", suffixes/keywords (road, bridge, tavern, inn, lighthouse, workshop, shrine, district).
- Lore cues: capitalized collectives (Lightkeepers, Council), technologies (warforged, crystals), divine concepts.
- Connections:
  - NPC at/in Location => NPC.connections += { type: 'location', id: <locId>, reason: 'present at' }
  - NPC member/agent of Lore => NPC.connections += { type: 'lore', id: <loreId>, reason: 'affiliation' }
  - NPC is related to an NPC => => NPC.connections += { type: 'npc', id: <npcId>, reason: 'affiliation' }
  - NPC is related to a character => => NPC.connections += { type: 'character', id: <npcId>, reason: 'affiliation' }
  - Location within Province/City => Location.connections += { type: 'location', id: <parentId>, reason: 'within' }
  - Others should use existing connection types if they are reasonable.

ID Rules
- Lowercase, kebab-case; strip punctuation; collapse spaces to '-'.
- Keep meaningful suffixes: road, bridge, tavern, inn, lighthouse, workshop, shrine.
- Examples: "Old Trade Road" => old-trade-road; "Proctor Eduard" => proctor-eduard.

Stub Rules (autofix only; minimal and safe)
- Locations: { id, name, type: 'poi' (or best-fit), description: 'Introduced in Session N.', connections: [], history: [{ session: N, note: 'First mentioned' }] }
- NPCs: { id, name, role: '<from text if clear|"Unknown">', location: '<if clear|"Unknown">', description: 'Introduced in Session N.', connections: [], history: [{ session: N, note: 'First encountered' }] }
- Lore: { id, term, description: 'Introduced in Session N.', connections: [], history: [{ session: N, note: 'First revealed' }] }
- For existing entities getting updates, add concise history notes reflecting the change.

Entity Enhancement Rules
- For existing entities, if the session reveals new information:
  - Update description to incorporate new details (non-destructively)
  - Add relevant connections discovered in the session
  - Always add a history entry documenting the change/revelation

Significance filter for creation and history
- Only create entities or add history entries for substantial events or introductions
- Favor quality over quantity; only add when the session clearly establishes the entity in canon or changes its state/relationships
- Avoid creating entries for trivial mentions or passing references

Quality gates
- No syntax errors in modified files
- Avoid duplicate history.session values; keep history sorted ascending by session when practical
- Connections reference existing ids (or stubs you add in the same patch)
  - New descriptions maintain existing tone and style
- Reruns must be idempotent: verify an existing processed session N and existing N+1 stub instead of duplicating or replacing them unless they are stale or incorrect.

Session Discovery
- Find all session-*.md files in src/assets/sessions/
- Extract numeric values and determine the maximum
- Process only that highest-numbered session

Report template (example)
---
Latest Session: 7
- Session Index Updated
  - Updated session 7: marked complete, added highlights and summary
  - Created session 8 stub for next session
- New Entities Created
  - location emerald-dock — evidence: "arrived at the Emerald Dock" — new location mentioned.
- History Entries Added
  - npc captain-hayes — added history { session: 7, note: 'Provided passage across the harbor' } — evidence: "Captain Hayes agreed to ferry them"
- Connections Added
  - npc captain-hayes — add { type: 'location', id: 'emerald-dock', reason: 'operates from' }
- Descriptions Updated
  - location bastion-harbor — updated to include reference to Emerald Dock
---

Patch header (autofix):
- summary: process session 7; update session index; add 1 location stub; add 2 history entries; add 1 connection; update 1 description.

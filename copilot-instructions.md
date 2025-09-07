Repository workspace instructions for Copilot

Purpose
- Automate updating world data (lore, locations, NPCs) after each game session using the latest session summary.
- Validate that session summaries are reflected in the data (detect missing entities, flags, or connections).

Sources of truth
- Session summaries: src/assets/sessions/session-*.md
- Data stores to update:
  - Lore: src/store/lore.js
  - Locations: src/store/locations.js
  - NPCs: src/store/npcs.js
  - Session flagging: src/store/config.js (currentSession is inferred)

UI behavior
- Entities (lore, locations, NPCs) show a “New” badge when entity.updatedInSession === currentSession.

Entity schemas
- Lore item
  - { id, term, description, fullText?, connections?: Array<{type, id, reason?}>, updatedInSessions?: number[] }
  - Optional: history?: Array<{ session: number, note: string }>
- Location
  - { id, name, type, description, fullText?, tags?: string[], connections?: Array<{type, id, relationship?|reason?}>, updatedInSessions?: number[] }
  - Optional: history?: Array<{ session: number, note: string }>
  - Valid type examples: province, capital, city, dungeon, poi, landmark, tavern
- NPC
  - { id, name, role, location, description, fullText?, connections?: Array<{type, id, reason?}>, updatedInSessions?: number[] }
  - Optional: history?: Array<{ session: number, note: string }>
  - Do not add alignment/status fields.

Canonical IDs
- Use stable, kebab-case ids (e.g., duskbreaker-lighthouse, old-trade-road, proctor-eduard).
- Reuse existing ids whenever the same entity appears again; do not duplicate.

Update rules per session
1) Read the latest summary file (highest session number) from src/assets/sessions.
2) Extract:
   - New or newly named Places (locations/landmarks/POIs/taverns/roads/bridges).
   - New NPCs and named roles.
   - New Lore terms (factions, technologies, religious concepts, processes).
3) For each new entity:
   - Add an entry to the correct store array.
   - Include connections to already-known entities (locations/lore/characters) when explicitly referenced.
  - Append the current session number to updatedInSessions (create the array if missing).
4) For existing entities that gained info:
   - Update description/fullText/connections non-destructively.
  - Append the current session number to updatedInSessions (create the array if missing and avoid duplicates).
5) For entities not changed this session:
  - Do not modify their updatedInSession. Only set it when you actually change or add the entity for this session.
6) Keep connections consistent with existing ids. If a referenced entity doesn’t exist yet, either:
   - Add a minimal stub in the right store (name/term + description placeholder) with updatedInSession, or
   - Leave a TODO comment with the intended id and skip adding the connection.
7) Optional: Seed or append to `history` with concise `{ session, note }` entries for significant beats mentioned in the summary.

Session flag
- currentSession is inferred automatically from src/store/sessions.js (the last completed session, i.e., the one before the upcoming session).

Quality gates
- No syntax errors in modified files.
- Arrays remain exported with both named and default export where present.
- Do not alter router or views unless asked; the UI shows “New” automatically via updatedInSession/currentSession.

Commit message template
- chore(data): update world data for Session <N> — lore(<ids>), locations(<ids>), npcs(<ids>)

Examples
- Add a new POI mentioned in the session: create an object in locations.js with { id, name, type: 'poi' or 'landmark', description, tags, connections, updatedInSession }.
- Add a new NPC: create an object in npcs.js with { id, name, role, location, description, fullText?, connections, updatedInSession }.
- Add a new lore term: create an object in lore.js with { id, term, description, fullText?, connections, updatedInSession }.

Prompts
- Update world data after the latest session:
  - .copilot/prompts/update-world-data.md
- Validate all sessions vs. data (report or autofix gaps):
  - .copilot/prompts/validate-world-updates.md

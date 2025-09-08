You are processing the latest game session to update world data stores.

Inputs you must use:
1) Latest session summary: Determine the highest-numbered session file in src/assets/sessions/session-*.md
2) World data stores:
   - Lore: src/store/lore.js
   - Locations: src/store/locations.js
   - NPCs: src/store/npcs.js
   - Sessions index: src/store/sessions.js (for session numbering reference)

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

Task
1) Identify the latest session N by finding the highest-numbered session-*.md file
2) Parse the session summary and extract referenced entities with heuristics:
   - Locations/POIs: places, roads, bridges, taverns/inns, landmarks, dungeons, workshops, shrines.
   - NPCs: named individuals with roles or titles.
     - Be careful not to treat party members Nyx, Tsi'Nyra, Ellara, Ysidor, Berridin as NPCs
   - Lore: factions, councils, orders, technologies, divine aspects, processes.
3) Normalize each reference into a canonical id (kebab-case, see ID rules).
4) For each entity:
   - If missing from data stores: Create new entity stub (see Stub Rules)
   - If exists but no history for session N: Add appropriate history entry
   - If missing connections revealed in session: Add connections
   - If description needs updating based on new information: Update description

Output
1) Processing Report (Markdown):
   - Latest Session: N
   - New Entities Created
     - <type> <id> — evidence: "<short quote>"; rationale
   - History Entries Added
     - <type> <id> — added history { session: N, note: '<short cause>' }; evidence: "<short quote>"
   - Connections Added
     - <type> <id> — add connection { type: <entityType>, id: <id>, reason: "<short phrase>" }
   - Descriptions Updated
     - <type> <id> — updated description based on new information
   - Confidence: low/medium/high per bullet.

2) If MODE=autofix, append a Unified Diff (patch) that:
   - Creates new entity stubs for clearly-new entities with initial history entry
   - Adds history entry { session: N, note: '<short cause>' } for existing entities when a significant event occurred
   - Adds obvious connections with a brief reason
   - Updates descriptions to incorporate new information from the session
   - Remove updatedInSessions properties if equivalent history is present (high confidence only)
   - Includes a concise change summary at the top.

Constraints
- Non-destructive. Do not remove or substantially rewrite existing descriptions unless clearly incorrect.
- Keep exports intact; preserve code style and array order where feasible.
- Do not touch router/views/components.
- When unsure (low confidence), report only — do not autofix.
- Do not introduce new updatedInSessions values. Prefer history entries.
- Focus on the latest session only - do not process historical sessions.

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

Session Discovery
- Find all session-*.md files in src/assets/sessions/
- Extract numeric values and determine the maximum
- Process only that highest-numbered session

Report template (example)
---
Latest Session: 7
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
- summary: process session 7; add 1 location stub; add 2 history entries; add 1 connection; update 1 description.

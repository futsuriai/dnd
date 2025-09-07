You are validating world data against all game session summaries.

Inputs you must use:
1) All session summaries: src/assets/sessions/session-*.md (iterate ascending by N)
2) World data stores:
   - Lore: src/store/lore.js
   - Locations: src/store/locations.js
   - NPCs: src/store/npcs.js
   - Sessions index: src/store/sessions.js (for upcoming/completed and to cross-check N)

Mode
- MODE: report (default) | autofix
  - report: Produce a validation report only, no code changes.
  - autofix: In addition to the report, output a minimal, safe patch to fix clear gaps (see Autofix Scope).

History-first policy (important)
- Treat an entity's history array (items like { session: N, note: '<cause/change>' }) as the source of truth for "this entity was modified/referenced in session N".
- Only add history entries for significant events. A mere mention of a place or person does not warrant history. Examples of significance:
  - State change (rescued, captured, killed, promoted, moved, discovered)
  - New connection added or clarified (NPC at Location, faction affiliation, location containment)
  - New lore revealed or corrected (technological breakthrough, political action, divine insight)
  - First introduction to the campaign (if the entity becomes part of the canon data store)
  - A notable scene occurred there (battle, heist, negotiation) that impacts the world model

Backfill directive
- When running in autofix, backfill missing history entries for significant events inferred from session summaries 1..N.
- Don't create a duplicate entry if one already exists, if one does verify that the change you are providing new and valuable changes to the history array, especially first introductions are important

Task
For each session N:
- Parse the session summary and extract referenced entities with heuristics:
  - Locations/POIs: places, roads, bridges, taverns/inns, landmarks, dungeons, workshops, shrines.
  - NPCs: named individuals with roles or titles.
    - Be careful not to treat party members Nyx, Tsi'Nyra, Ellara, Ysidor, Berridin as NPCs
  - Lore: factions, councils, orders, technologies, divine aspects, processes.
- Normalize each reference into a canonical id (kebab-case, see ID rules).
- Cross-check against data stores:
  1) Missing entity: Not present in the corresponding store.
  2) Mentioned but not recorded: Present, but history has no entry for session N despite a significant event/change.
  3) Missing connection: Text indicates a relationship (e.g., NPC at Location; member of Faction) not present in connections.
  4) Potential duplicate: Multiple entities with similar names/ids that might refer to the same thing.

Additionally, for any entity that is changed or clearly involved in session N, ensure a history entry exists, e.g., { session: N, note: '<short cause>' }.

Output
1) Validation Report (Markdown), grouped by session:
   - Session N
     - Missing Entities
       - <type> <suggested-id> — evidence: "<short quote>"; rationale
     - Missing History Entries
       - <type> <id> — needs history { session: N, note: '<short cause>' }; evidence: "<short quote>"
     - Missing/Incorrect Connections
       - <type> <id> — add connection { type: <entityType>, id: <id>, reason: "<short phrase>" }
     - Potential Duplicates/Conflicts
       - <idA> vs <idB> — similarity: <reason>
   - Confidence: low/medium/high per bullet.

2) If MODE=autofix, append a Unified Diff (patch) that:
  - Adds a history entry { session: N, note: '<short cause>' } for existing entities when a significant event occurred (avoid duplicates; keep history sorted by session when practical).
   - Optionally creates minimal stubs for clearly-new entities (see Stub Rules) and include an initial history entry.
   - Optionally appends obvious connections with a brief reason.
  - Remove updatedInSessions properties repository-wide once equivalent history is present (high confidence only). Do not add new updatedInSessions values.
   - Includes a concise change summary at the top.

Constraints
- Non-destructive. Do not remove or substantially rewrite descriptions.
- Keep exports intact; preserve code style and array order where feasible.
- Do not touch router/views/components.
- When unsure (low confidence), report only — do not autofix.
- Do not introduce new updatedInSessions values. Prefer history entries. If removing updatedInSessions, only do so when equivalent history exists for those sessions.

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
  - Others should use existing connection types if they are reasonable. Verify that we have all connections mapped and updated.

ID Rules
- Lowercase, kebab-case; strip punctuation; collapse spaces to '-'.
- Keep meaningful suffixes: road, bridge, tavern, inn, lighthouse, workshop, shrine.
- Examples: "Old Trade Road" => old-trade-road; "Proctor Eduard" => proctor-eduard.

Stub Rules (autofix only; minimal and safe)
- Locations: { id, name, type: 'poi' (or best-fit), description: 'Mentioned in Session N.', connections: [], history: [{ session: N, note: 'Mentioned in session' }] }
- NPCs: { id, name, role: '<from text if clear|"Unknown">', location: '<if clear|"Unknown">', description: 'Mentioned in Session N.', connections: [], history: [{ session: N, note: 'Mentioned in session' }] }
- Lore: { id, term, description: 'Mentioned in Session N.', connections: [], history: [{ session: N, note: 'Mentioned in session' }] }
- Whenever a stub or existing entity is clearly updated (connections added, fields clarified), add a concise history note reflecting the change.

Significance filter for stubs and history
- Do not create stubs or history entries for trivial mentions. Favor quality over quantity; only add when the session clearly establishes the entity in canon or changes its state/relationships.

Quality gates
- No syntax errors in modified files.
- Avoid duplicate history.session values; keep history sorted ascending by session when practical.
- Connections reference existing ids (or stubs you add in the same patch).

Report template (example excerpt)
---
Session 6
- Missing Entities
  - location faberge-workshop — evidence: "Faberge’s workshop in Bastion" — highly likely POI.
- Missing History Entries
  - npc proctor-eduard — needs history { session: 6, note: 'Discussed investigation/escalation' } — evidence: "met with Proctor Eduard…"
- Missing/Incorrect Connections
  - npc donnathan-reeves — add { type: 'location', id: 'bastion-city', reason: 'operates in' }
---

Patch header (autofix):
- summary: add history entries to 3 entities; add 1 location stub; add 2 connections; remove deprecated updatedInSessions from 2 entities (fully covered by history).

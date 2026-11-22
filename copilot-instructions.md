Repository workspace instructions for AI assistants

Purpose
- Automate updating world data (`sessions`, `lore`, `locations`, `npcs`) after each game session using the latest polished session summary.
- Keep the website, generated entity artifacts, and sibling Ellara campaign state validated and in sync.

Canonical Pipeline & Prompts
- Full audio -> transcript -> notes -> website -> ellara-state -> verify workflow:
  `AGENT_SESSION_PIPELINE.md` and `scripts/transcription/run_session_auto.py`
- Post-session website store update prompt:
  `.copilot/prompts/process-latest-session.md`
- Shared validation rules (used by both Python and Node verifiers):
  `scripts/shared_sync_rules.json`

Sources of Truth
- Polished session summaries: `src/assets/sessions/session-*.md`
- Data stores to update:
  - Sessions index & homepage/chronicle copy: `src/store/sessions.js`
  - Lore: `src/store/lore.js`
  - Locations: `src/store/locations.js`
  - NPCs: `src/store/npcs.js`
  - Party PCs (do NOT add as NPCs): `src/store/characters.js` (`Nyx`, `Ellara`, `Ysidor`, `Berridin`, `Witty` / `Whitaker "Witty" Whitman VI`)
  - Session flagging: `src/store/config.js` (`currentSession` is inferred from `sessions.js`)

UI Behavior (Data-Driven)
- Entities (`lore`, `locations`, `npcs`, `characters`) display a "New" / "Updated" badge automatically when `entity.history` contains an entry with `session === currentSession`. Do NOT use `updatedInSessions`.
- `HomeView.vue` reads `homeRecap` and `nextSteps` directly from `src/store/sessions.js`.
- `StorySoFarView.vue` reads `storyPreamble` and per-session `storyBeat` (falling back to `description`) directly from `src/store/sessions.js`.
- Do NOT manually edit `HomeView.vue` or `StorySoFarView.vue` for normal session updates.

Entity Schemas
- Session (`src/store/sessions.js`):
  - `{ id, title, subtitle, location, date, upcoming, summaryFile?, description, highlights: string[], homeRecap?: string, nextSteps?: string[] | string, storyBeat?: string }`
- Lore item (`src/store/lore.js`):
  - `{ id, term, description, fullText?, connections?: Array<{ type, id, reason }>, history: Array<{ session: number, note: string }> }`
- Location (`src/store/locations.js`):
  - `{ id, name, type, description, fullText?, tags?: string[], connections?: Array<{ type, id, reason }>, history: Array<{ session: number, note: string }> }`
  - Valid type examples: `province`, `capital`, `city`, `district`, `dungeon`, `poi`, `landmark`, `tavern`
- NPC (`src/store/npcs.js`):
  - `{ id, name, role, location, description, fullText?, connections?: Array<{ type, id, reason }>, history: Array<{ session: number, note: string }> }`
  - Do not add alignment/status fields.

Canonical IDs & Connections
- Use stable, kebab-case ids (e.g., `duskbreaker-lighthouse`, `old-trade-road`, `proctor-eduard`).
- Reuse existing ids from `ENTITY_LIST.md`; never duplicate entities.
- Every connection object MUST use `reason:` (never `relationship:`) and reference an existing `type` + `id`.

Update Rules per Session
1) Read the latest polished summary (`src/assets/sessions/session-N.md`).
2) Update `src/store/sessions.js`:
   - Mark `session-N` `upcoming: false`, set `summaryFile: 'session-N.md'`, update `subtitle`, `location`, `date`, `description`, `highlights` (5–8 entries), `homeRecap`, `nextSteps`, and `storyBeat` (when warranted).
   - Ensure `session-(N+1)` is the single `upcoming: true` entry at index 0 with a non-placeholder description and `highlights: []`.
3) Update only genuinely affected entities (typically 3–8 per session) in `lore.js`, `locations.js`, and `npcs.js`:
   - Append `{ session: N, note: '...' }` to `history` (no duplicate session entries, sorted ascending).
   - Add newly revealed `connections` using `reason:`.
   - Update `description` only when permanent world facts changed (never put pending party plans into `description`).
4) Never introduce `updatedInSessions`.
5) Run `npm run sync-check` (`npm run generate-list && npm run verify-session-sync -- --session latest && npm run build`).

Quality Gates
- `npm run sync-check` exits 0 with zero errors.
- `python3 -B scripts/transcription/validate_session_pipeline.py --session N` exits 0.
- Exports remain intact (`export const ...` and default export where present).
- Canonical spelling preserved (`Nites`, `Hyr` in stores / `Hýr` in prose, `Hýrda`, capitalized PC names).

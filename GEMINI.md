# GEMINI.md - Context & Instructions

## Project Overview
This is a **Vue 3 + Vite** application designed as a **Dungeons & Dragons Campaign Manager / Wiki**. It allows users to track the history, lore, locations, and characters of a D&D campaign. The application is data-driven, relying on structured JavaScript files to store world information, which is rendered dynamically.

## Architecture & Data Management

### Data Stores
The "database" consists of plain JavaScript files located in `src/store/`. These files export arrays of objects representing the world state.

*   `src/store/sessions.js`: Metadata about game sessions, including `homeRecap`, `nextSteps`, and `storyBeat` fields that drive `HomeView.vue` and `StorySoFarView.vue` directly.
*   `src/store/lore.js`: General world knowledge, history, and magic.
*   `src/store/locations.js`: Cities, landmarks, dungeons, and geography.
*   `src/store/npcs.js`: Non-player characters and their roles.
*   `src/store/characters.js`: Player characters (`Nyx`, `Ellara`, `Ysidor`, `Berridin`, `Witty`).
*   `src/store/worldData.js`: Unified entity index, bidirectional connection backlinks, and WikiLink resolver.
*   `src/store/config.js`: Utility logic to determine the "current" session and highlight newly updated content from `history`.

**Entity Data Format:**
Entities follow a **history-first** schema (do NOT add `updatedInSessions` — `history` is the single source of truth):
```javascript
{
  id: 'kebab-case-id',
  name: 'Display Name', // or 'term' for lore
  description: 'Short summary of what the entity is.',
  fullText: `Markdown content with [[WikiLinks]] support.`,
  history: [
    { session: 21, note: 'Concise one-sentence summary of what changed.' }
  ],
  connections: [
    { type: 'location', id: 'bastion-city', reason: 'Home base' } // always use `reason`, never `relationship`
  ]
}
```

**Session Data Format (`src/store/sessions.js`):**
```javascript
{
  id: 'session-21',
  title: 'Session 21',
  subtitle: 'Session Subtitle',
  location: 'Primary Locations',
  date: 'October 11, 2026',
  upcoming: false,
  summaryFile: 'session-21.md',
  description: 'Short card summary.',
  highlights: ['5–8 key bullet points'],
  homeRecap: 'Concise homepage "Where We Left Off" recap.',
  nextSteps: ['Concise homepage "What Comes Next" bullet(s).'],
  storyBeat: 'Narrative chronicle paragraph for The Story So Far.'
}
```

### Session Workflow
The canonical end-to-end pipeline from per-speaker audio to website + Ellara Campaign State is `scripts/transcription/run_session_auto.py` (documented in `AGENT_SESSION_PIPELINE.md`):
1.  **Audio -> Notes:** Transcribe (`gladia` + local Whisper), arbitrate with Gemini 4 Neon (`agy`), fuse, generate & audit `Raw Session N.md`, and produce polished `Session N.md`.
2.  **Website Sync:** Copy `Session N.md` into `src/assets/sessions/session-N.md`, update `src/store/sessions.js` (including `homeRecap`, `nextSteps`, `storyBeat`, and the `session-(N+1)` upcoming stub) and impacted world stores per `.copilot/prompts/process-latest-session.md`.
3.  **Ellara Campaign State (`ellara-state`):** Run `scripts/transcription/run_ellara_analysis_agent.py` against sibling `../ellara` (`Ellara/Campaign State/`) and verify with `check_session_delta.py --validate`.
4.  **Verification:** Run `npm run sync-check` (`generate-list` + `verify-session-sync` + `build`) and `scripts/transcription/validate_session_pipeline.py --session N`.

## Development

### Key Commands
*   `npm run dev`: Start the local development server (Vite).
*   `npm run build`: Build the application for production.
*   `npm run preview`: Preview the production build locally.
*   `npm run generate-list`: Regenerate `ENTITY_LIST.md` and `scripts/transcription/entity_metadata.json`.
*   `npm run sync-check`: Run `generate-list`, `verify-session-sync -- --session latest`, and `build`.
*   `python3 -B scripts/transcription/run_session_auto.py --session N --audio-dir <dir>`: Full automated session pipeline.

### Coding Standards
*   **Vue Components:** Use `<script setup>` syntax where appropriate.
*   **Styling:** Check `src/style.css` for global styles.
*   **IDs:** Always use **kebab-case** for entity IDs (e.g., `ancient-ruins`, `proctor-eduard`).
*   **Connections:** Always use `reason:` (never `relationship:`), pointing to valid entity IDs.
*   **Wiki Links:** Use `[[ID]]` or `[[ID|Display Text]]` for internal linking within descriptions/fullText.
*   **Exports:** Data files should use named exports (e.g., `export const lore = [...]`).

## Special Files
*   `AGENT_SESSION_PIPELINE.md`: Canonical runbook for the automated audio -> website -> Ellara pipeline.
*   `.copilot/prompts/process-latest-session.md`: Governing instructions for post-session website store updates.
*   `scripts/shared_sync_rules.json`: Shared canonical spelling and session-fact validation rules read by Python and JS validators.
*   `copilot-instructions.md`: Concise store schema and update rules for AI assistants.

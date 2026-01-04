# GEMINI.md - Context & Instructions

## Project Overview
This is a **Vue 3 + Vite** application designed as a **Dungeons & Dragons Campaign Manager / Wiki**. It allows users to track the history, lore, locations, and characters of a D&D campaign. The application is data-driven, relying on structured JavaScript files to store world information, which is rendered dynamically.

## Architecture & Data Management

### Data Stores
The "database" consists of plain JavaScript files located in `src/store/`. These files export arrays of objects representing the world state.

*   `src/store/lore.js`: General world knowledge, history, and magic.
*   `src/store/locations.js`: Cities, landmarks, dungeons, and geography.
*   `src/store/npcs.js`: Non-player characters and their roles.
*   `src/store/sessions.js`: Metadata about game sessions.
*   `src/store/config.js`: Utility logic to determine the "current" session and highlight new content.

**Data Format:**
Entities typically follow this schema:
```javascript
{
  id: 'kebab-case-id',
  name: 'Display Name', // or 'term' for lore
  description: 'Short summary.',
  fullText: `Markdown content with [[WikiLinks]] support.`,
  updatedInSessions: [1, 5], // Array of session numbers where this entity was modified
  history: [ // Optional granular history
     { session: 5, note: "Moved to Bastion City." }
  ],
  connections: [
    { type: 'location', id: 'bastion-city', reason: 'Home base' }
  ]
}
```

### Session Workflow
1.  **Session Notes:** Raw notes are written in Markdown files in `src/assets/sessions/` (e.g., `session-10.md`).
2.  **Data Updates:** After a session, the data stores (`lore.js`, `locations.js`, etc.) are updated to reflect new events, characters, and places. This is often assisted by AI prompts found in `.copilot/prompts/`.
3.  **Visualization:** The UI automatically highlights entities updated in the most recent session using the logic in `src/store/config.js`.

## Development

### Key Commands
*   `npm run dev`: Start the local development server (Vite).
*   `npm run build`: Build the application for production.
*   `npm run preview`: Preview the production build locally.

### Coding Standards
*   **Vue Components:** Use `<script setup>` syntax.
*   **Styling:** Check `src/style.css` for global styles.
*   **IDs:** Always use **kebab-case** for entity IDs (e.g., `ancient-ruins`, `captain-berridin`).
*   **Wiki Links:** Use `[[ID]]` or `[[ID|Display Text]]` for internal linking within descriptions.
*   **Exports:** Data files should use named exports (e.g., `export const lore = [...]`).

## Special Files
*   `copilot-instructions.md`: Detailed rules for AI assistants on how to parse session notes and update store files.
*   `TRANSCRIPTION_GUIDE.md` & `transcribe.py`: Tools for converting audio recordings of sessions into text.

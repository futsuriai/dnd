# Vue 3 + Vite

This template should help get you started developing with Vue 3 in Vite. The template uses Vue 3 `<script setup>` SFCs, check out the [script setup docs](https://v3.vuejs.org/api/sfc-script-setup.html#sfc-script-setup) to learn more.

Learn more about IDE Support for Vue in the [Vue Docs Scaling up Guide](https://vuejs.org/guide/scaling-up/tooling.html#ide-support).

## Updating world data after a session

We keep data in plain JS arrays so it’s easy to evolve:

- Lore: `src/store/lore.js`
- Locations: `src/store/locations.js`
- NPCs: `src/store/npcs.js`
- Session flag: `src/store/config.js` (current session is inferred automatically)

Steps each session:
1) Add your notes to `src/assets/sessions/session-<N>.md` (increment N)
2) Use Copilot with `.copilot/prompts/update-world-data.md` to generate a patch from your notes
3) Review and commit

Any entity with `updatedInSession: <N>` will render a small “New” badge in the UI.

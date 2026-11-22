'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const REPO_ROOT = path.resolve(__dirname, '..');

const ENTITY_STORE_FILES = [
  { name: 'lore.js', type: 'Lore', entityType: 'lore', exportName: 'lore' },
  { name: 'locations.js', type: 'Locations', entityType: 'location', exportName: 'locations' },
  { name: 'npcs.js', type: 'NPCs', entityType: 'npc', exportName: 'npcs' },
  { name: 'characters.js', type: 'Characters', entityType: 'character', exportName: 'characters' },
];

function stripModuleSyntax(content) {
  return content
    // Replace Vite glob expressions with empty objects for headless Node evaluation
    .replace(/import\.meta\.glob\([\s\S]*?\)/g, '({})')
    // Strip ES static import statements (single-line or multi-line)
    .replace(/^\s*import\s+[\s\S]*?from\s+['"][^'"]+['"];?\s*$/gm, '')
    .replace(/^\s*import\s+['"][^'"]+['"];?\s*$/gm, '')
    // Convert named exports to local declarations
    .replace(/\bexport\s+(const|let|var|function)\s+/g, '$1 ')
    // Strip re-export / export-list / default export statements
    .replace(/^\s*export\s+default\s+[\s\S]*?;?\s*$/gm, '')
    .replace(/^\s*export\s*\{[\s\S]*?\};?\s*$/gm, '');
}

/**
 * Safely evaluate a store module in an isolated VM context with console.warn muted
 * and stubbed asset helpers (e.g. avatars.js imports).
 *
 * @param {string} relativePath - Repo-relative path to a JS store file
 * @param {string[]} exportNames - List of top-level identifiers to extract
 * @param {string} [repoRoot]
 * @returns {Record<string, any>}
 */
function loadStoreExports(relativePath, exportNames, repoRoot = REPO_ROOT) {
  const fullPath = path.isAbsolute(relativePath)
    ? relativePath
    : path.join(repoRoot, relativePath);
  const rawContent = fs.readFileSync(fullPath, 'utf8');
  const transformed = stripModuleSyntax(rawContent);

  const context = {
    __exports: {},
    console: {
      log: () => {},
      info: () => {},
      warn: () => {},
      error: (...args) => console.error(...args),
    },
    // Safe stubs for avatar helper imports used by characters.js / npcs.js
    getAvatarUrl: () => null,
    getPortraitUrl: () => null,
    getCharacterAvatar: () => null,
    getCharacterPortrait: () => null,
  };

  const assignments = exportNames
    .map(
      (name) =>
        `__exports[${JSON.stringify(name)}] = typeof ${name} !== 'undefined' ? ${name} : undefined;`
    )
    .join('\n');

  vm.createContext(context);
  const script = new vm.Script(`${transformed}\n${assignments}`, {
    filename: relativePath,
  });
  script.runInContext(context);
  return context.__exports;
}

/**
 * Load a single exported array from a store module.
 *
 * @param {string} relativePath
 * @param {string} exportName
 * @param {string} [repoRoot]
 * @returns {any[]}
 */
function loadStoreArray(relativePath, exportName, repoRoot = REPO_ROOT) {
  const exportsObj = loadStoreExports(relativePath, [exportName], repoRoot);
  return exportsObj[exportName];
}

/**
 * Load all campaign data stores cleanly in one call.
 *
 * @param {string} [repoRoot]
 */
function loadAllEntityStores(repoRoot = REPO_ROOT) {
  const sessionExports = loadStoreExports(
    'src/store/sessions.js',
    ['sessions', 'storyPreamble'],
    repoRoot
  );
  return {
    lore: loadStoreArray('src/store/lore.js', 'lore', repoRoot) || [],
    locations: loadStoreArray('src/store/locations.js', 'locations', repoRoot) || [],
    npcs: loadStoreArray('src/store/npcs.js', 'npcs', repoRoot) || [],
    characters: loadStoreArray('src/store/characters.js', 'characters', repoRoot) || [],
    sessions: sessionExports.sessions || [],
    storyPreamble: sessionExports.storyPreamble,
  };
}

/**
 * Build canonical ENTITY_LIST.md and entity_metadata.json strings directly from stores.
 * Shared by generate_entity_list.js and verify_session_sync.js to prevent drift.
 *
 * @param {string} [repoRoot]
 * @returns {{ entityList: string, metadata: string, metadataArray: Array<object> }}
 */
function buildGeneratedEntityArtifacts(repoRoot = REPO_ROOT) {
  let entityList = '# World Entity List\n\nThis file is auto-generated. Do not edit manually.\n\n';
  const metadataArray = [];

  for (const file of ENTITY_STORE_FILES) {
    const relativePath = `src/store/${file.name}`;
    const absolutePath = path.join(repoRoot, relativePath);
    if (!fs.existsSync(absolutePath)) continue;

    const rawEntities = loadStoreArray(relativePath, file.exportName, repoRoot) || [];
    const entities = rawEntities
      .map((entity) => {
        const sessionSet = new Set(entity.updatedInSessions || []);
        if (Array.isArray(entity.history)) {
          entity.history.forEach((entry) => {
            if (entry && typeof entry.session === 'number') {
              sessionSet.add(entry.session);
            }
          });
        }

        return {
          id: entity.id,
          name: entity.name || entity.term,
          updatedInSessions: Array.from(sessionSet).sort((a, b) => a - b),
        };
      })
      .filter((entity) => entity.id && entity.name)
      .sort((a, b) => a.id.localeCompare(b.id));

    entityList += `## ${file.type}\n\n`;
    for (const entity of entities) {
      entityList += `- \`${entity.id}\`: ${entity.name}\n`;
      metadataArray.push({
        id: entity.id,
        name: entity.name,
        type: file.type,
        updatedInSessions: entity.updatedInSessions,
      });
    }
    entityList += '\n';
  }

  return {
    entityList,
    metadata: `${JSON.stringify(metadataArray, null, 2)}\n`,
    metadataArray,
  };
}

module.exports = {
  REPO_ROOT,
  ENTITY_STORE_FILES,
  loadStoreExports,
  loadStoreArray,
  loadAllEntityStores,
  buildGeneratedEntityArtifacts,
};

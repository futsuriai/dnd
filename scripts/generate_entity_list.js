import fs from 'fs';
import path from 'path';
import vm from 'vm';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Paths to data stores
const storePath = path.join(__dirname, '../src/store');
const outputFile = path.join(__dirname, '../ENTITY_LIST.md');

// Files to process
const files = [
  { name: 'lore.js', type: 'Lore', exportName: 'lore' },
  { name: 'locations.js', type: 'Locations', exportName: 'locations' },
  { name: 'npcs.js', type: 'NPCs', exportName: 'npcs' },
  { name: 'characters.js', type: 'Characters', exportName: 'characters' }
];

function loadEntitiesFromStore(content, exportName) {
  const transformed = content
    .replace(/import\.meta\.glob\([^)]*\)/g, '({})')
    .replace(new RegExp(`export\\s+const\\s+${exportName}\\s*=`), `const ${exportName} =`)
    .replace(new RegExp(`export\\s+default\\s+${exportName}\\s*;?`, 'g'), '');

  const context = {
    __entities: [],
    console: {
      log: () => {},
      warn: () => {},
      error: (...args) => console.error(...args),
    },
  };

  vm.createContext(context);
  const script = new vm.Script(`
${transformed}
__entities = ${exportName}
  .map((entity) => {
    const sessions = new Set(entity.updatedInSessions || []);
    if (Array.isArray(entity.history)) {
      entity.history.forEach(h => {
        if (h && typeof h.session === 'number') {
          sessions.add(h.session);
        }
      });
    }
    return {
      id: entity.id,
      name: entity.name || entity.term,
      updatedInSessions: Array.from(sessions).sort((a, b) => a - b)
    };
  })
  .filter((entity) => entity.id && entity.name);
`);
  script.runInContext(context);
  return context.__entities;
}

let output = '# World Entity List\n\nThis file is auto-generated. Do not edit manually.\n\n';
const metadata = [];

files.forEach(file => {
  const filePath = path.join(storePath, file.name);
  if (fs.existsSync(filePath)) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      
      const entities = loadEntitiesFromStore(content, file.exportName);
      
      output += '## ' + file.type + '\n\n';
      entities.sort((a, b) => a.id.localeCompare(b.id));
      
      entities.forEach(entity => {
        output += '- `' + entity.id + '`: ' + entity.name + '\n';
        metadata.push({
          id: entity.id,
          name: entity.name,
          type: file.type,
          updatedInSessions: entity.updatedInSessions
        });
      });
      output += '\n';
      
    } catch (err) {
      console.error('Error reading ' + file.name + ':', err);
    }
  } else {
    console.warn('File not found: ' + filePath);
  }
});

fs.writeFileSync(outputFile, output);
console.log('Entity list generated at ' + outputFile);

// Also write structured JSON metadata for weighting prompts in ASR
const metadataFile = path.join(__dirname, 'transcription/entity_metadata.json');
fs.writeFileSync(metadataFile, JSON.stringify(metadata, null, 2) + '\n');
console.log('Entity metadata JSON generated at ' + metadataFile);

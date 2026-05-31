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
  .map((entity) => ({ id: entity.id, name: entity.name || entity.term }))
  .filter((entity) => entity.id && entity.name);
`);
  script.runInContext(context);
  return context.__entities;
}

let output = '# World Entity List\n\nThis file is auto-generated. Do not edit manually.\n\n';

files.forEach(file => {
  const filePath = path.join(storePath, file.name);
  if (fs.existsSync(filePath)) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      
      const entities = loadEntitiesFromStore(content, file.exportName);
      
      output += '## ' + file.type + '\n\n';
      entities.sort((a, b) => a.id.localeCompare(b.id));
      
      entities.forEach(entity => {
        // Use concatenation to avoid nested template literal issues in tool calls
        output += '- `' + entity.id + '`: ' + entity.name + '\n';
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

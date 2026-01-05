import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Paths to data stores
const storePath = path.join(__dirname, '../src/store');
const outputFile = path.join(__dirname, '../ENTITY_LIST.md');

// Files to process
const files = [
  { name: 'lore.js', type: 'Lore' },
  { name: 'locations.js', type: 'Locations' },
  { name: 'npcs.js', type: 'NPCs' },
  { name: 'characters.js', type: 'Characters' }
];

let output = '# World Entity List\n\nThis file is auto-generated. Do not edit manually.\n\n';

files.forEach(file => {
  const filePath = path.join(storePath, file.name);
  if (fs.existsSync(filePath)) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      
      const entities = [];
      // Split by object start "{ id:" to find entries
      const objectChunks = content.split(/\{\s*id:/);
      
      // Skip the first chunk (file header)
      for (let i = 1; i < objectChunks.length; i++) {
        const chunk = 'id:' + objectChunks[i];
        
        const idMatch = /id:\s*['"]([^'"]+)['"]/.exec(chunk);
        const nameMatch = /(?:name|term):\s*['"]([^'"]+)['"]/.exec(chunk);
        
        if (idMatch && nameMatch) {
            entities.push({
                id: idMatch[1],
                name: nameMatch[1]
            });
        }
      }
      
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
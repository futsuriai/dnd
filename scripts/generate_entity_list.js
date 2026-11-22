import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';

const require = createRequire(import.meta.url);
const { REPO_ROOT, buildGeneratedEntityArtifacts } = require('./store_loader.cjs');

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const outputFile = path.join(REPO_ROOT, 'ENTITY_LIST.md');
const metadataFile = path.join(__dirname, 'transcription/entity_metadata.json');

function writeIfChanged(filePath, content) {
  if (fs.existsSync(filePath)) {
    const existing = fs.readFileSync(filePath, 'utf8');
    if (existing === content) {
      return false;
    }
  }
  fs.writeFileSync(filePath, content);
  return true;
}

const { entityList, metadata } = buildGeneratedEntityArtifacts(REPO_ROOT);

writeIfChanged(outputFile, entityList);
console.log('Entity list generated at ' + outputFile);

writeIfChanged(metadataFile, metadata);
console.log('Entity metadata JSON generated at ' + metadataFile);

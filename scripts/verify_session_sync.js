#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import vm from 'vm';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..');

const args = process.argv.slice(2);

function argValue(name, fallback = null) {
  const index = args.indexOf(name);
  if (index === -1) return fallback;
  return args[index + 1] ?? fallback;
}

const sessionArg = argValue('--session', 'latest');
const skipHome = args.includes('--skip-home-override');
const skipStory = args.includes('--skip-story-stage');
const skipGeneratedDrift = args.includes('--skip-generated-drift');

const errors = [];
const warnings = [];

function ok(message) {
  console.log(`OK: ${message}`);
}

function warn(message) {
  warnings.push(message);
  console.warn(`WARN: ${message}`);
}

function error(message) {
  errors.push(message);
  console.error(`ERROR: ${message}`);
}

function readText(relativePath) {
  return fs.readFileSync(path.join(repoRoot, relativePath), 'utf8');
}

function listSessionMarkdownNumbers() {
  const dir = path.join(repoRoot, 'src/assets/sessions');
  return fs.readdirSync(dir)
    .map((name) => {
      const match = name.match(/^session-(\d+)\.md$/);
      return match ? Number.parseInt(match[1], 10) : null;
    })
    .filter(Number.isFinite)
    .sort((a, b) => a - b);
}

function loadExportedArray(relativePath, exportName) {
  const content = readText(relativePath)
    .replace(/import\.meta\.glob\([^)]*\)/g, '({})')
    .replace(new RegExp(`export\\s+const\\s+${exportName}\\s*=`), `const ${exportName} =`)
    .replace(new RegExp(`export\\s+default\\s+${exportName}\\s*;?`, 'g'), '');
  const context = { __value: null, console };
  vm.createContext(context);
  const script = new vm.Script(`${content}\n__value = ${exportName};`);
  script.runInContext(context);
  return context.__value;
}

const generatedEntityFiles = [
  { name: 'lore.js', type: 'Lore', exportName: 'lore' },
  { name: 'locations.js', type: 'Locations', exportName: 'locations' },
  { name: 'npcs.js', type: 'NPCs', exportName: 'npcs' },
  { name: 'characters.js', type: 'Characters', exportName: 'characters' },
];

function buildGeneratedEntityArtifacts() {
  let list = '# World Entity List\n\nThis file is auto-generated. Do not edit manually.\n\n';
  const metadata = [];

  for (const file of generatedEntityFiles) {
    const relativePath = `src/store/${file.name}`;
    const absolutePath = path.join(repoRoot, relativePath);
    if (!fs.existsSync(absolutePath)) continue;

    const entities = loadExportedArray(relativePath, file.exportName)
      .map((entity) => {
        const sessions = new Set(entity.updatedInSessions || []);
        if (Array.isArray(entity.history)) {
          entity.history.forEach((entry) => {
            if (entry && typeof entry.session === 'number') {
              sessions.add(entry.session);
            }
          });
        }

        return {
          id: entity.id,
          name: entity.name || entity.term,
          updatedInSessions: Array.from(sessions).sort((a, b) => a - b),
        };
      })
      .filter((entity) => entity.id && entity.name)
      .sort((a, b) => a.id.localeCompare(b.id));

    list += `## ${file.type}\n\n`;
    for (const entity of entities) {
      list += `- \`${entity.id}\`: ${entity.name}\n`;
      metadata.push({
        id: entity.id,
        name: entity.name,
        type: file.type,
        updatedInSessions: entity.updatedInSessions,
      });
    }
    list += '\n';
  }

  return {
    entityList: list,
    metadata: `${JSON.stringify(metadata, null, 2)}\n`,
  };
}

function checkBadPatterns(relativePath) {
  if (!fs.existsSync(path.join(repoRoot, relativePath))) return;
  const text = readText(relativePath);
  const checks = [
    [/\bNýtes\b|\bNytes\b/g, 'Use canonical spelling `Nites`, not `Nýtes` or `Nytes`.'],
    [/\bHirotera\b/g, 'Use canonical spelling `Hieroterra`.'],
    [/Ardwin,\s+the\s+Black\s+Swan/gi, 'Ardwin is the blacksmith, not the Black Swan.'],
    [/Ellara asked if .*Jacinta/gi, 'Verify this likely means Nites, not Jacinta.'],
    [/\bH[ýy]r\b[^.\n]{0,140}\bJacinta\b|\bJacinta\b[^.\n]{0,140}\bH[ýy]r\b/gi, 'In the Session 17 Hýr/static beat, verify this means Nites or the unknown censored birth name, not Jacinta.'],
    [/\b(?:static|censorship)\b[^\n]{0,220}\bBerridin\b[^\n]{0,120}\b(?:Arcana\s+natural\s+20|natural\s+20\s+Arcana)\b|\bBerridin\b[^\n]{0,120}\b(?:Arcana\s+natural\s+20|natural\s+20\s+Arcana)\b[^\n]{0,220}\b(?:static|censorship|world-scale|world scale|H[ýy]r)\b|\bBerridin['’]s\b[^\n]{0,80}\bnatural\s+20\s+Arcana\b[^\n]{0,220}\b(?:static|censorship|world-scale|world scale|H[ýy]r)\b|\bBerridin\s+remembered\s+hearing\s+it\b|\bvoice\s+was\s+not\s+new\s+to\s+Berridin\b/gi, 'Session 17 Hýr/static-name Arcana natural 20 and familiar-voice realization belong to Nyx, not Berridin.'],
    [/Session\s+\d+:\s+[a-z]/g, 'A public recap appears to lowercase a sentence-leading proper noun.'],
    [/By the end,\s+[a-z]/g, 'A generic recap ending appears to lowercase a sentence-leading proper noun.'],
  ];

  for (const [pattern, message] of checks) {
    for (const match of text.matchAll(pattern)) {
      const line = text.slice(0, match.index).split('\n').length;
      error(`${relativePath}:${line}: ${message} Found \`${match[0]}\`.`);
    }
  }
}

function countQuotedStrings(arrayText) {
  if (!arrayText) return 0;
  return [...arrayText.matchAll(/'[^']+'|"[^"]+"/g)].length;
}

function checkSessionIndex(session) {
  const sessions = loadExportedArray('src/store/sessions.js', 'sessions');
  const completed = sessions.filter((item) => item.id === `session-${session}`);
  if (completed.length !== 1) {
    error(`src/store/sessions.js should contain exactly one session-${session} object; found ${completed.length}`);
    return;
  }

  const item = completed[0];
  if (item.upcoming !== false) error(`session-${session} should have upcoming: false`);
  if (item.summaryFile !== `session-${session}.md`) error(`session-${session} should reference summaryFile: 'session-${session}.md'`);
  if (!item.description || /placeholder|tbd/i.test(item.description)) error(`session-${session} needs a real description`);
  if (!Array.isArray(item.highlights) || item.highlights.length < 5 || item.highlights.length > 10) {
    error(`session-${session} should have 5-10 highlights`);
  }

  const upcoming = sessions.filter((candidate) => candidate.upcoming === true);
  if (upcoming.length !== 1) {
    error(`there should be exactly one upcoming session; found ${upcoming.length}`);
  } else {
    const next = upcoming[0];
    if (next.id !== `session-${session + 1}`) error(`upcoming session should be session-${session + 1}, found ${next.id}`);
    if (sessions[0] !== next) error(`upcoming session-${session + 1} should be first in sessions.js`);
    if (Array.isArray(next.highlights) && next.highlights.length !== 0) error(`upcoming session-${session + 1} should have empty highlights`);
    if (!next.description || /placeholder|tbd/i.test(next.description)) error(`upcoming session-${session + 1} needs a non-placeholder description`);
  }

  for (const candidate of sessions) {
    if (candidate.upcoming === false && candidate.summaryFile) {
      const summaryPath = path.join(repoRoot, 'src/assets/sessions', candidate.summaryFile);
      if (!fs.existsSync(summaryPath)) {
        error(`${candidate.id} summaryFile does not exist: ${candidate.summaryFile}`);
      }
    }
  }
  ok(`session index contains completed session-${session} and upcoming session-${session + 1}`);
}

function checkViewCoverage(session) {
  const home = readText('src/views/HomeView.vue');
  if (!skipHome) {
    const recapBlock = home.match(/const HOME_RECAP_BY_SESSION = \{[\s\S]*?\n\};/)?.[0] || '';
    const nextBlock = home.match(/const HOME_NEXT_STEPS_BY_SESSION = \{[\s\S]*?\n\};/)?.[0] || '';
    if (!new RegExp(`\\b${session}\\s*:`).test(recapBlock)) {
      warn(`HomeView.vue has no HOME_RECAP_BY_SESSION override for session ${session}`);
    }
    if (!new RegExp(`\\b${session}\\s*:`).test(nextBlock)) {
      warn(`HomeView.vue has no HOME_NEXT_STEPS_BY_SESSION override for session ${session}`);
    }
  }

  if (!skipStory) {
    const story = readText('src/views/StorySoFarView.vue');
    if (!new RegExp(`minSession:\\s*${session}\\b`).test(story)) {
      warn(`StorySoFarView.vue has no BACK_OF_BOOK_STAGES paragraph for session ${session}`);
    }
  }
}

function checkGeneratedDrift() {
  if (skipGeneratedDrift) return;
  const expected = buildGeneratedEntityArtifacts();
  const actualEntityList = readText('ENTITY_LIST.md');
  const actualMetadata = readText('scripts/transcription/entity_metadata.json');

  if (actualEntityList !== expected.entityList || actualMetadata !== expected.metadata) {
    error('ENTITY_LIST.md or entity_metadata.json is stale; run `npm run generate-list` and review the result');
  } else {
    ok('generated entity list and metadata match the current stores');
  }
}

function checkScratchArtifacts(session) {
  const sessionAssets = path.join(repoRoot, 'src/assets/sessions');
  const scratchPatterns = [
    /^Raw Session .*Candidate\.md$/,
    /Reconciled Candidate/i,
    /\.tmp$/,
    /\.bak$/,
    / bkp\./i,
  ];
  for (const name of fs.readdirSync(sessionAssets)) {
    if (scratchPatterns.some((pattern) => pattern.test(name))) {
      error(`scratch artifact should not be in website session assets: ${name}`);
    }
  }

  const transcriptsDir = path.join(sessionAssets, 'transcripts');
  if (!fs.existsSync(transcriptsDir)) return;
  const currentTranscriptDir = `Session ${session}`;
  const currentTranscriptLeak = new RegExp(`^session_${session}_.+\\.(txt|json)$`);
  for (const name of fs.readdirSync(transcriptsDir)) {
    if (name === currentTranscriptDir) {
      error(`current-session transcript artifact should not be bundled unless intentionally exposed: src/assets/sessions/transcripts/${name}`);
    }
    if (currentTranscriptLeak.test(name)) {
      error(`current-session transcript artifact should not be bundled unless intentionally exposed: src/assets/sessions/transcripts/${name}`);
    }
  }
}

const sessionNumbers = listSessionMarkdownNumbers();
if (!sessionNumbers.length) {
  error('No src/assets/sessions/session-*.md files found');
}

const latest = sessionNumbers.at(-1);
const session = sessionArg === 'latest' ? latest : Number.parseInt(sessionArg, 10);
if (!Number.isFinite(session)) {
  error(`Invalid --session value: ${sessionArg}`);
}

if (Number.isFinite(session)) {
  if (session !== latest) {
    warn(`validating session ${session}, but latest markdown session is ${latest}`);
  }
  const latestFile = path.join(repoRoot, 'src/assets/sessions', `session-${session}.md`);
  if (!fs.existsSync(latestFile)) {
    error(`missing website session markdown: src/assets/sessions/session-${session}.md`);
  } else {
    const content = fs.readFileSync(latestFile, 'utf8');
    if (!content.trim()) error(`website session markdown is empty: session-${session}.md`);
    ok(`website session markdown exists for session-${session}`);
  }

  checkSessionIndex(session);
  checkViewCoverage(session);
  checkScratchArtifacts(session);
  checkGeneratedDrift();

  [
    `src/assets/sessions/session-${session}.md`,
    'src/views/HomeView.vue',
    'src/views/StorySoFarView.vue',
    'src/store/sessions.js',
    'src/store/locations.js',
    'src/store/lore.js',
    'src/store/npcs.js',
    'ENTITY_LIST.md',
    'scripts/transcription/entity_metadata.json',
  ].forEach(checkBadPatterns);
}

console.log();
console.log(`Session sync verification complete: ${errors.length} error(s), ${warnings.length} warning(s).`);
process.exit(errors.length ? 1 : 0);

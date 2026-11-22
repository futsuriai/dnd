#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';

const require = createRequire(import.meta.url);
const {
  REPO_ROOT,
  loadAllEntityStores,
  buildGeneratedEntityArtifacts,
} = require('./store_loader.cjs');

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = REPO_ROOT;

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
const strictTranscripts = args.includes('--strict-transcripts');

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
  return fs
    .readdirSync(dir)
    .map((name) => {
      const match = name.match(/^session-(\d+)\.md$/);
      return match ? Number.parseInt(match[1], 10) : null;
    })
    .filter(Number.isFinite)
    .sort((a, b) => a - b);
}

// Built-in fallback rules when scripts/shared_sync_rules.json is not yet present
const BUILTIN_SYNC_RULES = {
  badPublicPatterns: [
    {
      pattern: '\\bNýtes\\b|\\bNytes\\b',
      flags: 'g',
      message: 'Use canonical spelling `Nites`, not `Nýtes` or `Nytes`.',
    },
    {
      pattern: '\\bMarie\\b',
      flags: 'g',
      message: 'Use canonical spelling `Meri`, not `Marie`.',
    },
    {
      pattern: '\\b(?:Mara|Illaoi|Bigilar)\\b',
      flags: 'g',
      message:
        'Unrecognized ASR-like character name; use the canonical entity name or add a real entity before publishing.',
    },
    {
      pattern: '\\b(?:Stongalais|Stonegull(?:\\s+eyes?)?)\\b',
      flags: 'gi',
      message:
        'Use canonical phrase `stone goliaths`, not ASR variants like `Stongalais` or `Stonegull eyes`.',
    },
    {
      pattern: '\\bHirotera\\b',
      flags: 'g',
      message: 'Use canonical spelling `Hieroterra`.',
    },
    {
      pattern: 'Ardwin,\\s+the\\s+Black\\s+Swan',
      flags: 'gi',
      message: 'Ardwin is the blacksmith, not the Black Swan.',
    },
    {
      pattern: 'Is there any books|comically long fuse|tasted the freedom|Mom,\\s+not like Jeeves',
      flags: 'gi',
      message:
        'Polished public copy preserved a known awkward ASR/direct-transcript phrase; paraphrase or clean it before publishing.',
    },
    {
      pattern: 'Ellara asked if .*Jacinta',
      flags: 'gi',
      message: 'Verify this likely means Nites, not Jacinta.',
    },
    {
      pattern: 'Session\\s+\\d+:\\s+[a-z]',
      flags: 'g',
      message: 'A public recap appears to lowercase a sentence-leading proper noun.',
    },
    {
      pattern: 'By the end,\\s+[a-z]',
      flags: 'g',
      message: 'A generic recap ending appears to lowercase a sentence-leading proper noun.',
    },
  ],
  sessionSpecificRules: {
    '17': [
      {
        pattern: '\\bH[ýy]r\\b[^.\\n]{0,140}\\bJacinta\\b|\\bJacinta\\b[^.\\n]{0,140}\\bH[ýy]r\\b',
        flags: 'gi',
        message:
          'In the Session 17 Hýr/static beat, verify this means Nites or the unknown censored birth name, not Jacinta.',
      },
      {
        pattern:
          '\\b(?:static|censorship)\\b[^\\n]{0,220}\\bBerridin\\b[^\\n]{0,120}\\b(?:Arcana\\s+natural\\s+20|natural\\s+20\\s+Arcana)\\b|\\bBerridin\\b[^\\n]{0,120}\\b(?:Arcana\\s+natural\\s+20|natural\\s+20\\s+Arcana)\\b[^\\n]{0,220}\\b(?:static|censorship|world-scale|world scale|H[ýy]r)\\b|\\bBerridin[\'’]s\\b[^\\n]{0,80}\\bnatural\\s+20\\s+Arcana\\b[^\\n]{0,220}\\b(?:static|censorship|world-scale|world scale|H[ýy]r)\\b|\\bBerridin\\s+remembered\\s+hearing\\s+it\\b|\\bvoice\\s+was\\s+not\\s+new\\s+to\\s+Berridin\\b',
        flags: 'gi',
        message:
          'Session 17 Hýr/static-name Arcana natural 20 and familiar-voice realization belong to Nyx, not Berridin.',
      },
    ],
  },
};

function loadSyncRules() {
  const rulesPath = path.join(__dirname, 'shared_sync_rules.json');
  if (fs.existsSync(rulesPath)) {
    try {
      const parsed = JSON.parse(fs.readFileSync(rulesPath, 'utf8'));
      if (parsed && typeof parsed === 'object') {
        return { source: 'scripts/shared_sync_rules.json', rules: parsed };
      }
    } catch (err) {
      warn(`failed to parse scripts/shared_sync_rules.json (${err.message}); using built-in rules`);
    }
  }
  return { source: 'built-in fallback', rules: BUILTIN_SYNC_RULES };
}

function compileRuleEntries(rulesConfig) {
  const entries = [];
  const pushRule = (rule) => {
    if (!rule || !rule.pattern || !rule.message) return;
    const rawFlags = typeof rule.flags === 'string' ? rule.flags : 'g';
    const flags = rawFlags.includes('g') ? rawFlags : `${rawFlags}g`;
    entries.push([new RegExp(rule.pattern, flags), rule.message]);
  };

  if (Array.isArray(rulesConfig.badPublicPatterns)) {
    rulesConfig.badPublicPatterns.forEach(pushRule);
  }
  if (rulesConfig.sessionSpecificRules && typeof rulesConfig.sessionSpecificRules === 'object') {
    for (const group of Object.values(rulesConfig.sessionSpecificRules)) {
      if (Array.isArray(group)) {
        group.forEach(pushRule);
      }
    }
  }
  return entries;
}

function checkBadPatterns(relativePath, compiledChecks) {
  if (!fs.existsSync(path.join(repoRoot, relativePath))) return;
  const text = readText(relativePath);

  for (const [pattern, message] of compiledChecks) {
    pattern.lastIndex = 0;
    for (const match of text.matchAll(pattern)) {
      const line = text.slice(0, match.index).split('\n').length;
      error(`${relativePath}:${line}: ${message} Found \`${match[0]}\`.`);
    }
  }
}

function checkSessionIndex(session, stores) {
  const { sessions, storyPreamble } = stores;

  if (typeof storyPreamble !== 'string' || !storyPreamble.trim()) {
    error('src/store/sessions.js must export a non-empty `storyPreamble` string');
  }

  const completed = sessions.filter((item) => item.id === `session-${session}`);
  if (completed.length !== 1) {
    error(
      `src/store/sessions.js should contain exactly one session-${session} object; found ${completed.length}`
    );
    return;
  }

  const item = completed[0];
  if (item.upcoming !== false) error(`session-${session} should have upcoming: false`);
  if (item.summaryFile !== `session-${session}.md`) {
    error(`session-${session} should reference summaryFile: 'session-${session}.md'`);
  }
  if (!item.description || /placeholder|tbd/i.test(item.description)) {
    error(`session-${session} needs a real description`);
  }
  if (!Array.isArray(item.highlights) || item.highlights.length < 5 || item.highlights.length > 10) {
    error(`session-${session} should have 5-10 highlights`);
  }

  // Session-driven HomeView & StorySoFarView fields (no brittle Vue view regexes)
  if (!skipHome) {
    if (typeof item.homeRecap !== 'string' || !item.homeRecap.trim()) {
      warn(`src/store/sessions.js session-${session} has no homeRecap (HomeView will fall back to description)`);
    }
    if (!Array.isArray(item.nextSteps) || item.nextSteps.length === 0) {
      warn(`src/store/sessions.js session-${session} has no nextSteps array for HomeView`);
    }
  }

  if (!skipStory) {
    if (typeof item.storyBeat !== 'string' || !item.storyBeat.trim()) {
      warn(`src/store/sessions.js session-${session} has no storyBeat (StorySoFarView will fall back to description)`);
    }
  }

  // Validate schema consistency across all sessions
  const seenDescriptions = new Map();
  for (const candidate of sessions) {
    if (typeof candidate.upcoming !== 'boolean') {
      error(`src/store/sessions.js ${candidate.id} is missing boolean \`upcoming\` field`);
    }
    if (candidate.homeRecap !== undefined && (typeof candidate.homeRecap !== 'string' || !candidate.homeRecap.trim())) {
      error(`src/store/sessions.js ${candidate.id} has invalid \`homeRecap\` (must be non-empty string)`);
    }
    if (candidate.storyBeat !== undefined && (typeof candidate.storyBeat !== 'string' || !candidate.storyBeat.trim())) {
      error(`src/store/sessions.js ${candidate.id} has invalid \`storyBeat\` (must be non-empty string)`);
    }
    if (candidate.nextSteps !== undefined) {
      const validSteps =
        Array.isArray(candidate.nextSteps) &&
        candidate.nextSteps.every((step) => typeof step === 'string' && step.trim().length > 0);
      if (!validSteps) {
        error(`src/store/sessions.js ${candidate.id} has invalid \`nextSteps\` (must be string[])`);
      }
    }

    if (typeof candidate.description === 'string' && candidate.description.trim()) {
      const normalizedDesc = candidate.description.trim().toLowerCase().replace(/\s+/g, ' ');
      if (seenDescriptions.has(normalizedDesc)) {
        error(
          `src/store/sessions.js duplicate session description shared by ${seenDescriptions.get(normalizedDesc)} and ${candidate.id}`
        );
      } else {
        seenDescriptions.set(normalizedDesc, candidate.id);
      }
    }

    if (candidate.upcoming === false && candidate.summaryFile) {
      const summaryPath = path.join(repoRoot, 'src/assets/sessions', candidate.summaryFile);
      if (!fs.existsSync(summaryPath)) {
        error(`${candidate.id} summaryFile does not exist: ${candidate.summaryFile}`);
      }
    }

    if (candidate.transcriptFile) {
      const transcriptPath = path.join(
        repoRoot,
        'src/assets/sessions/transcripts',
        candidate.transcriptFile
      );
      if (!fs.existsSync(transcriptPath)) {
        error(`${candidate.id} transcriptFile does not exist: ${candidate.transcriptFile}`);
      } else if (!/^session_\d+_corrected\.txt$/.test(candidate.transcriptFile)) {
        error(
          `${candidate.id} transcriptFile '${candidate.transcriptFile}' does not match published pattern session_*_corrected.txt`
        );
      }
    }
  }

  const upcoming = sessions.filter((candidate) => candidate.upcoming === true);
  if (upcoming.length !== 1) {
    error(`there should be exactly one upcoming session; found ${upcoming.length}`);
  } else {
    const next = upcoming[0];
    if (next.id !== `session-${session + 1}`) {
      error(`upcoming session should be session-${session + 1}, found ${next.id}`);
    }
    if (sessions[0] !== next) {
      error(`upcoming session-${session + 1} should be first in sessions.js`);
    }
    if (Array.isArray(next.highlights) && next.highlights.length !== 0) {
      error(`upcoming session-${session + 1} should have empty highlights`);
    }
    if (!next.description || /placeholder|tbd/i.test(next.description)) {
      error(`upcoming session-${session + 1} needs a non-placeholder description`);
    }
  }

  ok(`session index validated (completed session-${session}, upcoming session-${session + 1}, storyPreamble, unique descriptions)`);
}

function checkStoreIntegrity(stores) {
  const storeMap = {
    character: { file: 'src/store/characters.js', list: stores.characters },
    npc: { file: 'src/store/npcs.js', list: stores.npcs },
    location: { file: 'src/store/locations.js', list: stores.locations },
    lore: { file: 'src/store/lore.js', list: stores.lore },
    session: { file: 'src/store/sessions.js', list: stores.sessions },
  };

  // 1. Duplicate entity IDs within any store
  const idIndex = {};
  for (const [type, { file, list }] of Object.entries(storeMap)) {
    const seen = new Set();
    for (const entity of list) {
      if (!entity || !entity.id) {
        error(`${file} contains an entity missing \`id\``);
        continue;
      }
      if (seen.has(entity.id)) {
        error(`${file} contains duplicate entity id \`${entity.id}\``);
      }
      seen.add(entity.id);
    }
    idIndex[type] = seen;
  }

  // 2. Connection integrity (valid type, existing target id, reason vs relationship)
  const validTargetTypes = new Set(Object.keys(storeMap));
  for (const [sourceType, { file, list }] of Object.entries(storeMap)) {
    if (sourceType === 'session') continue;
    for (const entity of list) {
      if (!Array.isArray(entity.connections)) continue;
      for (const conn of entity.connections) {
        if (!conn || typeof conn !== 'object') {
          error(`${file} (${entity.id}) has malformed connection entry`);
          continue;
        }
        if ('relationship' in conn) {
          error(
            `${file} (${entity.id} -> ${conn.type}:${conn.id}) uses disallowed \`relationship:\` key; use \`reason:\` instead`
          );
        }
        if (!conn.reason || typeof conn.reason !== 'string' || !conn.reason.trim()) {
          error(`${file} (${entity.id} -> ${conn.type}:${conn.id}) is missing a non-empty \`reason:\` label`);
        }
        if (!validTargetTypes.has(conn.type)) {
          error(`${file} (${entity.id}) has connection with invalid type \`${conn.type}\` (id: \`${conn.id}\`)`);
        } else if (!idIndex[conn.type].has(conn.id)) {
          error(`${file} (${entity.id}) has broken connection to missing ${conn.type} \`${conn.id}\``);
        }
      }
    }
  }

  // 3. Orphan locations not reachable on /locations or /bastion-city
  const worldLocationTypes = new Set([
    'empire',
    'province',
    'capital',
    'city',
    'town',
    'village',
    'dungeon',
    'poi',
    'landmark',
    'tavern',
  ]);
  const provinceIds = new Set(
    stores.locations.filter((loc) => loc && loc.type === 'province').map((loc) => loc.id)
  );
  for (const loc of stores.locations) {
    const onBastionPage =
      loc.id === 'bastion-city' ||
      (Array.isArray(loc.tags) && loc.tags.includes('bastion city')) ||
      (Array.isArray(loc.connections) &&
        loc.connections.some((c) => c && c.type === 'location' && c.id === 'bastion-city'));
    const onLocationsPage =
      worldLocationTypes.has(loc.type) ||
      (Array.isArray(loc.connections) &&
        loc.connections.some((c) => c && c.type === 'location' && provinceIds.has(c.id)));
    if (!onBastionPage && !onLocationsPage) {
      error(
        `src/store/locations.js orphan location \`${loc.id}\` (type: \`${loc.type}\`) is not reachable on /locations or /bastion-city`
      );
    }
  }

  // 4. prominence: 'minor' hiding fullText
  for (const npc of stores.npcs) {
    if (npc.prominence === 'minor' && typeof npc.fullText === 'string' && npc.fullText.trim()) {
      error(
        `src/store/npcs.js NPC \`${npc.id}\` has \`prominence: 'minor'\` while defining \`fullText\`, hiding major content`
      );
    }
  }

  // 5. Unresolved [[WikiLink]] targets across entity fullText/description/bio
  checkWikiLinks(stores, idIndex);

  ok('store integrity validated (unique IDs, connections, locations, NPC prominence, WikiLinks)');
}

function slugifyTarget(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/['’"]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

const HISTORY_PAGE_SLUGS = new Set([
  'timeline-of-the-world',
  'world-history',
  'timeline',
  'history',
]);

const WIKILINK_ALIASES = {
  'light-crystal': ['lore', 'light-crystals'],
  'light-crystals': ['lore', 'light-crystals'],
  'shadowed': ['lore', 'curse-shadowed'],
  'the-shadowed': ['lore', 'curse-shadowed'],
  'eulogia': ['lore', 'eulogia-eternal-light'],
  'the-eulogia': ['lore', 'eulogia-eternal-light'],
  'eulogia-of-the-eternal-light': ['lore', 'eulogia-eternal-light'],
  'hariolar-empire': ['location', 'hariolar-empire'],
  'the-hariolar-empire': ['location', 'hariolar-empire'],
  'hyrda': ['location', 'hyrta'],
  'hyrda-mines': ['location', 'hyrta-mines'],
  'hyrda-ducal-encampment': ['location', 'hyrta-ducal-encampment'],
  'lighthouse': ['location', 'duskbreaker-lighthouse'],
  'the-lighthouse': ['location', 'duskbreaker-lighthouse'],
  'eternal-light': ['lore', 'eternal-light'],
  'the-eternal-light': ['lore', 'eternal-light'],
  'first-emperor': ['lore', 'first-emperor'],
  'the-first-emperor': ['lore', 'first-emperor'],
  'lightkeepers': ['lore', 'lightkeepers'],
  'the-lightkeepers': ['lore', 'lightkeepers'],
  'black-swan': ['lore', 'black-swan'],
  'the-black-swan': ['lore', 'black-swan'],
  'great-cataclysm': ['lore', 'great-cataclysm'],
  'the-great-cataclysm': ['lore', 'great-cataclysm'],
  'pilgrimage-of-the-enlightened': ['lore', 'pilgrimage-enlightened'],
  'the-pilgrimage-of-the-enlightened': ['lore', 'pilgrimage-enlightened'],
  'the-static': ['lore', 'the-static'],
  'static': ['lore', 'the-static'],
  'warforged': ['lore', 'warforged'],
  'warforged-construct': ['lore', 'warforged'],
  'warforged-constructs': ['lore', 'warforged'],
  'whitaker-family': ['lore', 'whitaker-family'],
  'whitaker-brothers': ['lore', 'whitaker-family'],
  'the-whitaker-brothers': ['lore', 'whitaker-family'],
  'lord-whitaker-6th': ['character', 'witty'],
  'lord-whitaker-the-6th': ['character', 'witty'],
  'tsinyra': ['npc', 'tsinyra'],
  'tsi-nyra': ['npc', 'tsinyra'],
  'eduard': ['npc', 'proctor-eduard'],
  'director-reeves': ['npc', 'donnathan-reeves'],
  'viscount-sommeil': ['npc', 'donnathan-reeves'],
  'reeves': ['npc', 'donnathan-reeves'],
  'director-faberge': ['npc', 'michelle-faberge'],
  'faberge': ['npc', 'michelle-faberge'],
  'grand-duke-valerian-oliander': ['npc', 'duke-valerian-oliander'],
  'lady-ophelia': ['npc', 'lady-ophelia-xanteres-oliander'],
};

function canResolveWikiLink(rawInner, stores, idIndex) {
  const pipeIdx = rawInner.indexOf('|');
  const targetPart = (pipeIdx !== -1 ? rawInner.slice(0, pipeIdx) : rawInner).trim();
  const hashIdx = targetPart.indexOf('#');
  const pagePartRaw = (hashIdx !== -1 ? targetPart.slice(0, hashIdx) : targetPart).trim();
  const pageSegment = pagePartRaw.includes('/')
    ? pagePartRaw.split('/').pop().trim()
    : pagePartRaw;
  const slug = slugifyTarget(pageSegment);
  if (!slug) return false;
  if (HISTORY_PAGE_SLUGS.has(slug)) return true;

  const stripThe = (s) => (s.startsWith('the-') ? s.slice(4) : s);
  const alias = WIKILINK_ALIASES[slug] || WIKILINK_ALIASES[stripThe(slug)];
  if (alias && idIndex[alias[0]]?.has(alias[1])) return true;

  const candidates = new Set([slug, stripThe(slug)]);
  if (slug.endsWith('s') && slug.length > 3) candidates.add(slug.slice(0, -1));
  else candidates.add(`${slug}s`);

  const allCollections = [
    ['character', stores.characters],
    ['npc', stores.npcs],
    ['location', stores.locations],
    ['lore', stores.lore],
    ['session', stores.sessions],
  ];

  for (const [type, list] of allCollections) {
    for (const entity of list) {
      if (!entity || !entity.id) continue;
      if (candidates.has(entity.id.toLowerCase())) return true;
      const rawName = type === 'lore' ? entity.term : type === 'session' ? entity.title : entity.name;
      const nameSlug = slugifyTarget(rawName);
      if (candidates.has(nameSlug) || candidates.has(stripThe(nameSlug))) return true;
    }
  }
  return false;
}

function checkWikiLinks(stores, idIndex) {
  const targets = [
    ['src/store/lore.js', stores.lore],
    ['src/store/locations.js', stores.locations],
    ['src/store/npcs.js', stores.npcs],
    ['src/store/characters.js', stores.characters],
    ['src/store/sessions.js', stores.sessions],
  ];

  for (const [file, list] of targets) {
    for (const entity of list) {
      for (const field of ['description', 'fullText', 'bio']) {
        const value = entity[field];
        if (typeof value !== 'string' || !value.includes('[[')) continue;
        for (const match of value.matchAll(/\[\[([^\]]+)\]\]/g)) {
          const inner = match[1];
          if (!canResolveWikiLink(inner, stores, idIndex)) {
            error(`${file} (${entity.id}.${field}): unresolved WikiLink \`[[${inner}]]\``);
          }
        }
      }
    }
  }
}

function checkGeneratedDrift() {
  if (skipGeneratedDrift) return;
  const expected = buildGeneratedEntityArtifacts(repoRoot);
  const actualEntityList = readText('ENTITY_LIST.md');
  const actualMetadata = readText('scripts/transcription/entity_metadata.json');

  if (actualEntityList !== expected.entityList || actualMetadata !== expected.metadata) {
    error(
      'ENTITY_LIST.md or entity_metadata.json is stale; run `npm run generate-list` and review the result'
    );
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

  // Verify markdownLoader.js restricts transcript glob strictly to session_*_corrected.txt
  const loaderPath = 'src/utils/markdownLoader.js';
  if (fs.existsSync(path.join(repoRoot, loaderPath))) {
    const loaderSource = readText(loaderPath);
    if (/transcripts\/\*\.txt/.test(loaderSource)) {
      error(`${loaderPath} uses broad \`transcripts/*.txt\` glob which leaks raw/bkp transcripts into dist`);
    }
  }

  const transcriptsDir = path.join(sessionAssets, 'transcripts');
  if (!fs.existsSync(transcriptsDir)) return;

  const currentTranscriptDir = `Session ${session}`;
  const currentTranscriptLeak = new RegExp(`^session_${session}_.+\\.(txt|json)$`);
  const leakedArtifactPattern = /(_raw\.|bkp|\.bak$|\.tmp$)/i;

  for (const name of fs.readdirSync(transcriptsDir)) {
    if (name === currentTranscriptDir || currentTranscriptLeak.test(name)) {
      error(
        `current-session transcript artifact should not be bundled unless intentionally exposed: src/assets/sessions/transcripts/${name}`
      );
      continue;
    }

    if (leakedArtifactPattern.test(name)) {
      const msg = `unreferenced raw/backup transcript artifact present in src/assets/sessions/transcripts/${name} (excluded from bundle by markdownLoader.js)`;
      if (strictTranscripts) {
        error(msg);
      } else {
        warn(msg);
      }
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

  const stores = loadAllEntityStores(repoRoot);
  const { source: rulesSource, rules: syncRules } = loadSyncRules();
  const compiledChecks = compileRuleEntries(syncRules);
  ok(`loaded ${compiledChecks.length} public-copy sync rule(s) from ${rulesSource}`);

  checkSessionIndex(session, stores);
  checkStoreIntegrity(stores);
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
  ].forEach((file) => checkBadPatterns(file, compiledChecks));
}

console.log();
console.log(`Session sync verification complete: ${errors.length} error(s), ${warnings.length} warning(s).`);
process.exit(errors.length ? 1 : 0);

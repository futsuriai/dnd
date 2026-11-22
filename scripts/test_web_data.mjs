#!/usr/bin/env node
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { REPO_ROOT, loadAllEntityStores } = require('./store_loader.cjs');

import {
  worldData,
  characters,
  npcs,
  locations,
  lore,
  sessions,
  storyPreamble,
  items,
  getAllEntities,
  getEntityById,
  getEntityConnections,
  resolveEntityByNameOrId,
  getEntitiesUpdatedInSession,
  getAllSearchableEntities,
} from '../src/store/worldData.js';
import { currentSession } from '../src/store/config.js';
import {
  BASTION_ONLY_LOCATION_IDS,
  getLocationRoute,
  getEntityRoute,
  badgeLabel,
  hasHistory,
  getLatestSession,
  formatHistoryMarkdown,
} from '../src/utils/entityHelpers.js';

async function loadUseModal() {
  try {
    const mod = await import('../src/composables/useModal.js');
    return mod.useModal;
  } catch (err) {
    if (err && err.code === 'ERR_MODULE_NOT_FOUND') {
      // Fallback when running in a fresh worktree without node_modules/vue
      const src = fs
        .readFileSync(path.join(REPO_ROOT, 'src/composables/useModal.js'), 'utf8')
        .replace(/^\s*import\s+.*from\s+['"]vue['"];?\s*$/m, '')
        .replace(/\bexport\s+function\s+useModal/, 'function useModal')
        .replace(/^\s*export\s+default\s+useModal;?\s*$/m, '');
      const ctx = {
        ref: (initial) => ({ value: initial }),
        __useModal: null,
      };
      vm.createContext(ctx);
      new vm.Script(`${src}\n__useModal = useModal;`).runInContext(ctx);
      return ctx.__useModal;
    }
    throw err;
  }
}

const useModal = await loadUseModal();

let passed = 0;
function test(name, fn) {
  fn();
  passed += 1;
  console.log(`PASS: ${name}`);
}

test('sessions.js exports storyPreamble, stage fields, locations, and unique descriptions', () => {
  assert.equal(typeof storyPreamble, 'string');
  const preambleParagraphs = storyPreamble.split(/\n\s*\n/).filter(Boolean);
  assert.equal(preambleParagraphs.length, 2);

  const s21 = sessions.find((s) => s.id === 'session-21');
  assert.ok(s21);
  assert.equal(typeof s21.homeRecap, 'string');
  assert.ok(s21.homeRecap.length > 40);
  assert.ok(Array.isArray(s21.nextSteps) && s21.nextSteps.length >= 3);
  assert.equal(typeof s21.storyBeat, 'string');

  const milestoneNums = [2, 5, 6, 8, 12, 15, 16, 17, 18, 19, 20, 21];
  for (const n of milestoneNums) {
    const sess = sessions.find((s) => s.id === `session-${n}`);
    assert.ok(sess && typeof sess.storyBeat === 'string' && sess.storyBeat.trim(), `session-${n} missing storyBeat`);
  }

  const s4 = sessions.find((s) => s.id === 'session-4');
  const s5 = sessions.find((s) => s.id === 'session-5');
  assert.notEqual(s4.description, s5.description);
  assert.match(s4.description, /Old Trade Road/i);
  assert.match(s5.description, /Michelle Faberge/i);

  const sMinus1 = sessions.find((s) => s.id === 'session-minus-1');
  assert.equal(sMinus1.upcoming, false);

  for (let n = 10; n <= 15; n += 1) {
    const sess = sessions.find((s) => s.id === `session-${n}`);
    assert.ok(sess.location && sess.location.trim().length > 0, `session-${n} missing location`);
  }

  const rawSessionsText = fs.readFileSync(path.join(REPO_ROOT, 'src/store/sessions.js'), 'utf8');
  assert.ok(!/\bEllaria\b/.test(rawSessionsText), 'Typo Ellaria still present');
  assert.ok(!/\bdesipte\b/.test(rawSessionsText), 'Typo desipte still present');
});

test('characters.js, locations.js, npcs.js data fixes', () => {
  assert.equal(characters.length, 5);
  for (const pc of characters) {
    assert.equal(pc.level, 5, `${pc.id} should be level 5`);
  }

  const estate = getEntityById('location', 'lord-whitakers-estate');
  assert.ok(estate.connections.some((c) => c.type === 'character' && c.id === 'witty'));

  for (const loc of locations) {
    for (const conn of loc.connections || []) {
      assert.ok(!('relationship' in conn), `${loc.id} still uses relationship:`);
      assert.ok(conn.reason && conn.reason.trim(), `${loc.id} connection missing reason:`);
    }
  }

  const faberge = getEntityById('npc', 'michelle-faberge');
  const reeves = getEntityById('npc', 'donnathan-reeves');
  assert.notEqual(faberge.prominence, 'minor');
  assert.notEqual(reeves.prominence, 'minor');

  for (const npcId of ['lex', 'cooper', 'stanley-guard', 'aaron', 'tingle', 'dawn']) {
    const npc = getEntityById('npc', npcId);
    for (const conn of npc.connections || []) {
      assert.ok(getEntityById(conn.type, conn.id), `Broken connection on ${npcId}: ${conn.type}:${conn.id}`);
    }
  }
});

test('worldData.js removes src_future import and exposes exact contracts', () => {
  const wdSource = fs.readFileSync(path.join(REPO_ROOT, 'src/store/worldData.js'), 'utf8');
  assert.ok(!/import\s+.*src_future/.test(wdSource), 'worldData.js should not import src_future');
  assert.deepEqual(items, []);
  assert.deepEqual(worldData.items, []);

  assert.equal(getEntityById('location', 'does-not-exist'), null);
  assert.equal(getEntityById('lore', ''), null);

  const all = getAllEntities();
  assert.equal(all.length, characters.length + npcs.length + locations.length + lore.length);
});

test('worldData.getEntityConnections supports both signatures and deduplicated bidirectional backlinks', () => {
  for (const pc of characters) {
    const viaObj = getEntityConnections(pc);
    const viaPair = getEntityConnections('character', pc.id);
    assert.deepEqual(viaObj, viaPair, `Mismatch between object and pair call for ${pc.id}`);
    assert.ok(viaObj.length > 0, `PC ${pc.id} should have connections`);
  }

  // Verify incoming backlinks on PCs
  const ellaraConns = getEntityConnections('character', 'ellara');
  assert.ok(ellaraConns.some((c) => c.id === 'proctor-eduard' && c.direction === 'incoming'));
  assert.ok(ellaraConns.some((c) => c.id === 'arcos' && c.direction === 'incoming'));

  const ysidorConns = getEntityConnections('character', 'ysidor');
  assert.ok(ysidorConns.some((c) => c.id === 'meri' && c.direction === 'incoming'));
  assert.ok(ysidorConns.some((c) => c.id === 'hyr' && c.direction === 'incoming'));

  const nyxConns = getEntityConnections('character', 'nyx');
  assert.ok(nyxConns.some((c) => c.id === 'tsinyra' && c.direction === 'incoming'));
  assert.ok(nyxConns.some((c) => c.id === 'the-static' && c.direction === 'incoming'));

  const wittyConns = getEntityConnections('character', 'witty');
  assert.ok(wittyConns.some((c) => c.id === 'whitaker-family' && c.direction === 'incoming'));

  // Verify deduplication across every entity in all stores
  for (const [type, list] of [
    ['character', characters],
    ['npc', npcs],
    ['location', locations],
    ['lore', lore],
  ]) {
    for (const entity of list) {
      const conns = getEntityConnections(type, entity.id);
      const keys = new Set();
      for (const c of conns) {
        const key = `${c.entityType}:${c.id}`;
        assert.ok(!keys.has(key), `Duplicate connection ${key} on ${type}:${entity.id}`);
        keys.add(key);
        assert.ok(c.direction === 'outgoing' || c.direction === 'incoming');
        assert.ok(c.route && c.route.startsWith('/'));
      }
    }
  }

  // Disambiguate shared ID 'torchlight-college' between locations and lore
  const tcLoc = getEntityById('location', 'torchlight-college');
  const tcLore = getEntityById('lore', 'torchlight-college');
  const tcLocConns = getEntityConnections(tcLoc);
  const tcLoreConns = getEntityConnections(tcLore);
  assert.ok(tcLocConns.some((c) => c.entityType === 'lore' && c.id === 'torchlight-college'));
  assert.ok(tcLoreConns.some((c) => c.entityType === 'location' && c.id === 'torchlight-college'));
});

test('worldData.resolveEntityByNameOrId resolves every WikiLink across all stores', () => {
  const explicitCases = [
    ['[[The Hariolar Empire/The Hariolar Empire|The Hariolar Empire]]', 'location', 'hariolar-empire', '/locations#hariolar-empire'],
    ['[[Timeline of the World#The Age of Shadow]]', 'history', 'the-age-of-shadow', '/history#the-age-of-shadow'],
    ['[[Light Crystal]]', 'lore', 'light-crystals', '/lore#light-crystals'],
    ['[[Eulogia of the Eternal Light]]', 'lore', 'eulogia-eternal-light', '/lore#eulogia-eternal-light'],
    ['[[Shadowed]]', 'lore', 'curse-shadowed', '/lore#curse-shadowed'],
    ['[[Bastion City]]', 'location', 'bastion-city', '/bastion-city'],
    ['[[Duskbreaker Lighthouse]]', 'location', 'duskbreaker-lighthouse', '/locations#duskbreaker-lighthouse'],
    ['[[Hieroterra]]', 'location', 'hieroterra', '/locations#hieroterra'],
    ['[[Pharus]]', 'location', 'pharus', '/locations#pharus'],
  ];

  for (const [input, expectedType, expectedId, expectedRoute] of explicitCases) {
    const res = resolveEntityByNameOrId(input);
    assert.ok(res, `Failed to resolve ${input}`);
    assert.equal(res.type, expectedType, `Wrong type for ${input}`);
    assert.equal(res.id, expectedId, `Wrong id for ${input}`);
    assert.equal(res.route, expectedRoute, `Wrong route for ${input}`);
  }

  assert.equal(resolveEntityByNameOrId('[[Completely Unknown Entity XYZ]]'), null);

  let linkCount = 0;
  for (const list of [lore, locations, npcs, characters, sessions]) {
    for (const entity of list) {
      for (const field of ['fullText', 'description', 'bio']) {
        const text = entity[field];
        if (typeof text !== 'string') continue;
        for (const match of text.matchAll(/\[\[([^\]]+)\]\]/g)) {
          linkCount += 1;
          const resolved = resolveEntityByNameOrId(match[1]);
          assert.ok(resolved, `Unresolved WikiLink [[${match[1]}]] in ${entity.id}.${field}`);
        }
      }
    }
  }
  assert.ok(linkCount >= 9, `Expected at least 9 WikiLinks in stores, checked ${linkCount}`);
});

test('worldData.getEntitiesUpdatedInSession(21) and getAllSearchableEntities()', () => {
  assert.equal(currentSession, 21);
  const updated21 = getEntitiesUpdatedInSession(21);
  assert.deepEqual(
    updated21.npcs.map((n) => n.id).sort(),
    ['donnathan-reeves', 'duke-valerian-oliander', 'proctor-eduard']
  );
  assert.deepEqual(
    updated21.locations.map((l) => l.id).sort(),
    ['duskbreaker-lighthouse', 'lord-whitakers-estate']
  );
  assert.deepEqual(
    updated21.lore.map((l) => l.id).sort(),
    ['light-crystals', 'whitaker-family']
  );

  const searchable = getAllSearchableEntities();
  assert.equal(
    searchable.length,
    sessions.length + characters.length + npcs.length + locations.length + lore.length
  );
  const typesSeen = new Set(searchable.map((s) => s.type));
  assert.deepEqual([...typesSeen].sort(), ['character', 'location', 'lore', 'npc', 'session']);
  for (const entry of searchable) {
    assert.ok(entry.id && entry.name && entry.route.startsWith('/'));
    assert.equal(typeof entry.isNew, 'boolean');
  }
});

test('entityHelpers.js routing, badges, and clickable history markdown', () => {
  for (const id of [
    'the-golden-goose',
    'stonewall-tower',
    'small-watch-house',
    'basement-lab',
    'lighthouse-deep-basement',
    'lighthouse-engineering-floor',
    'lighthouse-arcana-floor',
  ]) {
    assert.ok(BASTION_ONLY_LOCATION_IDS.has(id), `${id} should be in BASTION_ONLY_LOCATION_IDS`);
    assert.equal(getLocationRoute(id), `/bastion-city#${id}`);
  }
  assert.equal(getLocationRoute('bastion-city'), '/bastion-city');
  assert.equal(getLocationRoute('hyrta'), '/locations#hyrta');

  assert.equal(getEntityRoute('character', 'ellara'), '/characters/ellara');
  assert.equal(getEntityRoute('npc', 'meri'), '/npcs#meri');
  assert.equal(getEntityRoute('lore', 'hyr'), '/lore#hyr');
  assert.equal(getEntityRoute('session', 'session-21'), '/sessions/session-21');
  assert.equal(getEntityRoute('location', 'stonewall-tower'), '/bastion-city#stonewall-tower');

  const eduard = getEntityById('npc', 'proctor-eduard');
  assert.equal(hasHistory(eduard), true);
  assert.equal(getLatestSession(eduard), 21);
  assert.equal(badgeLabel(eduard, 21), 'Updated');
  const histMd = formatHistoryMarkdown(eduard);
  assert.match(histMd, /\[Session 21\]\(#\/sessions\/session-21\)/);
  assert.match(histMd, /\[Session 2\]\(#\/sessions\/session-2\)/);

  const brandNew = { history: [{ session: 21, note: 'Introduced' }] };
  assert.equal(badgeLabel(brandNew, 21), 'New');
});

test('useModal composable manages modal state cleanly', () => {
  const { isOpen, modalTitle, modalContent, modalMeta, openModal, closeModal } = useModal();
  assert.equal(isOpen.value, false);
  openModal('Test Title', 'Body **markdown**', { contentClass: 'prose' });
  assert.equal(isOpen.value, true);
  assert.equal(modalTitle.value, 'Test Title');
  assert.equal(modalContent.value, 'Body **markdown**');
  assert.equal(modalMeta.value.contentClass, 'prose');
  closeModal();
  assert.equal(isOpen.value, false);
  assert.equal(modalTitle.value, '');
  assert.equal(modalContent.value, '');
  assert.equal(Object.keys(modalMeta.value).length, 0);
});

test('store_loader.cjs loads all stores cleanly without console.warn spam', () => {
  const warns = [];
  const origWarn = console.warn;
  console.warn = (...a) => warns.push(a.join(' '));
  try {
    const loaded = loadAllEntityStores(REPO_ROOT);
    assert.equal(loaded.characters.length, 5);
    assert.equal(loaded.npcs.length, npcs.length);
    assert.equal(loaded.locations.length, locations.length);
    assert.equal(loaded.lore.length, lore.length);
    assert.equal(loaded.sessions.length, sessions.length);
    assert.equal(typeof loaded.storyPreamble, 'string');
  } finally {
    console.warn = origWarn;
  }
  assert.equal(warns.length, 0, `Unexpected console.warn output: ${warns.join('; ')}`);
});

console.log(`\nAll ${passed} web-data tests passed.`);

// Central data store for world information with bidirectional relationships
// Imports all data collections from separate files and provides shared logic

import { characters } from './characters.js';
import { npcs } from './npcs.js';
import { locations } from './locations.js';
import { sessions, storyPreamble } from './sessions.js';
import { worldHistory } from './worldHistory.js';
import { lore } from './lore.js';
import { currentSession, isEntityNew, parseSessionNumber } from './config.js';
import { getEntityRoute, getLatestSession } from '../utils/entityHelpers.js';

// Retained as an empty array for backward compatibility
export const items = [];

const ENTITY_COLLECTIONS = [
  ['character', characters],
  ['npc', npcs],
  ['location', locations],
  ['lore', lore],
];

// --- Getter functions ---

export function getLocation(id) {
  return locations.find((loc) => loc.id === id) || null;
}

export function getCharacter(id) {
  return characters.find((char) => char.id === id) || null;
}

export function getNpc(id) {
  return npcs.find((npc) => npc.id === id) || null;
}

export function getItem(id) {
  return items.find((item) => item.id === id) || null;
}

export function getSession(id) {
  return sessions.find((session) => session.id === id) || null;
}

export function getLore(id) {
  if (id) {
    return lore.find((item) => item.id === id) || null;
  }
  return lore;
}

export function getLocations(typeOrId) {
  if (!typeOrId) {
    return locations;
  }
  const byId = locations.find((loc) => loc.id === typeOrId);
  if (byId) {
    return byId;
  }
  return locations.filter((loc) => loc.type === typeOrId);
}

// --- Canonical entity lookup functions ---

export function getEntityById(type, id) {
  if (!type || !id) return null;
  if (type === 'character') return getCharacter(id);
  if (type === 'npc') return getNpc(id);
  if (type === 'lore') return getLore(id);
  if (type === 'location') return getLocation(id);
  if (type === 'item') return getItem(id);
  if (type === 'session') return getSession(id);
  return null;
}

// Backward-compatible alias
export function getEntity(type, id) {
  return getEntityById(type, id);
}

function getEntityDisplayName(type, entity) {
  if (!entity) return '';
  if (type === 'lore') return entity.term || entity.name || entity.id;
  if (type === 'session') return entity.subtitle ? `${entity.title}: ${entity.subtitle}` : entity.title || entity.id;
  return entity.name || entity.term || entity.id;
}

function inferEntityType(entity) {
  if (!entity || typeof entity !== 'object') return null;
  if (entity.entityType && ['character', 'npc', 'location', 'lore', 'session', 'item'].includes(entity.entityType)) {
    return entity.entityType;
  }
  // Exact reference check first (handles shared IDs like 'torchlight-college' in both locations & lore)
  if (characters.includes(entity)) return 'character';
  if (npcs.includes(entity)) return 'npc';
  if (locations.includes(entity)) return 'location';
  if (lore.includes(entity)) return 'lore';
  if (sessions.includes(entity)) return 'session';

  // Structural fallback for cloned objects
  if ('term' in entity) return 'lore';
  if ('race' in entity || 'class' in entity || 'dndBeyondLink' in entity) return 'character';
  if ('role' in entity) return 'npc';
  if ('highlights' in entity || 'upcoming' in entity) return 'session';
  if (entity.id) {
    if (getLocation(entity.id)) return 'location';
    if (getNpc(entity.id)) return 'npc';
    if (getCharacter(entity.id)) return 'character';
    if (getLore(entity.id)) return 'lore';
    if (getSession(entity.id)) return 'session';
  }
  return null;
}

/**
 * Return all world entities (characters, npcs, locations, lore) as a flat array
 * tagged with entityType, displayName, and route.
 */
export function getAllEntities() {
  const result = [];
  for (const [entityType, collection] of ENTITY_COLLECTIONS) {
    for (const entity of collection) {
      if (!entity || !entity.id) continue;
      result.push({
        ...entity,
        entityType,
        displayName: getEntityDisplayName(entityType, entity),
        route: getEntityRoute(entityType, entity.id),
      });
    }
  }
  return result;
}

// --- Connection functions (bidirectional + deduplicated) ---

/**
 * Resolve outgoing connections and auto-derived deduplicated incoming backlinks.
 * Supports BOTH signatures:
 *   - getEntityConnections(entity)
 *   - getEntityConnections(type, id)
 *
 * Each returned item has:
 *   { name, id, type, entityType, reason, direction: 'outgoing' | 'incoming', route }
 */
export function getEntityConnections(entityOrType, maybeId) {
  let sourceType = null;
  let sourceId = null;
  let entity = null;

  if (typeof entityOrType === 'string' && typeof maybeId === 'string') {
    sourceType = entityOrType;
    sourceId = maybeId;
    entity = getEntityById(sourceType, sourceId);
  } else if (entityOrType && typeof entityOrType === 'object') {
    entity = entityOrType;
    sourceId = entity.id || null;
    sourceType = inferEntityType(entity);
    if (sourceType && sourceId) {
      entity = getEntityById(sourceType, sourceId) || entity;
    }
  }

  if (!entity || !sourceType || !sourceId) return [];

  const resolved = [];
  const seen = new Set();

  // 1. Outgoing connections declared on the entity
  if (Array.isArray(entity.connections)) {
    for (const conn of entity.connections) {
      if (!conn || !conn.type || !conn.id) continue;
      if (conn.type === sourceType && conn.id === sourceId) continue;
      const connectedEntity = getEntityById(conn.type, conn.id);
      if (!connectedEntity) continue;

      const key = `${conn.type}:${connectedEntity.id}`;
      if (seen.has(key)) continue;
      seen.add(key);

      resolved.push({
        name: getEntityDisplayName(conn.type, connectedEntity),
        id: connectedEntity.id,
        type: conn.type,
        entityType: conn.type,
        reason: conn.reason || conn.relationship || '',
        direction: 'outgoing',
        route: getEntityRoute(conn.type, connectedEntity.id),
      });
    }
  }

  // 2. Incoming backlinks auto-derived from all other entities across stores
  for (const [otherType, collection] of ENTITY_COLLECTIONS) {
    for (const other of collection) {
      if (!other || !other.id || !Array.isArray(other.connections)) continue;
      if (otherType === sourceType && other.id === sourceId) continue;

      const matchingConn = other.connections.find(
        (conn) => conn && conn.type === sourceType && conn.id === sourceId
      );
      if (!matchingConn) continue;

      const key = `${otherType}:${other.id}`;
      if (seen.has(key)) continue;
      seen.add(key);

      resolved.push({
        name: getEntityDisplayName(otherType, other),
        id: other.id,
        type: otherType,
        entityType: otherType,
        reason: matchingConn.reason || matchingConn.relationship || '',
        direction: 'incoming',
        route: getEntityRoute(otherType, other.id),
      });
    }
  }

  return resolved;
}

// --- WikiLink / Name-or-ID Resolver ---

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
  'light-crystal': { type: 'lore', id: 'light-crystals' },
  'light-crystals': { type: 'lore', id: 'light-crystals' },
  'shadowed': { type: 'lore', id: 'curse-shadowed' },
  'the-shadowed': { type: 'lore', id: 'curse-shadowed' },
  'curse-of-the-shadowed': { type: 'lore', id: 'curse-shadowed' },
  'the-curse-of-the-shadowed': { type: 'lore', id: 'curse-shadowed' },
  'eulogia': { type: 'lore', id: 'eulogia-eternal-light' },
  'the-eulogia': { type: 'lore', id: 'eulogia-eternal-light' },
  'eulogia-of-the-eternal-light': { type: 'lore', id: 'eulogia-eternal-light' },
  'hariolar-empire': { type: 'location', id: 'hariolar-empire' },
  'the-hariolar-empire': { type: 'location', id: 'hariolar-empire' },
  'hyrda': { type: 'location', id: 'hyrta' },
  'hyrda-mines': { type: 'location', id: 'hyrta-mines' },
  'hyrda-ducal-encampment': { type: 'location', id: 'hyrta-ducal-encampment' },
  'lighthouse': { type: 'location', id: 'duskbreaker-lighthouse' },
  'the-lighthouse': { type: 'location', id: 'duskbreaker-lighthouse' },
  'eternal-light': { type: 'lore', id: 'eternal-light' },
  'the-eternal-light': { type: 'lore', id: 'eternal-light' },
  'first-emperor': { type: 'lore', id: 'first-emperor' },
  'the-first-emperor': { type: 'lore', id: 'first-emperor' },
  'lightkeepers': { type: 'lore', id: 'lightkeepers' },
  'the-lightkeepers': { type: 'lore', id: 'lightkeepers' },
  'black-swan': { type: 'lore', id: 'black-swan' },
  'the-black-swan': { type: 'lore', id: 'black-swan' },
  'great-cataclysm': { type: 'lore', id: 'great-cataclysm' },
  'the-great-cataclysm': { type: 'lore', id: 'great-cataclysm' },
  'pilgrimage-of-the-enlightened': { type: 'lore', id: 'pilgrimage-enlightened' },
  'the-pilgrimage-of-the-enlightened': { type: 'lore', id: 'pilgrimage-enlightened' },
  'the-static': { type: 'lore', id: 'the-static' },
  'static': { type: 'lore', id: 'the-static' },
  'warforged': { type: 'lore', id: 'warforged' },
  'warforged-construct': { type: 'lore', id: 'warforged' },
  'warforged-constructs': { type: 'lore', id: 'warforged' },
  'whitaker-family': { type: 'lore', id: 'whitaker-family' },
  'whitaker-brothers': { type: 'lore', id: 'whitaker-family' },
  'the-whitaker-brothers': { type: 'lore', id: 'whitaker-family' },
  'lord-whitaker-6th': { type: 'character', id: 'witty' },
  'lord-whitaker-the-6th': { type: 'character', id: 'witty' },
  'whitaker-whitman-vi': { type: 'character', id: 'witty' },
  'whitaker-witty-whitman-vi': { type: 'character', id: 'witty' },
  'tsinyra': { type: 'npc', id: 'tsinyra' },
  'tsi-nyra': { type: 'npc', id: 'tsinyra' },
  'eduard': { type: 'npc', id: 'proctor-eduard' },
  'director-reeves': { type: 'npc', id: 'donnathan-reeves' },
  'viscount-sommeil': { type: 'npc', id: 'donnathan-reeves' },
  'reeves': { type: 'npc', id: 'donnathan-reeves' },
  'director-faberge': { type: 'npc', id: 'michelle-faberge' },
  'faberge': { type: 'npc', id: 'michelle-faberge' },
  'grand-duke-valerian-oliander': { type: 'npc', id: 'duke-valerian-oliander' },
  'valerian-oliander': { type: 'npc', id: 'duke-valerian-oliander' },
  'lady-ophelia': { type: 'npc', id: 'lady-ophelia-xanteres-oliander' },
  'ophelia': { type: 'npc', id: 'lady-ophelia-xanteres-oliander' },
  'denmother': { type: 'npc', id: 'denmother' },
  'the-denmother': { type: 'npc', id: 'denmother' },
};

function stripLeadingThe(slug) {
  return slug.startsWith('the-') ? slug.slice(4) : slug;
}

/**
 * Parse Obsidian/WikiLink syntax (`[[Folder/Target|Label]]`, `[[Target#Anchor]]`,
 * plain names, or IDs) and resolve to a canonical entity or history route.
 *
 * @param {string} rawTarget
 * @returns {{ type: string, id: string, name: string, route: string, anchor: string|null } | null}
 */
export function resolveEntityByNameOrId(rawTarget) {
  if (typeof rawTarget !== 'string') return null;
  let cleaned = rawTarget.trim();
  if (!cleaned) return null;

  // Allow callers to pass either "[[Target|Label]]" or "Target|Label"
  if (cleaned.startsWith('[[') && cleaned.endsWith(']]')) {
    cleaned = cleaned.slice(2, -2).trim();
  }
  if (!cleaned) return null;

  const pipeIdx = cleaned.indexOf('|');
  const targetPart = (pipeIdx !== -1 ? cleaned.slice(0, pipeIdx) : cleaned).trim();
  const aliasLabel = pipeIdx !== -1 ? cleaned.slice(pipeIdx + 1).trim() : '';

  const hashIdx = targetPart.indexOf('#');
  const pagePartRaw = (hashIdx !== -1 ? targetPart.slice(0, hashIdx) : targetPart).trim();
  const rawAnchor = hashIdx !== -1 ? targetPart.slice(hashIdx + 1).trim() : '';
  const anchor = rawAnchor ? slugifyTarget(rawAnchor) : null;

  const pageSegment = pagePartRaw.includes('/')
    ? pagePartRaw.split('/').pop().trim()
    : pagePartRaw;
  const slug = slugifyTarget(pageSegment);

  if (!slug) return null;

  // Special case: Timeline / World History page links (e.g. [[Timeline of the World#The Age of Shadow]])
  if (HISTORY_PAGE_SLUGS.has(slug)) {
    const matchedEra = rawAnchor
      ? worldHistory.eras.find((era) => slugifyTarget(era.name) === anchor)
      : null;
    const displayName = aliasLabel || (matchedEra ? matchedEra.name : rawAnchor || 'World History');
    return {
      type: 'history',
      id: anchor || 'history',
      name: displayName,
      route: anchor ? `/history#${anchor}` : '/history',
      anchor,
    };
  }

  const buildResult = (type, entity) => {
    const baseRoute = getEntityRoute(type, entity.id);
    const route = anchor && !baseRoute.includes('#') ? `${baseRoute}#${anchor}` : baseRoute;
    return {
      type,
      id: entity.id,
      name: aliasLabel || getEntityDisplayName(type, entity),
      route,
      anchor,
    };
  };

  // 1. Canonical alias map
  const aliasMatch = WIKILINK_ALIASES[slug] || WIKILINK_ALIASES[stripLeadingThe(slug)];
  if (aliasMatch) {
    const entity = getEntityById(aliasMatch.type, aliasMatch.id);
    if (entity) return buildResult(aliasMatch.type, entity);
  }

  // 2. Direct search across entity collections + sessions
  const searchableCollections = [
    ['character', characters],
    ['npc', npcs],
    ['location', locations],
    ['lore', lore],
    ['session', sessions],
  ];

  const candidateSlugs = new Set([slug, stripLeadingThe(slug)]);
  if (slug.endsWith('s') && slug.length > 3) {
    candidateSlugs.add(slug.slice(0, -1));
  } else {
    candidateSlugs.add(`${slug}s`);
  }

  // Pass A: exact ID match
  for (const [type, collection] of searchableCollections) {
    for (const entity of collection) {
      if (!entity || !entity.id) continue;
      if (candidateSlugs.has(entity.id.toLowerCase())) {
        return buildResult(type, entity);
      }
    }
  }

  // Pass B: slugified display name / term / title match
  for (const [type, collection] of searchableCollections) {
    for (const entity of collection) {
      if (!entity || !entity.id) continue;
      const rawName = type === 'lore' ? entity.term : type === 'session' ? entity.title : entity.name;
      const nameSlug = slugifyTarget(rawName);
      if (candidateSlugs.has(nameSlug) || candidateSlugs.has(stripLeadingThe(nameSlug))) {
        return buildResult(type, entity);
      }
    }
  }

  return null;
}

// --- Session Digest & Global Search helpers ---

function entityWasUpdatedInSession(entity, sessionNum) {
  if (!entity) return false;
  if (Array.isArray(entity.history)) {
    if (entity.history.some((entry) => entry && entry.session === sessionNum)) {
      return true;
    }
  }
  if (Array.isArray(entity.updatedInSessions)) {
    if (entity.updatedInSessions.includes(sessionNum)) {
      return true;
    }
  }
  return false;
}

/**
 * Return entities whose history includes the specified session number.
 *
 * @param {number|string} sessionNum
 * @returns {{ characters: object[], npcs: object[], locations: object[], lore: object[] }}
 */
export function getEntitiesUpdatedInSession(sessionNum) {
  let num = typeof sessionNum === 'number' ? sessionNum : null;
  if (num === null && typeof sessionNum === 'string') {
    const parsedId = parseSessionNumber(sessionNum);
    num = parsedId !== null ? parsedId : Number.parseInt(sessionNum, 10);
  }
  if (!Number.isFinite(num)) {
    return { characters: [], npcs: [], locations: [], lore: [] };
  }

  return {
    characters: characters.filter((entity) => entityWasUpdatedInSession(entity, num)),
    npcs: npcs.filter((entity) => entityWasUpdatedInSession(entity, num)),
    locations: locations.filter((entity) => entityWasUpdatedInSession(entity, num)),
    lore: lore.filter((entity) => entityWasUpdatedInSession(entity, num)),
  };
}

/**
 * Flat array of all searchable records across sessions, characters, npcs, locations, and lore
 * formatted for GlobalSearch.vue.
 *
 * @returns {Array<{
 *   type: string,
 *   id: string,
 *   name: string,
 *   subtitle: string,
 *   description: string,
 *   route: string,
 *   latestSession: number|null,
 *   isNew: boolean
 * }>}
 */
export function getAllSearchableEntities() {
  const results = [];

  for (const session of sessions) {
    if (!session || !session.id) continue;
    const sessionNum = parseSessionNumber(session.id);
    results.push({
      type: 'session',
      id: session.id,
      name: session.subtitle ? `${session.title}: ${session.subtitle}` : session.title,
      subtitle: [session.date, session.location].filter(Boolean).join(' · '),
      description: session.description || '',
      route: getEntityRoute('session', session.id),
      latestSession: sessionNum,
      isNew: sessionNum !== null && sessionNum === currentSession,
    });
  }

  for (const character of characters) {
    if (!character || !character.id) continue;
    results.push({
      type: 'character',
      id: character.id,
      name: character.name,
      subtitle: `${character.race} ${character.class} · Level ${character.level}`,
      description: character.bio || '',
      route: getEntityRoute('character', character.id),
      latestSession: getLatestSession(character),
      isNew: isEntityNew(character),
    });
  }

  for (const npc of npcs) {
    if (!npc || !npc.id) continue;
    results.push({
      type: 'npc',
      id: npc.id,
      name: npc.name,
      subtitle: [npc.role, npc.location].filter(Boolean).join(' · '),
      description: npc.description || '',
      route: getEntityRoute('npc', npc.id),
      latestSession: getLatestSession(npc),
      isNew: isEntityNew(npc),
    });
  }

  for (const loc of locations) {
    if (!loc || !loc.id) continue;
    const typeLabel = loc.type ? loc.type.charAt(0).toUpperCase() + loc.type.slice(1) : 'Location';
    results.push({
      type: 'location',
      id: loc.id,
      name: loc.name,
      subtitle: typeLabel,
      description: loc.description || '',
      route: getEntityRoute('location', loc.id),
      latestSession: getLatestSession(loc),
      isNew: isEntityNew(loc),
    });
  }

  for (const entry of lore) {
    if (!entry || !entry.id) continue;
    results.push({
      type: 'lore',
      id: entry.id,
      name: entry.term,
      subtitle: 'Lore',
      description: entry.description || '',
      route: getEntityRoute('lore', entry.id),
      latestSession: getLatestSession(entry),
      isNew: isEntityNew(entry),
    });
  }

  return results;
}

// --- Legacy runtime mutators (preserved for backward compatibility) ---

export function addCharacter(character) {
  if (!character.id || !character.name) {
    console.error('Character must have id and name');
    return false;
  }
  if (getCharacter(character.id)) {
    console.error(`Character with id ${character.id} already exists`);
    return false;
  }
  characters.push(character);
  return true;
}

export function addNpc(npc) {
  if (!npc.id || !npc.name) {
    console.error('NPC must have id and name');
    return false;
  }
  if (getNpc(npc.id)) {
    console.error(`NPC with id ${npc.id} already exists`);
    return false;
  }
  npcs.push(npc);
  return true;
}

export function addLocation(location) {
  if (!location.id || !location.name || !location.type) {
    console.error('Location must have id, name, and type');
    return false;
  }
  if (getLocation(location.id)) {
    console.error(`Location with id ${location.id} already exists`);
    return false;
  }
  locations.push(location);
  return true;
}

export function addItem(item) {
  if (!item.id || !item.name) {
    console.error('Item must have id and name');
    return false;
  }
  if (getItem(item.id)) {
    console.error(`Item with id ${item.id} already exists`);
    return false;
  }
  items.push(item);
  return true;
}

export function addSession(session) {
  if (!session.id || !session.title) {
    console.error('Session must have id and title');
    return false;
  }
  if (getSession(session.id)) {
    console.error(`Session with id ${session.id} already exists`);
    return false;
  }
  sessions.push(session);
  return true;
}

export function addConnection(sourceType, sourceId, targetType, targetId, reason) {
  const sourceEntity = getEntityById(sourceType, sourceId);
  const targetEntity = getEntityById(targetType, targetId);

  if (!sourceEntity || !targetEntity) {
    console.error('Source or target entity not found for connection:', {
      sourceType,
      sourceId,
      targetType,
      targetId,
    });
    return false;
  }

  if (!sourceEntity.connections) {
    sourceEntity.connections = [];
  }

  const existingConnection = sourceEntity.connections.find(
    (conn) => conn.type === targetType && conn.id === targetId
  );

  const targetName = getEntityDisplayName(targetType, targetEntity);

  if (existingConnection) {
    if (reason) {
      existingConnection.reason = reason;
    }
  } else {
    sourceEntity.connections.push({
      type: targetType,
      id: targetId,
      reason: reason || `Connected to ${targetName}`,
    });
  }

  return true;
}

// Export the data collections for direct imports
export {
  characters,
  npcs,
  locations,
  sessions,
  storyPreamble,
  worldHistory,
  lore,
};

// Named + default worldData object
export const worldData = {
  characters,
  npcs,
  lore,
  locations,
  items,
  sessions,
  storyPreamble,
  worldHistory,
  getLocations,
  getLocation,
  getCharacter,
  getNpc,
  getLore,
  getItem,
  getSession,
  getEntity,
  getEntityById,
  getAllEntities,
  getEntityConnections,
  resolveEntityByNameOrId,
  getEntitiesUpdatedInSession,
  getAllSearchableEntities,
  addCharacter,
  addNpc,
  addLocation,
  addItem,
  addSession,
  addConnection,
};

export default worldData;

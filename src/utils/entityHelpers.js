// Shared entity routing, badge, and history formatting helpers

import { locations } from '../store/locations.js';
import { currentSession as defaultCurrentSession, getEntityUpdateHistory } from '../store/config.js';

const WORLD_LOCATION_TYPES = new Set([
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

const PROVINCE_IDS = new Set(
  locations
    .filter((loc) => loc && loc.type === 'province')
    .map((loc) => loc.id)
);

function isBastionScopedLocation(loc) {
  if (!loc || loc.id === 'bastion-city') return false;
  if (Array.isArray(loc.tags) && loc.tags.includes('bastion city')) return true;
  return Boolean(
    Array.isArray(loc.connections) &&
      loc.connections.some(
        (conn) =>
          conn &&
          conn.type === 'location' &&
          (conn.id === 'bastion-city' || conn.id === 'duskbreaker-lighthouse')
      )
  );
}

/**
 * Location IDs that render on /bastion-city rather than /locations
 * (e.g. Bastion inns, prisons, and Lighthouse facilities).
 */
export const BASTION_ONLY_LOCATION_IDS = new Set(
  locations
    .filter((loc) => {
      if (!isBastionScopedLocation(loc)) return false;
      if (WORLD_LOCATION_TYPES.has(loc.type)) return false;
      const connectedToProvince =
        Array.isArray(loc.connections) &&
        loc.connections.some((conn) => conn && conn.type === 'location' && PROVINCE_IDS.has(conn.id));
      return !connectedToProvince;
    })
    .map((loc) => loc.id)
);

/**
 * Resolve the route for a location entity ID.
 * Bastion City routes to /bastion-city; Bastion-only locations route to /bastion-city#<id>;
 * all other locations route to /locations#<id>.
 *
 * @param {string} locationId
 * @returns {string}
 */
export function getLocationRoute(locationId) {
  if (!locationId) return '/locations';
  if (locationId === 'bastion-city') return '/bastion-city';
  if (BASTION_ONLY_LOCATION_IDS.has(locationId)) {
    return `/bastion-city#${locationId}`;
  }
  return `/locations#${locationId}`;
}

/**
 * Resolve the canonical app route for any entity type and ID.
 *
 * @param {string} type - 'character' | 'npc' | 'location' | 'lore' | 'session' | 'history'
 * @param {string} id
 * @returns {string}
 */
export function getEntityRoute(type, id) {
  if (!type) return '/';
  switch (type) {
    case 'character':
      return id ? `/characters/${id}` : '/characters';
    case 'npc':
      return id ? `/npcs#${id}` : '/npcs';
    case 'lore':
      return id ? `/lore#${id}` : '/lore';
    case 'session':
      return id ? `/sessions/${id}` : '/sessions';
    case 'location':
      return getLocationRoute(id);
    case 'history':
      return id && id !== 'history' ? `/history#${id}` : '/history';
    default:
      return '/';
  }
}

/**
 * Return the latest session number recorded in an entity's history, or null if none.
 *
 * @param {Object} entity
 * @returns {number|null}
 */
export function getLatestSession(entity) {
  const sessionNumbers = getEntityUpdateHistory(entity);
  return sessionNumbers.length > 0 ? sessionNumbers[sessionNumbers.length - 1] : null;
}

/**
 * Return true if an entity has any recorded history entries.
 *
 * @param {Object} entity
 * @returns {boolean}
 */
export function hasHistory(entity) {
  if (!entity) return false;
  const sessionNumbers = getEntityUpdateHistory(entity);
  const notes = Array.isArray(entity.history) ? entity.history : [];
  return sessionNumbers.length > 0 || notes.length > 0;
}

/**
 * Return 'New' (only updated in currentSession), 'Updated' (updated in currentSession and earlier),
 * or null if not touched in currentSession.
 *
 * @param {Object} entity
 * @param {number} [currentSession]
 * @returns {'New'|'Updated'|null}
 */
export function badgeLabel(entity, currentSession = defaultCurrentSession) {
  const sessionNumbers = getEntityUpdateHistory(entity);
  if (!sessionNumbers.includes(currentSession)) {
    return null;
  }
  return sessionNumbers.length === 1 ? 'New' : 'Updated';
}

/**
 * Return a fallback 'Session N' label for entities with history not updated in currentSession.
 *
 * @param {Object} entity
 * @param {number} [currentSession]
 * @returns {string|null}
 */
export function fallbackBadgeLabel(entity, currentSession = defaultCurrentSession) {
  const sessionNumbers = getEntityUpdateHistory(entity);
  if (!sessionNumbers.length || sessionNumbers.includes(currentSession)) {
    return null;
  }
  const latest = sessionNumbers[sessionNumbers.length - 1];
  return `Session ${latest}`;
}

/**
 * Format an entity's history entries as Markdown with clickable session links.
 *
 * @param {Object} entity
 * @returns {string}
 */
export function formatHistoryMarkdown(entity) {
  if (!entity) return '';
  const sessionNumbers = getEntityUpdateHistory(entity);
  const notes = Array.isArray(entity.history) ? entity.history : [];
  if (!sessionNumbers.length && !notes.length) return '';

  const notesBySession = {};
  for (const entry of notes) {
    if (entry && typeof entry.session === 'number') {
      if (!notesBySession[entry.session]) {
        notesBySession[entry.session] = [];
      }
      if (entry.note) {
        notesBySession[entry.session].push(entry.note);
      }
    }
  }

  const allSessions = Array.from(
    new Set([
      ...sessionNumbers,
      ...notes
        .map((entry) => (entry && typeof entry.session === 'number' ? entry.session : null))
        .filter((n) => typeof n === 'number'),
    ])
  ).sort((a, b) => a - b);

  return allSessions
    .map((sessionNum) => {
      const link = `[Session ${sessionNum}](#/sessions/session-${sessionNum})`;
      const detail =
        notesBySession[sessionNum] && notesBySession[sessionNum].length > 0
          ? ` — ${notesBySession[sessionNum].join(' • ')}`
          : ' — Updated';
      return `- ${link}${detail}`;
    })
    .join('\n');
}

export default {
  BASTION_ONLY_LOCATION_IDS,
  getLocationRoute,
  getEntityRoute,
  badgeLabel,
  fallbackBadgeLabel,
  hasHistory,
  getLatestSession,
  formatHistoryMarkdown,
};

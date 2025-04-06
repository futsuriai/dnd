// Central data store for world information using history-based event sourcing
// This file now acts as an adapter between the history-based data model and the rest of the application

import historyStore, {
  buildEntityFromHistory,
  getAllEntities,
  getEntityEvents,
  getAllSessionRelatedEvents
} from './history.js';

// HELPER FUNCTIONS

// Getter functions - now pulling from history events
export function getLocations(type = null) {
  const locations = getAllEntities('location');
  if (type) {
    return locations.filter(loc => loc.type === type);
  }
  return locations;
}

export function getLocation(id) {
  return buildEntityFromHistory('location', id);
}

export function getCharacter(id) {
  return buildEntityFromHistory('character', id);
}

export function getNpc(id) {
  return buildEntityFromHistory('npc', id);
}

export function getItem(id) {
  return buildEntityFromHistory('item', id);
}

export function getSession(id) {
  return buildEntityFromHistory('session', id);
}

// Get all sessions
export function getAllSessions() {
  return getAllEntities('session').sort((a, b) => {
    // Get session number from ID
    const aNum = parseInt(a.id.split('-')[1]) || -1;
    const bNum = parseInt(b.id.split('-')[1]) || -1;
    return bNum - aNum; // Sort in descending order (newest first)
  });
}

// Get all characters
export function getAllCharacters() {
  return getAllEntities('character');
}

// Get all npcs
export function getAllNpcs() {
  return getAllEntities('npc');
}

// Get all items 
export function getAllItems() {
  return getAllEntities('item');
}

// Entity retrieval functions
export function getEntity(type, id) {
  if (type === 'character') return getCharacter(id);
  if (type === 'npc') return getNpc(id);
  if (type === 'location') return getLocation(id);
  if (type === 'item') return getItem(id);
  if (type === 'session') return getSession(id);
  return null;
}

// Get entity history - events where this entity was created, updated, or connected
export function getEntityHistory(type, id) {
  return getEntityEvents(type, id);
}

// Get all entities that changed in a specific session
export function getSessionEntities(sessionId) {
  const events = getAllSessionRelatedEvents(sessionId);
  
  // Create a set of all affected entities
  const affectedEntities = new Set();
  
  events.forEach(event => {
    if (event.entityType !== 'session') { // Skip the session creation itself
      affectedEntities.add(`${event.entityType}:${event.entityId}`);
    }
    if (event.type === 'connect' && event.targetEntityType) {
      affectedEntities.add(`${event.targetEntityType}:${event.targetEntityId}`);
    }
  });
  
  // Convert the set back to an array of entity objects
  return Array.from(affectedEntities).map(entityKey => {
    const [type, id] = entityKey.split(':');
    return {
      type,
      id,
      entity: getEntity(type, id)
    };
  });
}

// Connection functions
export function getEntityConnections(type, id) {
  const entity = getEntity(type, id);

  if (!entity || !entity.connections) return [];

  return entity.connections.map(conn => {
    const connectedEntity = getEntity(conn.type, conn.id);

    if (connectedEntity) {
      return {
        name: connectedEntity.name,
        id: connectedEntity.id,
        reason: conn.reason,
        entityType: conn.type,
        sessionId: conn.sessionId // Include when the connection was established
      };
    }
    return null;
  }).filter(Boolean);
}

// Export the history-based collections for use in other files
export const characters = getAllCharacters();
export const npcs = getAllNpcs();
export const locations = getLocations();
export const items = getAllItems();
export const sessions = getAllSessions();

// Re-export worldHistory unchanged as it's a different structure
import { worldHistory } from './worldHistory.js';
export { worldHistory };

// Export default worldData object for easy importing
export default {
  characters,
  npcs,
  locations,
  items,
  sessions,
  worldHistory,
  getLocations,
  getLocation,
  getCharacter,
  getAllCharacters,
  getNpc,
  getAllNpcs,
  getItem,
  getAllItems,
  getSession,
  getAllSessions,
  getEntity,
  getEntityConnections,
  getEntityHistory,
  getSessionEntities
};

// Central data store for world information with bidirectional relationships
// Imports all data collections from separate files and provides shared logic

// Import data collections from separate files
import { characters } from './characters.js';
import { npcs } from './npcs.js';
import { locations } from './locations.js';
import { items } from './items.js';
import { sessions } from './sessions.js';
import { worldHistory } from './worldHistory.js';

// HELPER FUNCTIONS

// Getter functions
export function getLocations(type = null) {
  if (type) {
    return locations.filter(loc => loc.type === type);
  }
  return locations;
}

export function getLocation(id) {
  return locations.find(loc => loc.id === id);
}

export function getCharacter(id) {
  return characters.find(char => char.id === id);
}

export function getNpc(id) {
  return npcs.find(npc => npc.id === id);
}

export function getItem(id) {
  return items.find(item => item.id === id);
}

export function getSession(id) {
  return sessions.find(session => session.id === id);
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

// Entity adding functions
export function addCharacter(character) {
  // Ensure the character has all required fields
  if (!character.id || !character.name) {
    console.error('Character must have id and name');
    return false;
  }

  // Check for duplicates
  if (getCharacter(character.id)) {
    console.error(`Character with id ${character.id} already exists`);
    return false;
  }

  // Add to collection
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
        entityType: conn.type
      };
    }
    return null;
  }).filter(Boolean);
}

export function addConnection(sourceType, sourceId, targetType, targetId, reason) {
  const sourceEntity = getEntity(sourceType, sourceId);
  const targetEntity = getEntity(targetType, targetId);

  if (!sourceEntity || !targetEntity) {
    console.error('Source or target entity not found');
    return false;
  }

  // Initialize connections array if it doesn't exist
  if (!sourceEntity.connections) {
    sourceEntity.connections = [];
  }

  // Check if connection already exists
  const existingConnection = sourceEntity.connections.find(conn =>
    conn.type === targetType && conn.id === targetId
  );

  if (existingConnection) {
    // Update reason if provided
    if (reason) {
      existingConnection.reason = reason;
    }
  } else {
    // Add new connection
    sourceEntity.connections.push({
      type: targetType,
      id: targetId,
      reason: reason || `Connected to ${targetEntity.name}`
    });
  }

  return true;
}

// Export the data collections for use in other files
export {
  characters,
  npcs,
  locations,
  items,
  sessions,
  worldHistory
};

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
  getNpc,
  getItem,
  getSession,
  getEntity,
  getEntityConnections,
  addCharacter,
  addNpc,
  addLocation,
  addItem,
  addSession,
  addConnection
};

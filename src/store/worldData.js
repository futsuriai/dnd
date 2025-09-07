// Central data store for world information with bidirectional relationships
// Imports all data collections from separate files and provides shared logic

// Import data collections from separate files
import { characters } from './characters.js';
import { npcs } from './npcs.js';
import { locations } from './locations.js';
import { items } from '../../src_future/items.js';
import { sessions } from './sessions.js';
import { worldHistory } from './worldHistory.js';
import { lore } from './lore.js';

// HELPER FUNCTIONS

// Getter functions

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


export function getLore(id) { // Updated to accept id
  if (id) {
    return lore.find(item => item.id === id);
  }
  return lore; // Return all if no id provided
}

export function getLocations(typeOrId) { // Updated to get by type or id
  if (!typeOrId) {
    return locations; // Return all if no type/id provided
  }
  // Check if it's likely an ID (simple check, adjust if needed)
  if (locations.some(loc => loc.id === typeOrId)) {
    return locations.find(loc => loc.id === typeOrId);
  }
  // Otherwise, filter by type
  return locations.filter(loc => loc.type === typeOrId);
}

// Entity retrieval functions
export function getEntity(type, id) {
  if (type === 'character') return getCharacter(id);
  if (type === 'npc') return getNpc(id);
  if (type === 'lore') return getLore(id); // Added lore retrieval
  if (type === 'location') return getLocations(id);
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
      // Use 'term' for lore, 'name' for others
      const displayName = conn.type === 'lore' ? connectedEntity.term : connectedEntity.name;
      return {
        name: displayName, // Use appropriate display name
        id: connectedEntity.id,
        reason: conn.reason,
        entityType: conn.type
      };
    }
    return null;
  }).filter(Boolean);
}

// Updated addConnection to be potentially bidirectional if needed later,
// but currently only adds to source as per original structure.
// If bidirectional connections are desired, this function needs modification
// to add the connection to the targetEntity as well.
export function addConnection(sourceType, sourceId, targetType, targetId, reason) {
  const sourceEntity = getEntity(sourceType, sourceId);
  const targetEntity = getEntity(targetType, targetId); // Get target for validation

  if (!sourceEntity || !targetEntity) {
    console.error('Source or target entity not found for connection:', { sourceType, sourceId, targetType, targetId });
    return false;
  }

  // Initialize connections array if it doesn't exist on source
  if (!sourceEntity.connections) {
    sourceEntity.connections = [];
  }

  // Check if connection already exists on source
  const existingConnection = sourceEntity.connections.find(conn =>
    conn.type === targetType && conn.id === targetId
  );

  const targetName = targetType === 'lore' ? targetEntity.term : targetEntity.name;

  if (existingConnection) {
    // Update reason if provided
    if (reason) {
      existingConnection.reason = reason;
    }
  } else {
    // Add new connection to source
    sourceEntity.connections.push({
      type: targetType,
      id: targetId,
      reason: reason || `Connected to ${targetName}`
    });
  }

  // --- Optional: Add connection to target for bidirectionality ---
  // This part is commented out to maintain current behavior. Uncomment if needed.
  /*
  if (!targetEntity.connections) {
    targetEntity.connections = [];
  }
  const existingReverseConnection = targetEntity.connections.find(conn =>
    conn.type === sourceType && conn.id === sourceId
  );
  const sourceName = sourceType === 'lore' ? sourceEntity.term : sourceEntity.name;
  if (!existingReverseConnection) {
     targetEntity.connections.push({
       type: sourceType,
       id: sourceId,
       reason: `Connected from ${sourceName}` // Or use the provided reason? Needs decision.
     });
  }
  */

  return true;
}


// Export the data collections for use in other files
export {
  characters,
  npcs,
  locations,
  items,
  sessions,
  worldHistory,
  lore
};

// Export default worldData object for easy importing
export default {
  characters,
  npcs,
  lore,
  locations,
  items,
  sessions,
  worldHistory,
  getLocations,
  getLocation,
  getCharacter,
  getNpc,
  getLore,
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

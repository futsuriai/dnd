// Central data store for world information using history-based event sourcing
// This file now acts as an adapter between the history-based data model and the rest of the application

import historyStore, {
  buildEntityFromHistory,
  getAllEntities,
  getEntityEvents,
  getAllSessionRelatedEvents
} from './history.js';

// Import characters and npcs data
import { characters } from './characters.js';
import { npcs } from './npcs.js';
import { locations } from './locations.js';
import { items } from './items.js';
import { sessions } from './sessions.js';

// Import Firestore service
import firestoreService from '../services/FirestoreService.js';

// Export characters and npcs for direct use
export { characters, npcs, locations, items, sessions };

// State tracking for data source
let useFirestore = false;
let isInitialized = false;
let dataSource = 'local';

// HELPER FUNCTIONS

// Initialize function to determine whether to use Firestore or local data
export async function initWorldData(options = {}) {
  if (isInitialized && !options.forceInit) return dataSource;
  
  try {
    // If seed option is provided, seed the database first
    if (options.seedDatabase) {
      console.log('Seeding Firestore database...');
      const { seedFirestore } = await import('../scripts/seedFirestore.js');
      await seedFirestore();
      console.log('Database seeding complete!');
    }
    
    // Try to get data from Firestore
    const sessions = await firestoreService.getAllSessions();
    if (sessions && sessions.length > 0) {
      console.log('Using Firestore as data source');
      useFirestore = true;
      dataSource = 'firestore';
    } else {
      console.log('Using local data files as data source');
      useFirestore = false;
      dataSource = 'local';
    }
  } catch (error) {
    console.error('Error checking Firestore, falling back to local data:', error);
    useFirestore = false;
    dataSource = 'local';
  }
  
  isInitialized = true;
  return dataSource;
}

// Getter functions - now with support for both data sources
export async function getLocations(type = null) {
  if (!isInitialized) await initWorldData();
  
  if (useFirestore) {
    const locations = await firestoreService.getAllLocations();
    if (type) {
      return locations.filter(loc => loc.type === type);
    }
    return locations;
  } else {
    const locations = getAllEntities('location');
    if (type) {
      return locations.filter(loc => loc.type === type);
    }
    return locations;
  }
}

export async function getLocation(id) {
  if (!isInitialized) await initWorldData();
  
  if (useFirestore) {
    return await firestoreService.get('locations', id);
  } else {
    return buildEntityFromHistory('location', id);
  }
}

export async function getCharacter(id) {
  if (!isInitialized) await initWorldData();
  
  if (useFirestore) {
    return await firestoreService.get('characters', id);
  } else {
    return buildEntityFromHistory('character', id);
  }
}

export async function getNpc(id) {
  if (!isInitialized) await initWorldData();
  
  if (useFirestore) {
    return await firestoreService.get('npcs', id);
  } else {
    return buildEntityFromHistory('npc', id);
  }
}

export async function getItem(id) {
  if (!isInitialized) await initWorldData();
  
  if (useFirestore) {
    return await firestoreService.get('items', id);
  } else {
    return buildEntityFromHistory('item', id);
  }
}

export async function getSession(id) {
  if (!isInitialized) await initWorldData();
  
  if (useFirestore) {
    return await firestoreService.get('sessions', id);
  } else {
    return buildEntityFromHistory('session', id);
  }
}

// Get all sessions
export async function getAllSessions() {
  if (!isInitialized) await initWorldData();
  
  if (useFirestore) {
    return await firestoreService.getAllSessions();
  } else {
    return getAllEntities('session').sort((a, b) => {
      // Get session number from ID
      const aNum = parseInt(a.id.split('-')[1]) || -1;
      const bNum = parseInt(b.id.split('-')[1]) || -1;
      return bNum - aNum; // Sort in descending order (newest first)
    });
  }
}

// Get all characters
export async function getAllCharacters() {
  if (!isInitialized) await initWorldData();
  
  if (useFirestore) {
    return await firestoreService.getAllCharacters();
  } else {
    return getAllEntities('character');
  }
}

// Get all npcs
export async function getAllNpcs() {
  if (!isInitialized) await initWorldData();
  
  if (useFirestore) {
    return await firestoreService.getAllNpcs();
  } else {
    return getAllEntities('npc');
  }
}

// Get all items 
export async function getAllItems() {
  if (!isInitialized) await initWorldData();
  
  if (useFirestore) {
    return await firestoreService.getAllItems();
  } else {
    return getAllEntities('item');
  }
}

// Entity retrieval functions
export async function getEntity(type, id) {
  if (type === 'character') return await getCharacter(id);
  if (type === 'npc') return await getNpc(id);
  if (type === 'location') return await getLocation(id);
  if (type === 'item') return await getItem(id);
  if (type === 'session') return await getSession(id);
  return null;
}

// Get entity history - events where this entity was created, updated, or connected
export async function getEntityHistory(type, id) {
  if (!isInitialized) await initWorldData();
  
  if (useFirestore) {
    return await firestoreService.getEntityEvents(type, id);
  } else {
    return getEntityEvents(type, id);
  }
}

// Get all entities that changed in a specific session
export async function getSessionEntities(sessionId) {
  if (!isInitialized) await initWorldData();
  
  if (useFirestore) {
    const events = await firestoreService.getSessionEvents(sessionId);
    
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
    const entityPromises = Array.from(affectedEntities).map(async entityKey => {
      const [type, id] = entityKey.split(':');
      return {
        type,
        id,
        entity: await getEntity(type, id)
      };
    });
    
    return Promise.all(entityPromises);
  } else {
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
}

// Connection functions
export async function getEntityConnections(type, id) {
  const entity = await getEntity(type, id);

  if (!entity || !entity.connections) return [];

  const connectionPromises = entity.connections.map(async conn => {
    const connectedEntity = await getEntity(conn.type, conn.id);

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
  });

  const connections = await Promise.all(connectionPromises);
  return connections.filter(Boolean);
}

// Get current data source
export function getDataSource() {
  return { source: dataSource, initialized: isInitialized };
}

// Re-export worldHistory unchanged as it's a different structure
import { worldHistory } from './worldHistory.js';
export { worldHistory };

// Export default worldData object for easy importing
export default {
  initWorldData,
  getDataSource,
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
  getSessionEntities,
  worldHistory
};

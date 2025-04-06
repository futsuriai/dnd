// Central data store for world information using history-based event sourcing
// This file acts as an adapter between the history-based data model and the rest of the application

import { historyBasedDataExpanded } from './consolidatedData.js';
import firestoreService from '../services/FirestoreService.js';

// State tracking for data source
let useFirestore = false;
let isInitialized = false;
let dataSource = 'local';

// HISTORY DATA PROCESSING FUNCTIONS

// Build an entity from history entries
export function buildEntityFromHistory(entityType, entityId) {
  // Get all history entries for this entity
  const entries = historyBasedDataExpanded.historyEntries.filter(
    entry => entry.entityId === entityId && 
           (entry.changeType === 'creation' && entry.data.entityType === entityType)
  );
  
  // Also include update entries that target this entity
  const updateEntries = historyBasedDataExpanded.historyEntries.filter(
    entry => entry.entityId === entityId && 
            entry.changeType !== 'creation'
  );
  
  // Combine creation and update entries
  const allEntries = [...entries, ...updateEntries];
  
  if (allEntries.length === 0) return null;
  
  // Start with an empty entity
  const entity = { id: entityId, type: entityType };
  
  // Process entries in chronological order (by session ID and timestamp)
  const sortedEntries = allEntries.sort((a, b) => {
    // First sort by session ID
    const aSession = parseInt(a.sessionId.split('-')[1]) || 0;
    const bSession = parseInt(b.sessionId.split('-')[1]) || 0;
    
    if (aSession !== bSession) return aSession - bSession;
    
    // Then by timestamp if in the same session
    return new Date(a.timestamp) - new Date(b.timestamp);
  });
  
  // Apply each entry to build the entity
  sortedEntries.forEach(entry => {
    if (entry.changeType === 'creation') {
      // Apply all creation data
      Object.assign(entity, entry.data);
    } 
    else if (entry.changeType === 'update') {
      // Apply updates
      Object.assign(entity, entry.data);
    }
    else if (entry.changeType === 'connection_added') {
      // Initialize connections array if it doesn't exist
      if (!entity.connections) entity.connections = [];
      
      // Add the connection
      entity.connections.push({
        type: entry.data.connectedEntityType,
        id: entry.data.connectedEntityId,
        reason: entry.data.reason,
        sessionId: entry.sessionId
      });
    }
    else if (entry.changeType === 'connection_removed') {
      // Remove connection if it exists
      if (entity.connections) {
        entity.connections = entity.connections.filter(
          conn => !(conn.type === entry.data.connectedEntityType && conn.id === entry.data.connectedEntityId)
        );
      }
    }
    else if (entry.changeType === 'connection_updated') {
      // Update an existing connection
      if (entity.connections) {
        const connIndex = entity.connections.findIndex(
          conn => conn.type === entry.data.connectedEntityType && conn.id === entry.data.connectedEntityId
        );
        
        if (connIndex >= 0) {
          entity.connections[connIndex].reason = entry.data.reason;
        }
      }
    }
  });
  
  // Add history to the entity
  entity.history = organizeHistoryBySession(sortedEntries);
  
  return entity;
}

// Organize history entries by session for UI display
function organizeHistoryBySession(entries) {
  const sessionMap = new Map();
  
  entries.forEach(entry => {
    if (!sessionMap.has(entry.sessionId)) {
      sessionMap.set(entry.sessionId, {
        sessionId: entry.sessionId,
        events: []
      });
    }
    
    // Create a user-friendly event description
    let description = '';
    
    if (entry.changeType === 'creation') {
      description = `${capitalizeFirst(entry.data.entityType)} was created`;
    } else if (entry.changeType === 'update') {
      const entityType = entry.data.entityType || getEntityTypeFromId(entry.entityId);
      description = `${capitalizeFirst(entityType)} was updated`;
      
      // Add details about what was updated if available
      if (entry.data && entry.data.last_action) {
        description = entry.data.last_action;
      } else if (entry.data && entry.data.status) {
        description = `Status changed to: ${entry.data.status}`;
      }
    } else if (entry.changeType === 'connection_added') {
      const targetType = capitalizeFirst(entry.data.connectedEntityType);
      const targetName = getEntityNameFromId(entry.data.connectedEntityType, entry.data.connectedEntityId);
      description = `Connected to ${targetType} "${targetName}": ${entry.data.reason}`;
    } else if (entry.changeType === 'connection_removed') {
      const targetType = capitalizeFirst(entry.data.connectedEntityType);
      const targetName = getEntityNameFromId(entry.data.connectedEntityType, entry.data.connectedEntityId);
      description = `Connection to ${targetType} "${targetName}" was removed`;
    } else if (entry.changeType === 'connection_updated') {
      const targetType = capitalizeFirst(entry.data.connectedEntityType);
      const targetName = getEntityNameFromId(entry.data.connectedEntityType, entry.data.connectedEntityId);
      description = `Updated connection to ${targetType} "${targetName}": ${entry.data.reason}`;
    }
    
    sessionMap.get(entry.sessionId).events.push({
      type: entry.changeType.split('_')[0], // Simplify the type for CSS
      description: description,
      timestamp: entry.timestamp || new Date().toISOString(),
      changes: entry.data
    });
  });
  
  // Convert to array and sort by session ID
  return Array.from(sessionMap.values()).sort((a, b) => {
    const aSession = parseInt(a.sessionId.split('-')[1]) || 0;
    const bSession = parseInt(b.sessionId.split('-')[1]) || 0;
    return bSession - aSession; // Sort from newest to oldest
  });
}

// Get entity name from ID (for better history descriptions)
function getEntityNameFromId(entityType, entityId) {
  // Look for creation entries to get entity names
  const creationEntry = historyBasedDataExpanded.historyEntries.find(
    entry => entry.entityId === entityId && 
            entry.changeType === 'creation' && 
            entry.data.entityType === entityType
  );
  
  if (creationEntry && creationEntry.data && creationEntry.data.name) {
    return creationEntry.data.name;
  }
  
  // If not found, return the ID as fallback
  return entityId;
}

// Get entity type from ID when not provided
export function getEntityTypeFromId(entityId) {
  const creationEntry = historyBasedDataExpanded.historyEntries.find(
    entry => entry.entityId === entityId && entry.changeType === 'creation'
  );
  
  if (creationEntry && creationEntry.data && creationEntry.data.entityType) {
    return creationEntry.data.entityType;
  }
  
  return 'entity'; // Default fallback
}

// Utility function to capitalize first letter
function capitalizeFirst(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

// Get all entities of a specific type
export function getAllEntities(entityType) {
  // Get unique entity IDs of this type by checking creation entries
  const entityIds = [...new Set(
    historyBasedDataExpanded.historyEntries
      .filter(entry => entry.changeType === 'creation' && entry.data.entityType === entityType)
      .map(entry => entry.entityId)
  )];
  
  // Build each entity from history
  return entityIds.map(id => buildEntityFromHistory(entityType, id))
    .filter(Boolean) // Remove null entities
    .sort((a, b) => (a.name || '').localeCompare(b.name || '')); // Sort by name
}

// Get all events related to a specific entity
export function getEntityEvents(entityType, entityId) {
  // First find if the entity exists with the correct type
  const creationEntry = historyBasedDataExpanded.historyEntries.find(
    entry => entry.entityId === entityId && 
            entry.changeType === 'creation' && 
            entry.data.entityType === entityType
  );
  
  if (!creationEntry) return [];
  
  // If entity exists, get all its events
  return historyBasedDataExpanded.historyEntries.filter(
    entry => entry.entityId === entityId
  );
}

// Get all events related to a specific session
export function getAllSessionRelatedEvents(sessionId) {
  return historyBasedDataExpanded.historyEntries.filter(
    entry => entry.sessionId === sessionId
  );
}

// Get entity as it appeared at a specific session
export function getEntityAtSession(entityType, entityId, sessionId) {
  // Get the session number for comparison
  const targetSessionNum = parseInt(sessionId.split('-')[1]) || 0;
  
  // First check if entity exists with correct type
  const creationEntry = historyBasedDataExpanded.historyEntries.find(
    entry => entry.entityId === entityId && 
            entry.changeType === 'creation' && 
            entry.data.entityType === entityType
  );
  
  if (!creationEntry) return null;
  
  // Get all history entries for this entity up to the specified session
  const entries = historyBasedDataExpanded.historyEntries.filter(
    entry => {
      const entrySessionNum = parseInt(entry.sessionId.split('-')[1]) || 0;
      return entry.entityId === entityId && entrySessionNum <= targetSessionNum;
    }
  );
  
  if (entries.length === 0) return null;
  
  // Build entity with just these entries
  const entity = { id: entityId, type: entityType };
  
  // Process entries in chronological order
  const sortedEntries = entries.sort((a, b) => {
    const aSession = parseInt(a.sessionId.split('-')[1]) || 0;
    const bSession = parseInt(b.sessionId.split('-')[1]) || 0;
    
    if (aSession !== bSession) return aSession - bSession;
    
    // Then by timestamp if in the same session
    return new Date(a.timestamp) - new Date(b.timestamp);
  });
  
  // Apply each entry to build the entity (same logic as buildEntityFromHistory)
  sortedEntries.forEach(entry => {
    if (entry.changeType === 'creation') {
      Object.assign(entity, entry.data);
    } 
    else if (entry.changeType === 'update') {
      Object.assign(entity, entry.data);
    }
    else if (entry.changeType === 'connection_added') {
      if (!entity.connections) entity.connections = [];
      entity.connections.push({
        type: entry.data.connectedEntityType,
        id: entry.data.connectedEntityId,
        reason: entry.data.reason,
        sessionId: entry.sessionId
      });
    }
    else if (entry.changeType === 'connection_removed') {
      if (entity.connections) {
        entity.connections = entity.connections.filter(
          conn => !(conn.type === entry.data.connectedEntityType && conn.id === entry.data.connectedEntityId)
        );
      }
    }
    else if (entry.changeType === 'connection_updated') {
      if (entity.connections) {
        const connIndex = entity.connections.findIndex(
          conn => conn.type === entry.data.connectedEntityType && conn.id === entry.data.connectedEntityId
        );
        
        if (connIndex >= 0) {
          entity.connections[connIndex].reason = entry.data.reason;
        }
      }
    }
  });
  
  // Add filtered history to the entity
  entity.history = organizeHistoryBySession(sortedEntries);
  
  return entity;
}

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

// Get all sessions
export function getAllSessions() {
  // Get and sort sessions
  const sortedSessions = historyBasedDataExpanded.sessions.sort((a, b) => {
    // Get session number from ID
    const aNum = parseInt(a.id.split('-')[1]) || -1;
    const bNum = parseInt(b.id.split('-')[1]) || -1;
    return bNum - aNum; // Sort in descending order (newest first)
  });
  
  // Transform sessions to match expected properties in the Vue component
  return sortedSessions.map(session => {
    // Generate highlights based on the session
    const highlights = generateSessionHighlights(session.id);
    
    // Convert the data to the format expected by the UI
    return {
      id: session.id,
      title: session.title,
      date: session.date,
      subtitle: session.subtitle || '',
      description: session.summary, // Map summary to description
      upcoming: false, // Default to false, set true for future sessions
      highlights: highlights // Add the highlights
    };
  });
}

// Generate session highlights based on significant events
function generateSessionHighlights(sessionId) {
  const sessionNum = parseInt(sessionId.split('-')[1]) || 0;
  
  // Return preset highlights based on session ID
  switch(sessionId) {
    case 'session-0':
      return [
        'Established the main party and key NPCs',
        'Documented important locations and their connections',
        'Inventoried significant items and their origins'
      ];
    case 'session-1':
      return [
        'Investigated the Silent Mire Ruins',
        'Encountered and disabled an Ancient Guardian construct',
        'Recovered a flickering Data Shard',
        'Repelled forces loyal to Kragnor'
      ];
    case 'session-2':
      return [
        'Delivered the Data Shard to Lord Silverhand',
        'Received cryptic prophecy from the Oracle of Nexus',
        'Encountered Morana Shadowweaver who warned about the Oracle',
        'Learned about the "Prophecy of Convergence"'
      ];
    default:
      // For any other session, generate generic highlights based on important events
      const events = getAllSessionRelatedEvents(sessionId);
      const highlights = [];
      
      // Look for significant event types
      const creationEvents = events.filter(e => e.changeType === 'creation');
      const connectionEvents = events.filter(e => e.changeType.includes('connection'));
      
      // Add creation highlights
      if (creationEvents.length > 0) {
        const entityTypes = new Set(creationEvents.filter(e => e.data.entityType).map(e => e.data.entityType));
        if (entityTypes.size > 0) {
          highlights.push(`Discovered ${Array.from(entityTypes).join(', ')}s`);
        }
      }
      
      // Add connection highlights
      if (connectionEvents.length > 0) {
        highlights.push(`Established new relationships between characters and the world`);
      }
      
      return highlights;
  }
}

// Get a specific session
export function getSession(id) {
  return historyBasedDataExpanded.sessions.find(session => session.id === id);
}

// Getter functions - now unified across data sources
export async function getLocations(type = null) {
  const locations = getAllEntities('location');
  if (type) {
    return locations.filter(loc => loc.type === type);
  }
  return locations;
}

export async function getLocation(id) {
  return buildEntityFromHistory('location', id);
}

export async function getCharacter(id) {
  return buildEntityFromHistory('character', id);
}

export async function getNpc(id) {
  return buildEntityFromHistory('npc', id);
}

export async function getItem(id) {
  return buildEntityFromHistory('item', id);
}

// Entity retrieval functions
export async function getEntity(type, id) {
  if (type === 'character') return await getCharacter(id);
  if (type === 'npc') return await getNpc(id);
  if (type === 'location') return await getLocation(id);
  if (type === 'item') return await getItem(id);
  if (type === 'session') return getSession(id);
  return null;
}

// Get all characters
export async function getAllCharacters() {
  return getAllEntities('character');
}

// Get all npcs
export async function getAllNpcs() {
  return getAllEntities('npc');
}

// Get all items 
export async function getAllItems() {
  return getAllEntities('item');
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

// Get all entities that changed in a specific session
export async function getSessionEntities(sessionId) {
  const events = getAllSessionRelatedEvents(sessionId);
  
  // Create a set of all affected entities
  const affectedEntities = new Set();
  
  events.forEach(event => {
    // For creation events, use the entity type from data
    if (event.changeType === 'creation' && event.data.entityType) {
      affectedEntities.add(`${event.data.entityType}:${event.entityId}`);
    } 
    // For other events, we need to determine the entity type
    else if (event.entityId) {
      // Find the entity's creation entry to get its type
      const entityType = getEntityTypeFromId(event.entityId);
      if (entityType) {
        affectedEntities.add(`${entityType}:${event.entityId}`);
      }
    }
    
    // Also track connected entities
    if (event.changeType.includes('connection') && event.data.connectedEntityType) {
      affectedEntities.add(`${event.data.connectedEntityType}:${event.data.connectedEntityId}`);
    }
  });
  
  // Convert the set back to an array of entity objects
  return Array.from(affectedEntities).map(entityKey => {
    const [type, id] = entityKey.split(':');
    return {
      type,
      id,
      entity: buildEntityFromHistory(type, id)
    };
  }).filter(item => item.entity !== null); // Filter out null entities
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
  getSessionEntities,
  worldHistory,
  // New history-based functions
  buildEntityFromHistory,
  getAllEntities,
  getEntityEvents,
  getAllSessionRelatedEvents,
  getEntityAtSession,
  getEntityTypeFromId  // Add this function to the default export as well
};

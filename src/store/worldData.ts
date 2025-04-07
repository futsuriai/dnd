// Central data store for world information using history-based event sourcing
// This file acts as an adapter between the history-based data model and the rest of the application

import { historyBasedDataExpanded } from './consolidatedData';
import firestoreService from '../services/FirestoreService';
import { worldHistory } from './worldHistory';

// Define TypeScript interfaces for our data structures
export interface HistoryEntry {
  entityId: string;
  sessionId: string;
  changeType: 'creation' | 'update' | 'deletion' | 'connection_added' | 'connection_removed' | 'connection_updated';
  timestamp: string;
  editedBy?: string;
  data: {
    entityType?: string;
    [key: string]: any;
  };
}

export interface Session {
  id: string;
  title: string;
  date: string;
  subtitle?: string;
  description?: string;
  summary?: string;
  upcoming?: boolean;
  highlights?: string[];
  [key: string]: any;
}

export interface EntityConnection {
  type: string;
  id: string;
  reason: string;
  sessionId: string;
}

export interface Entity {
  id: string;
  entityType: string;
  name?: string;
  deleted?: boolean;
  connections?: EntityConnection[];
  history?: SessionHistory[];
  [key: string]: any;
}

export interface SessionHistory {
  sessionId: string;
  events: {
    type: string;
    description: string;
    timestamp: string;
    changes: any;
  }[];
}

export interface DisplayConnection {
  name: string;
  id: string;
  reason: string;
  entityType: string;
  sessionId: string;
}

export interface SessionEntity {
  type: string;
  id: string;
  entity: Entity | null;
}

export interface DataSource {
  source: string;
  initialized: boolean;
}

// State tracking for data source
let useFirestore = false;
let isInitialized = false;
let dataSource = 'local';

// Cache for Firestore history entries
let firestoreHistoryCache: HistoryEntry[] | null = null;
let firestoreSessionsCache: Session[] | null = null;

// HISTORY DATA PROCESSING FUNCTIONS

// Get all history entries (either from local data or Firestore)
async function getAllHistoryEntries(): Promise<HistoryEntry[]> {
  if (useFirestore) {
    if (!firestoreHistoryCache) {
      firestoreHistoryCache = (await firestoreService.getAllHistoryEvents()).map(doc => ({
        entityId: doc.entityId,
        sessionId: doc.sessionId,
        changeType: doc.changeType,
        timestamp: doc.timestamp,
        editedBy: doc.editedBy,
        data: doc.data
      })) as HistoryEntry[];
    }
    return firestoreHistoryCache;
  } else {
    return historyBasedDataExpanded.historyEntries;
  }
}

// Get all sessions (either from local data or Firestore)
async function getAllSessionsData(): Promise<Session[]> {
  if (useFirestore) {
    if (!firestoreSessionsCache) {
      firestoreSessionsCache = (await firestoreService.getAllSessions()).map(doc => ({
        id: doc.id,
        title: doc.title,
        date: doc.date,
        subtitle: doc.subtitle || '',
        description: doc.description || '',
        summary: doc.summary || '',
        upcoming: doc.upcoming || false,
        highlights: doc.highlights || []
      })) as Session[];
    }
    return firestoreSessionsCache;
  } else {
    return historyBasedDataExpanded.sessions;
  }
}

// Clear cache to ensure fresh data on next load
export function clearCache(): void {
  firestoreHistoryCache = null;
  firestoreSessionsCache = null;
}

// Build an entity from history entries
export async function buildEntityFromHistory(entityType: string, entityId: string): Promise<Entity | null> {
  // Get all history entries
  const allHistoryEntries = await getAllHistoryEntries();
  
  // Get all history entries for this entity
  const entries = allHistoryEntries.filter(
    entry => entry.entityId === entityId && 
           (entry.changeType === 'creation' && entry.data.entityType === entityType)
  );
  
  // Also include update entries that target this entity
  const updateEntries = allHistoryEntries.filter(
    entry => entry.entityId === entityId && 
            entry.changeType !== 'creation'
  );
  
  // Combine creation and update entries
  const allEntries = [...entries, ...updateEntries];
  
  if (allEntries.length === 0) return null;
  
  // Start with an empty entity
  const entity: Entity = { id: entityId, entityType };
  
  // Process entries in chronological order (by session ID and timestamp)
  const sortedEntries = allEntries.sort((a, b) => {
    // First sort by session ID
    const aSession = parseInt(a.sessionId.split('-')[1]) || 0;
    const bSession = parseInt(b.sessionId.split('-')[1]) || 0;
    
    if (aSession !== bSession) return aSession - bSession;
    
    // Then by timestamp if in the same session
    return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
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
    else if (entry.changeType === 'deletion') {
      // Mark entity as deleted
      entity.deleted = true;
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
  
  // Don't return deleted entities
  if (entity.deleted) return null;
  
  // Add history to the entity
  entity.history = await organizeHistoryBySession(sortedEntries);
  
  return entity;
}

// Organize history entries by session for UI display
export async function organizeHistoryBySession(entries: HistoryEntry[]): Promise<SessionHistory[]> {
  const sessionMap = new Map<string, SessionHistory>();
  
  for (const entry of entries) {
    if (!sessionMap.has(entry.sessionId)) {
      sessionMap.set(entry.sessionId, {
        sessionId: entry.sessionId,
        events: []
      });
    }
    
    // Create a user-friendly event description
    let description = '';
    
    if (entry.changeType === 'creation') {
      description = `${capitalizeFirst(entry.data.entityType || '')} was created`;
    } else if (entry.changeType === 'update') {
      const entityType = entry.data.entityType || await getEntityTypeFromId(entry.entityId);
      description = `${capitalizeFirst(entityType)} was updated`;
      
      // Add details about what was updated if available
      if (entry.data && entry.data.last_action) {
        description = entry.data.last_action;
      } else if (entry.data && entry.data.status) {
        description = `Status changed to: ${entry.data.status}`;
      }
    } else if (entry.changeType === 'deletion') {
      description = 'Entity was deleted';
    } else if (entry.changeType === 'connection_added') {
      const targetType = capitalizeFirst(entry.data.connectedEntityType);
      const targetName = await getEntityNameFromId(entry.data.connectedEntityType, entry.data.connectedEntityId);
      description = `Connected to ${targetType} "${targetName}": ${entry.data.reason}`;
    } else if (entry.changeType === 'connection_removed') {
      const targetType = capitalizeFirst(entry.data.connectedEntityType);
      const targetName = await getEntityNameFromId(entry.data.connectedEntityType, entry.data.connectedEntityId);
      description = `Connection to ${targetType} "${targetName}" was removed`;
    } else if (entry.changeType === 'connection_updated') {
      const targetType = capitalizeFirst(entry.data.connectedEntityType);
      const targetName = await getEntityNameFromId(entry.data.connectedEntityType, entry.data.connectedEntityId);
      description = `Updated connection to ${targetType} "${targetName}": ${entry.data.reason}`;
    }
    
    const session = sessionMap.get(entry.sessionId);
    if (session) {
      session.events.push({
        type: entry.changeType.split('_')[0], // Simplify the type for CSS
        description: description,
        timestamp: entry.timestamp || new Date().toISOString(),
        changes: entry.data
      });
    }
  }
  
  // Convert to array and sort by session ID
  return Array.from(sessionMap.values()).sort((a, b) => {
    const aSession = parseInt(a.sessionId.split('-')[1]) || 0;
    const bSession = parseInt(b.sessionId.split('-')[1]) || 0;
    return bSession - aSession; // Sort from newest to oldest
  });
}

// Get entity name from ID (for better history descriptions)
export async function getEntityNameFromId(entityType: string, entityId: string): Promise<string> {
  // Get all history entries
  const allHistoryEntries = await getAllHistoryEntries();
  
  // Look for creation entries to get entity names
  const creationEntry = allHistoryEntries.find(
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
export async function getEntityTypeFromId(entityId: string): Promise<string> {
  // Get all history entries
  const allHistoryEntries = await getAllHistoryEntries();
  
  const creationEntry = allHistoryEntries.find(
    entry => entry.entityId === entityId && entry.changeType === 'creation'
  );
  
  if (creationEntry && creationEntry.data && creationEntry.data.entityType) {
    return creationEntry.data.entityType;
  }
  
  return 'entity'; // Default fallback
}

// Utility function to capitalize first letter
export function capitalizeFirst(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

// Get all entities of a specific type
export async function getAllEntities(entityType: string): Promise<Entity[]> {
  // Get all history entries
  const allHistoryEntries = await getAllHistoryEntries();
  
  // Get unique entity IDs of this type by checking creation entries
  const entityIds = [...new Set(
    allHistoryEntries
      .filter(entry => entry.changeType === 'creation' && entry.data.entityType === entityType)
      .map(entry => entry.entityId)
  )];
  
  // Build each entity from history in parallel
  const entities = await Promise.all(
    entityIds.map(id => buildEntityFromHistory(entityType, id))
  );
  
  // Remove null entities (e.g., deleted ones) and sort by name
  return entities
    .filter((entity): entity is Entity => entity !== null)
    .sort((a, b) => (a.name || '').localeCompare(b.name || '')); 
}

// Get all events related to a specific entity
export async function getEntityEvents(entityType: string, entityId: string): Promise<HistoryEntry[]> {
  // Get all history entries
  const allHistoryEntries = await getAllHistoryEntries();
  
  // First find if the entity exists with the correct type
  const creationEntry = allHistoryEntries.find(
    entry => entry.entityId === entityId && 
            entry.changeType === 'creation' && 
            entry.data.entityType === entityType
  );
  
  if (!creationEntry) return [];
  
  // If entity exists, get all its events
  return allHistoryEntries.filter(
    entry => entry.entityId === entityId
  );
}

// Get all events related to a specific session
export async function getAllSessionRelatedEvents(sessionId: string): Promise<HistoryEntry[]> {
  // Get all history entries
  const allHistoryEntries = await getAllHistoryEntries();
  
  return allHistoryEntries.filter(
    entry => entry.sessionId === sessionId
  );
}

// Get entity as it appeared at a specific session
export async function getEntityAtSession(entityType: string, entityId: string, sessionId: string): Promise<Entity | null> {
  // Get all history entries
  const allHistoryEntries = await getAllHistoryEntries();
  
  // Get the session number for comparison
  const targetSessionNum = parseInt(sessionId.split('-')[1]) || 0;
  
  // First check if entity exists with correct type
  const creationEntry = allHistoryEntries.find(
    entry => entry.entityId === entityId && 
            entry.changeType === 'creation' && 
            entry.data.entityType === entityType
  );
  
  if (!creationEntry) return null;
  
  // Get all history entries for this entity up to the specified session
  const entries = allHistoryEntries.filter(
    entry => {
      const entrySessionNum = parseInt(entry.sessionId.split('-')[1]) || 0;
      return entry.entityId === entityId && entrySessionNum <= targetSessionNum;
    }
  );
  
  if (entries.length === 0) return null;
  
  // Build entity with just these entries
  const entity: Entity = { id: entityId, entityType };
  
  // Process entries in chronological order
  const sortedEntries = entries.sort((a, b) => {
    const aSession = parseInt(a.sessionId.split('-')[1]) || 0;
    const bSession = parseInt(b.sessionId.split('-')[1]) || 0;
    
    if (aSession !== bSession) return aSession - bSession;
    
    // Then by timestamp if in the same session
    return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
  });
  
  // Apply each entry to build the entity (same logic as buildEntityFromHistory)
  sortedEntries.forEach(entry => {
    if (entry.changeType === 'creation') {
      Object.assign(entity, entry.data);
    } 
    else if (entry.changeType === 'update') {
      Object.assign(entity, entry.data);
    }
    else if (entry.changeType === 'deletion') {
      entity.deleted = true;
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
  
  // Don't return deleted entities
  if (entity.deleted) return null;
  
  // Add filtered history to the entity
  entity.history = await organizeHistoryBySession(sortedEntries);
  
  return entity;
}

// Initialize function to determine whether to use Firestore or local data
export async function initWorldData(options: { forceInit?: boolean } = {}): Promise<string> {
  if (isInitialized && !options.forceInit) return dataSource;
  
  try {
    // Clear cache
    clearCache();
    
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

// Create a new history entry (in Firestore or local cache temporarily)
export async function createHistoryEntry(entryData: HistoryEntry): Promise<void> {
  if (useFirestore) {
    // Add to Firestore
    await firestoreService.createHistoryEntry(entryData);
    
    // Clear cache to ensure fresh data on next load
    clearCache();
  } else {
    // Add to local cache (warning: this is temporary and will be lost on refresh)
    historyBasedDataExpanded.historyEntries.push(entryData);
  }
}

// Get all sessions
export async function getAllSessions(): Promise<Session[]> {
  // Get all sessions data
  const allSessions = await getAllSessionsData();
  
  // Sort sessions
  const sortedSessions = allSessions.sort((a, b) => {
    // Get session number from ID
    const aNum = parseInt(a.id.split('-')[1]) || -1;
    const bNum = parseInt(b.id.split('-')[1]) || -1;
    return bNum - aNum; // Sort in descending order (newest first)
  });
  
  // Transform sessions to match expected properties in the Vue component
  return sortedSessions.map(session => {
    // Convert the data to the format expected by the UI
    return {
      id: session.id,
      title: session.title,
      date: session.date,
      subtitle: session.subtitle || '',
      description: session.summary || session.description, // Map summary to description
      upcoming: !!session.upcoming, // Ensure boolean
      highlights: session.highlights || [] // Ensure array
    };
  });
}

// Get a specific session
export async function getSession(id: string): Promise<Session | undefined> {
  const allSessions = await getAllSessionsData();
  return allSessions.find(session => session.id === id);
}

// Getter functions - now unified across data sources
export async function getLocations(type: string | null = null): Promise<Entity[]> {
  const locations = await getAllEntities('location');
  if (type) {
    return locations.filter(loc => loc.type === type);
  }
  return locations;
}

export async function getLocation(id: string): Promise<Entity | null> {
  return buildEntityFromHistory('location', id);
}

export async function getCharacter(id: string): Promise<Entity | null> {
  return buildEntityFromHistory('character', id);
}

export async function getNpc(id: string): Promise<Entity | null> {
  return buildEntityFromHistory('npc', id);
}

export async function getItem(id: string): Promise<Entity | null> {
  return buildEntityFromHistory('item', id);
}

// Entity retrieval functions
export async function getEntity(type: string, id: string): Promise<Entity | Session | null | undefined> {
  if (type === 'character') return await getCharacter(id);
  if (type === 'npc') return await getNpc(id);
  if (type === 'location') return await getLocation(id);
  if (type === 'item') return await getItem(id);
  if (type === 'session') return getSession(id);
  return null;
}

// Get all characters
export async function getAllCharacters(): Promise<Entity[]> {
  return getAllEntities('character');
}

// Get all npcs
export async function getAllNpcs(): Promise<Entity[]> {
  return getAllEntities('npc');
}

// Get all items 
export async function getAllItems(): Promise<Entity[]> {
  return getAllEntities('item');
}

// Connection functions
export async function getEntityConnections(type: string, id: string): Promise<DisplayConnection[]> {
  const entity = await getEntity(type, id);

  if (!entity || !('connections' in entity) || !entity.connections) return [];

  const connectionPromises = entity.connections.map(async conn => {
    const connectedEntity = await getEntity(conn.type, conn.id);

    if (connectedEntity && 'name' in connectedEntity) {
      return {
        name: connectedEntity.name || 'Unknown',
        id: connectedEntity.id,
        reason: conn.reason,
        entityType: conn.type,
        sessionId: conn.sessionId // Include when the connection was established
      };
    }
    return null;
  });

  const connections = await Promise.all(connectionPromises);
  return connections.filter((conn): conn is DisplayConnection => conn !== null);
}

// Get all entities that changed in a specific session
export async function getSessionEntities(sessionId: string): Promise<SessionEntity[]> {
  const events = await getAllSessionRelatedEvents(sessionId);
  
  // Create a set of all affected entities
  const affectedEntities = new Set<string>();
  
  events.forEach(event => {
    // For creation events, use the entity type from data
    if (event.changeType === 'creation' && event.data.entityType) {
      affectedEntities.add(`${event.data.entityType}:${event.entityId}`);
    } 
    // For other events, we need to determine the entity type
    else if (event.entityId) {
      // We'll use the async function later when processing the set
      affectedEntities.add(`unknown:${event.entityId}`);
    }
    
    // Also track connected entities
    if (event.changeType.includes('connection') && event.data.connectedEntityType) {
      affectedEntities.add(`${event.data.connectedEntityType}:${event.data.connectedEntityId}`);
    }
  });
  
  // Convert the set back to an array of entity promises
  const entityPromises = Array.from(affectedEntities).map(async entityKey => {
    let [type, id] = entityKey.split(':');
    
    // If type is unknown, determine it
    if (type === 'unknown') {
      type = await getEntityTypeFromId(id);
    }
    
    // Build the entity
    const entity = await buildEntityFromHistory(type, id);
    
    return {
      type,
      id,
      entity
    };
  });
  
  // Resolve all promises
  const entities = await Promise.all(entityPromises);
  
  // Filter out null entities (e.g., deleted ones)
  return entities.filter(item => item.entity !== null);
}

// Get current data source
export function getDataSource(): DataSource {
  return { source: dataSource, initialized: isInitialized };
}

// Methods for creating and updating history entries
export async function createEntity(entityType: string, entityData: any): Promise<string> {
  const timestamp = new Date().toISOString();
  const sessionId = entityData.sessionId || 'session-admin'; // Default to admin session
  
  // Ensure the entity has an ID
  const entityId = entityData.id || `${entityType}-${Date.now()}`;
  
  // Create the history entry
  const historyEntry: HistoryEntry = {
    entityId,
    sessionId,
    changeType: 'creation',
    timestamp,
    editedBy: entityData.editedBy || 'admin',
    data: {
      ...entityData,
      id: entityId,
      entityType
    }
  };
  
  // Add to history
  await createHistoryEntry(historyEntry);
  
  return entityId;
}

export async function updateEntity(entityType: string, entityId: string, updateData: any): Promise<string> {
  const timestamp = new Date().toISOString();
  const sessionId = updateData.sessionId || 'session-admin'; // Default to admin session
  
  // Create the history entry
  const historyEntry: HistoryEntry = {
    entityId,
    sessionId,
    changeType: 'update',
    timestamp,
    editedBy: updateData.editedBy || 'admin',
    data: {
      ...updateData,
      entityType
    }
  };
  
  // Add to history
  await createHistoryEntry(historyEntry);
  
  return entityId;
}

export async function deleteEntity(entityType: string, entityId: string): Promise<boolean> {
  const timestamp = new Date().toISOString();
  const sessionId = 'session-admin'; // Default to admin session
  
  // Create the history entry
  const historyEntry: HistoryEntry = {
    entityId,
    sessionId,
    changeType: 'deletion',
    timestamp,
    editedBy: 'admin',
    data: {
      entityType
    }
  };
  
  // Add to history
  await createHistoryEntry(historyEntry);
  
  return true;
}

export async function addEntityConnection(
  entityType: string, 
  entityId: string, 
  connectedType: string, 
  connectedId: string, 
  reason: string
): Promise<boolean> {
  const timestamp = new Date().toISOString();
  const sessionId = 'session-admin'; // Default to admin session
  
  // Create the history entry
  const historyEntry: HistoryEntry = {
    entityId,
    sessionId,
    changeType: 'connection_added',
    timestamp,
    editedBy: 'admin',
    data: {
      entityType,
      connectedEntityType: connectedType,
      connectedEntityId: connectedId,
      reason
    }
  };
  
  // Add to history
  await createHistoryEntry(historyEntry);
  
  return true;
}

export async function removeEntityConnection(
  entityType: string, 
  entityId: string, 
  connectedType: string, 
  connectedId: string
): Promise<boolean> {
  const timestamp = new Date().toISOString();
  const sessionId = 'session-admin'; // Default to admin session
  
  // Create the history entry
  const historyEntry: HistoryEntry = {
    entityId,
    sessionId,
    changeType: 'connection_removed',
    timestamp,
    editedBy: 'admin',
    data: {
      entityType,
      connectedEntityType: connectedType,
      connectedEntityId: connectedId
    }
  };
  
  // Add to history
  await createHistoryEntry(historyEntry);
  
  return true;
}

// Get latest non-upcoming session ID for use as default when creating/updating entities
export async function getLatestSessionId(): Promise<string> {
  // Get all sessions
  const allSessions = await getAllSessionsData();
  
  // Filter out upcoming sessions
  const nonUpcomingSessions = allSessions.filter(session => !session.upcoming);
  
  if (nonUpcomingSessions.length > 0) {
    // Sort by session number (descending order)
    nonUpcomingSessions.sort((a, b) => {
      const aNum = parseInt(a.id.split('-')[1]) || 0;
      const bNum = parseInt(b.id.split('-')[1]) || 0;
      return bNum - aNum; // Descending order (newest first)
    });
    
    // Return the latest session ID
    return nonUpcomingSessions[0].id;
  }
  
  // If no non-upcoming sessions exist, return 'session-1' as default
  return 'session-1';
}

// Export worldHistory to ensure compatibility with the old JS file
export { worldHistory };

// Export default worldData object for easy importing
const worldData = {
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
  // Event sourcing methods
  createEntity,
  updateEntity,
  deleteEntity,
  addEntityConnection,
  removeEntityConnection,
  // History-based functions
  buildEntityFromHistory,
  getAllEntities,
  getEntityEvents,
  getAllSessionRelatedEvents,
  getEntityAtSession,
  getEntityTypeFromId,
  // Extra utilities made available
  clearCache,
  capitalizeFirst,
  getEntityNameFromId,
  organizeHistoryBySession,
  getLatestSessionId
};

export default worldData;
import { ref, computed } from 'vue';
import firestoreService from '../services/FirestoreService';

// Main entity store
const entities = ref({
  characters: {},
  npcs: {},
  locations: {},
  items: {},
  sessions: {}
});

// Entity-session relationships (which entities were affected in which sessions)
const sessionEntities = ref({});

// Session-ordered history to track all changes
const entityHistory = ref([]);

// Flag for data source
const dataSource = ref('local');
const isInitialized = ref(false);

/**
 * Entity Schema:
 * {
 *   id: String,                  // Unique identifier
 *   type: String,                // 'character', 'npc', 'location', 'item'
 *   name: String,                // Display name
 *   description: String,         // General description
 *   // Type-specific fields based on entity type
 *   ...typeSpecificFields,
 *   history: [                   // History of changes
 *     {
 *       sessionId: String,       // Session when change occurred
 *       timestamp: Date,         // When the change happened
 *       type: String,            // 'create', 'update', 'connect'
 *       changes: Object,         // What was changed (new/modified fields)
 *       description: String      // Human-readable description of change
 *     }
 *   ],
 *   connections: [               // Relationships to other entities
 *     {
 *       entityId: String,        // ID of connected entity
 *       entityType: String,      // Type of connected entity
 *       reason: String,          // Description of connection
 *       sessionId: String,       // Session when connection was made
 *       isActive: Boolean        // Whether connection is still active
 *     }
 *   ]
 * }
 */

// Consolidated entity data format for Firestore export and local use
export const consolidatedEntities = {
  sessions: [
    {
      id: 'session-minus-1',
      title: 'Initial Setup',
      date: '2025-04-02',
      description: 'Initial setup of the world and entities.',
      entities: {
        characters: [
          {
            id: 'thorne',
            name: 'Thorne Ironheart',
            player: 'Player Name 1',
            race: 'Dwarf',
            class: 'Paladin',
            level: 5,
            background: 'Relic Hunter',
            bio: 'Born into a family of traditional relic hunters, Thorne discovered ancient armor in the ruins of Thaumanar that bonded to him, granting him paladin abilities. He seeks to fulfill the Prophecy of Convergence.',
            dndBeyondLink: 'https://www.dndbeyond.com/characters/123456',
            connections: [
              { type: 'location', id: 'thaumanar', reason: 'Discovered ancient armor in the ruins that bonded to him, granting paladin abilities.' },
              { type: 'location', id: 'oracle-nexus', reason: 'Visited the Oracle to learn more about his ancient armor and received a cryptic prophecy.' },
              { type: 'npc', id: 'silverhand', reason: 'Silverhand has hired Thorne multiple times for relic hunting expeditions.' }
            ]
          },
          // ...other characters
        ],
        npcs: [
          {
            id: 'silverhand',
            name: 'Lord Bartholomew Silverhand',
            location: 'Spire Central',
            role: 'High Councilor & Oracle Interpreter',
            description: 'A distinguished noble descended from the Luminar Dynasty, Silverhand claims partial Ancient bloodline. He leads excavation efforts at Active Nodes and consults regularly with the Oracle of Nexus.',
            status: 'Ally',
            connections: [
              { type: 'location', id: 'spire-central', reason: 'Leads the High Council that governs from Spire Central.' },
              { type: 'character', id: 'thorne', reason: 'Has hired Thorne multiple times for relic hunting expeditions.' },
              { type: 'character', id: 'brom', reason: 'Sees Brom as potentially dangerous due to his knowledge of a disturbing Oracle prophecy.' },
              { type: 'location', id: 'oracle-nexus', reason: 'Official interpreter of the Oracle\'s messages for the Seven Spires Confederation.' },
              { type: 'location', id: 'nexus', reason: 'Maintains a residence in the city to stay close to the Oracle.' }
            ]
          },
          // ...other NPCs
        ],
        locations: [
          {
            id: 'thaumanar',
            name: 'Thaumanar',
            type: 'city',
            subtype: 'magic',
            region: 'Eastern Spire Territory',
            description: 'The first major settlement established after the Restoration, built around the Whispering Spires. Known for its ancient architecture and the Wielders Guild headquarters. The city\'s foundations incorporate Ancient technology that still hums with power.',
            connections: [
              { type: 'character', id: 'thorne', reason: 'Where Thorne discovered ancient armor that bonded to him, granting paladin abilities.' },
              { type: 'npc', id: 'grimshaw', reason: 'Grimshaw operates a secret shop in the lower districts selling rare relics.' }
            ]
          },
          // ...other locations
        ],
        items: [
          {
            id: 'frostbite-blade',
            name: 'Frostbite Blade',
            type: 'Ancient Weapon (Ethereal Edge)',
            rarity: 'Rare',
            attunement: 'Required (Bloodline Affinity)',
            description: 'A longsword that appears to be made of translucent blue ice. Analysis suggests it\'s actually a fragment of the Ethereal Lattice, crystallized during the Sundering. It deals an additional 1d6 cold damage and slows targets by manipulating local temporal flow.',
            found: 'Recovered from an Active Node in the former Frozen Wastes, now the Crimson Desert',
            owner: 'Thorne Ironheart',
            connections: [
              { type: 'character', id: 'thorne', reason: 'Currently wielded by Thorne after it bonded with his paladin abilities.' },
              { type: 'location', id: 'crimson-desert', reason: 'Found in the depths of this Active Node, suggesting a link to the original Frozen Wastes.' }
            ]
          },
          // ...other items
        ]
      }
    },
    // ...other sessions
  ]
};

// Initialize the store and determine data source
async function initEntityStore(options = {}) {
  if (isInitialized.value && !options.forceInit) return dataSource.value;
  
  try {
    // If seeding is requested, do that first
    if (options.seedDatabase) {
      console.log('Seeding Firestore database...');
      await seedFirestore();
    }
    
    // Try to get sessions from Firestore to determine if we should use it
    const sessions = await firestoreService.getAllSessions();
    if (sessions && sessions.length > 0) {
      console.log('Using Firestore as data source');
      await loadFromFirestore();
      dataSource.value = 'firestore';
    } else {
      console.log('Using local data files as data source');
      await loadFromLocalFiles();
      dataSource.value = 'local';
    }
    
    isInitialized.value = true;
    return dataSource.value;
  } catch (error) {
    console.error('Error initializing entity store, falling back to local data:', error);
    await loadFromLocalFiles();
    dataSource.value = 'local';
    isInitialized.value = true;
    return dataSource.value;
  }
}

// Load entities from local files
async function loadFromLocalFiles() {
  // Import all the local data files
  const { characters } = await import('./characters.js');
  const { npcs } = await import('./npcs.js');
  const { locations } = await import('./locations.js');
  const { items } = await import('./items.js');
  const { sessions } = await import('./sessions.js');
  
  // Import all events
  const { characterEvents } = await import('./characterEvents.js');
  const { npcEvents } = await import('./npcEvents.js');
  const { locationEvents } = await import('./locationEvents.js');
  const { itemEvents } = await import('./itemEvents.js');
  
  // Combine all events
  const allEvents = [
    ...characterEvents,
    ...npcEvents,
    ...locationEvents,
    ...itemEvents
  ].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
  
  // Set to entity history
  entityHistory.value = allEvents;
  
  // Process entities
  processEntities('character', characters);
  processEntities('npc', npcs);
  processEntities('location', locations);
  processEntities('item', items);
  processEntities('session', sessions);
  
  // Process session-entity relationships
  buildSessionEntityRelationships();
}

// Process entities into the new structure
function processEntities(type, entityList) {
  entityList.forEach(entity => {
    // Get relevant events for this entity
    const relevantEvents = entityHistory.value.filter(
      event => event.entityType === type && event.entityId === entity.id
    );
    
    // Extract history
    const history = relevantEvents.map(event => ({
      sessionId: event.sessionId,
      timestamp: event.timestamp,
      type: event.type,
      changes: event.data || {},
      description: event.description
    }));
    
    // Extract connections
    const connections = entityHistory.value
      .filter(event => 
        event.type === 'connect' && 
        event.entityType === type && 
        event.entityId === entity.id
      )
      .map(event => ({
        entityId: event.targetEntityId,
        entityType: event.targetEntityType,
        reason: event.data?.reason || '',
        sessionId: event.sessionId,
        isActive: true
      }));
    
    // Create entity with history and connections
    const newEntity = {
      ...entity,
      type,
      history,
      connections
    };
    
    // Add to the store
    entities.value[type + 's'][entity.id] = newEntity;
  });
}

// Build relationships between sessions and entities
function buildSessionEntityRelationships() {
  // Initialize session entities
  entities.value.sessions = {}; // Reset
  
  // Process all history events
  entityHistory.value.forEach(event => {
    const { sessionId, entityType, entityId, type: eventType } = event;
    
    // Skip if not related to a session
    if (!sessionId) return;
    
    // Ensure session exists in entities.sessions 
    if (!entities.value.sessions[sessionId]) {
      // Create session entry if we find it in events but not in sessions list
      const sessionData = {
        id: sessionId,
        title: `Session ${sessionId.split('-')[1]}`,
        date: new Date(event.timestamp).toISOString().split('T')[0],
        description: 'Session details not found',
        type: 'session',
        history: [],
        connections: []
      };
      entities.value.sessions[sessionId] = sessionData;
    }
    
    // Initialize session entities map if needed
    if (!sessionEntities.value[sessionId]) {
      sessionEntities.value[sessionId] = {
        characters: new Set(),
        npcs: new Set(),
        locations: new Set(),
        items: new Set()
      };
    }
    
    // Add entity to session's entity list
    if (entityType !== 'session' && entityId) {
      sessionEntities.value[sessionId][entityType + 's'].add(entityId);
    }
    
    // For connect events, add both entities
    if (eventType === 'connect' && event.targetEntityType && event.targetEntityId) {
      sessionEntities.value[sessionId][event.targetEntityType + 's'].add(event.targetEntityId);
    }
  });
  
  // Convert Sets to arrays for easier consumption
  Object.keys(sessionEntities.value).forEach(sessionId => {
    const session = sessionEntities.value[sessionId];
    Object.keys(session).forEach(entityType => {
      sessionEntities.value[sessionId][entityType] = Array.from(session[entityType]);
    });
  });
}

// Load entities from Firestore
async function loadFromFirestore() {
  try {
    // Get all entities from Firestore
    const characters = await firestoreService.getAllCharacters();
    const npcs = await firestoreService.getAllNpcs();
    const locations = await firestoreService.getAllLocations();
    const items = await firestoreService.getAllItems();
    const sessions = await firestoreService.getAllSessions();
    const allEvents = await firestoreService.getAllHistoryEvents();
    
    // Sort events by timestamp
    entityHistory.value = allEvents.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    
    // Process entities
    entities.value.characters = Object.fromEntries(characters.map(char => [char.id, {...char, type: 'character'}]));
    entities.value.npcs = Object.fromEntries(npcs.map(npc => [npc.id, {...npc, type: 'npc'}]));
    entities.value.locations = Object.fromEntries(locations.map(loc => [loc.id, {...loc, type: 'location'}]));
    entities.value.items = Object.fromEntries(items.map(item => [item.id, {...item, type: 'item'}]));
    entities.value.sessions = Object.fromEntries(sessions.map(session => [session.id, {...session, type: 'session'}]));
    
    // Build session-entity relationships
    buildSessionEntityRelationships();
    
  } catch (error) {
    console.error('Error loading from Firestore:', error);
    throw error;
  }
}

// For export to Firestore from the admin panel
async function exportToFirestore() {
  if (!isInitialized.value) await initEntityStore();
  
  try {
    // Clear existing data (optional - might want confirmation from user first)
    await firestoreService.clearDatabase();
    
    // Prepare export data
    const exportData = {
      characters: Object.values(entities.value.characters),
      npcs: Object.values(entities.value.npcs),
      locations: Object.values(entities.value.locations),
      items: Object.values(entities.value.items),
      sessions: Object.values(entities.value.sessions),
      historyEvents: entityHistory.value
    };
    
    // Upload to Firestore
    await firestoreService.seedDatabase(exportData);
    
    // Update data source
    dataSource.value = 'firestore';
    
    return true;
  } catch (error) {
    console.error('Error exporting to Firestore:', error);
    throw error;
  }
}

// For seeding Firestore with initial data
async function seedFirestore() {
  // Load local data first
  await loadFromLocalFiles();
  
  // Then export to Firestore
  return exportToFirestore();
}

// Entity retrieval functions
function getEntity(type, id) {
  if (!entities.value[type + 's']) return null;
  return entities.value[type + 's'][id] || null;
}

// Get all entities of a specific type
function getAllEntities(type) {
  if (!entities.value[type + 's']) return [];
  return Object.values(entities.value[type + 's']);
}

// Get entities at a specific point in history (by session)
function getEntityAtSession(type, id, sessionId) {
  const entity = getEntity(type, id);
  if (!entity) return null;
  
  // Clone the entity
  const entityClone = {...entity};
  
  // Find the index of the session in history
  const sessionEvents = entity.history.filter(h => h.sessionId === sessionId);
  if (sessionEvents.length === 0) {
    // Entity didn't exist at this point
    return null;
  }
  
  // Find all history events up to and including this session
  const allEvents = entityHistory.value
    .filter(event => event.entityType === type && event.entityId === id)
    .filter(event => {
      // Compare session numbers for chronological ordering
      const eventSessionNum = parseInt(event.sessionId.split('-')[1]) || 0;
      const targetSessionNum = parseInt(sessionId.split('-')[1]) || 0;
      return eventSessionNum <= targetSessionNum;
    })
    .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
  
  // Build the entity as it existed at that point
  let entityAtSession = {
    id: entity.id,
    type: type,
    // Start with what we know from create event
    ...allEvents.find(e => e.type === 'create')?.data || {}
  };
  
  // Apply all update events up to the target session
  allEvents.filter(e => e.type === 'update').forEach(event => {
    entityAtSession = {...entityAtSession, ...event.data};
  });
  
  // Filter connections to only include those that existed at that point
  entityAtSession.connections = entity.connections.filter(conn => {
    const connSessionNum = parseInt(conn.sessionId.split('-')[1]) || 0;
    const targetSessionNum = parseInt(sessionId.split('-')[1]) || 0;
    return connSessionNum <= targetSessionNum;
  });
  
  return entityAtSession;
}

// Get all entities that changed in a specific session
function getSessionEntities(sessionId) {
  if (!sessionEntities.value[sessionId]) return {
    characters: [],
    npcs: [],
    locations: [],
    items: []
  };
  
  const sessionData = sessionEntities.value[sessionId];
  
  // Map IDs to actual entities
  return {
    characters: sessionData.characters.map(id => getEntity('character', id)).filter(Boolean),
    npcs: sessionData.npcs.map(id => getEntity('npc', id)).filter(Boolean),
    locations: sessionData.locations.map(id => getEntity('location', id)).filter(Boolean),
    items: sessionData.items.map(id => getEntity('item', id)).filter(Boolean)
  };
}

// Create a new entity
async function createEntity(type, entityData, sessionId) {
  if (!isInitialized.value) await initEntityStore();
  
  // Generate ID if not provided
  const id = entityData.id || `${type}-${Date.now()}`;
  
  // Create event object
  const event = {
    sessionId,
    timestamp: new Date().toISOString(),
    type: 'create',
    entityType: type,
    entityId: id,
    data: { id, ...entityData },
    description: `Added ${type}: ${entityData.name}`
  };
  
  // Add to history
  entityHistory.value.push(event);
  
  // Process entity
  const newEntity = {
    ...entityData,
    id,
    type,
    history: [{
      sessionId,
      timestamp: event.timestamp,
      type: 'create',
      changes: entityData,
      description: event.description
    }],
    connections: []
  };
  
  // Add to entities store
  entities.value[type + 's'][id] = newEntity;
  
  // Update session relationships
  if (!sessionEntities.value[sessionId]) {
    sessionEntities.value[sessionId] = {
      characters: [],
      npcs: [],
      locations: [],
      items: []
    };
  }
  sessionEntities.value[sessionId][type + 's'].push(id);
  
  // Update Firestore if using it
  if (dataSource.value === 'firestore') {
    await firestoreService.create(type + 's', newEntity);
    await firestoreService.createHistoryEvent(event);
  }
  
  return newEntity;
}

// Update an entity
async function updateEntity(type, id, updates, sessionId) {
  if (!isInitialized.value) await initEntityStore();
  
  const entity = getEntity(type, id);
  if (!entity) throw new Error(`Entity ${type}:${id} not found`);
  
  // Create event object
  const event = {
    sessionId,
    timestamp: new Date().toISOString(),
    type: 'update',
    entityType: type,
    entityId: id,
    data: updates,
    description: `Updated ${type}: ${entity.name}`
  };
  
  // Add to history
  entityHistory.value.push(event);
  
  // Update entity
  entities.value[type + 's'][id] = {
    ...entity,
    ...updates,
    history: [
      ...entity.history,
      {
        sessionId,
        timestamp: event.timestamp,
        type: 'update',
        changes: updates,
        description: event.description
      }
    ]
  };
  
  // Update session relationships
  if (!sessionEntities.value[sessionId]) {
    sessionEntities.value[sessionId] = {
      characters: [],
      npcs: [],
      locations: [],
      items: []
    };
  }
  if (!sessionEntities.value[sessionId][type + 's'].includes(id)) {
    sessionEntities.value[sessionId][type + 's'].push(id);
  }
  
  // Update Firestore if using it
  if (dataSource.value === 'firestore') {
    await firestoreService.update(type + 's', id, {
      ...updates,
      history: entities.value[type + 's'][id].history
    });
    await firestoreService.createHistoryEvent(event);
  }
  
  return entities.value[type + 's'][id];
}

// Connect two entities
async function connectEntities(sourceType, sourceId, targetType, targetId, reason, sessionId) {
  if (!isInitialized.value) await initEntityStore();
  
  const sourceEntity = getEntity(sourceType, sourceId);
  const targetEntity = getEntity(targetType, targetId);
  
  if (!sourceEntity) throw new Error(`Source entity ${sourceType}:${sourceId} not found`);
  if (!targetEntity) throw new Error(`Target entity ${targetType}:${targetId} not found`);
  
  // Create event object
  const event = {
    sessionId,
    timestamp: new Date().toISOString(),
    type: 'connect',
    entityType: sourceType,
    entityId: sourceId,
    targetEntityType: targetType,
    targetEntityId: targetId,
    data: { reason },
    description: `Connected ${sourceType} "${sourceEntity.name}" to ${targetType} "${targetEntity.name}"`
  };
  
  // Add to history
  entityHistory.value.push(event);
  
  // Create connection object
  const connection = {
    entityId: targetId,
    entityType: targetType,
    reason,
    sessionId,
    isActive: true
  };
  
  // Update source entity with connection
  entities.value[sourceType + 's'][sourceId] = {
    ...sourceEntity,
    connections: [...sourceEntity.connections, connection],
    history: [
      ...sourceEntity.history,
      {
        sessionId,
        timestamp: event.timestamp,
        type: 'connect',
        changes: { connection },
        description: event.description
      }
    ]
  };
  
  // Update session relationships
  if (!sessionEntities.value[sessionId]) {
    sessionEntities.value[sessionId] = {
      characters: [],
      npcs: [],
      locations: [],
      items: []
    };
  }
  
  // Add both entities to session
  if (!sessionEntities.value[sessionId][sourceType + 's'].includes(sourceId)) {
    sessionEntities.value[sessionId][sourceType + 's'].push(sourceId);
  }
  if (!sessionEntities.value[sessionId][targetType + 's'].includes(targetId)) {
    sessionEntities.value[sessionId][targetType + 's'].push(targetId);
  }
  
  // Update Firestore if using it
  if (dataSource.value === 'firestore') {
    await firestoreService.update(sourceType + 's', sourceId, {
      connections: entities.value[sourceType + 's'][sourceId].connections,
      history: entities.value[sourceType + 's'][sourceId].history
    });
    await firestoreService.createHistoryEvent(event);
  }
  
  return entities.value[sourceType + 's'][sourceId];
}

// Export all functions and reactivity
export default {
  // Reactive state
  entities: computed(() => entities.value),
  entityHistory: computed(() => entityHistory.value),
  sessionEntities: computed(() => sessionEntities.value),
  dataSource: computed(() => dataSource.value),
  isInitialized: computed(() => isInitialized.value),
  
  // Functions
  initEntityStore,
  getEntity,
  getAllEntities,
  getEntityAtSession,
  getSessionEntities,
  createEntity,
  updateEntity,
  connectEntities,
  exportToFirestore,
  
  // Specific entity getters for convenience
  getCharacter: (id) => getEntity('character', id),
  getNpc: (id) => getEntity('npc', id),
  getLocation: (id) => getEntity('location', id),
  getItem: (id) => getEntity('item', id),
  getSession: (id) => getEntity('session', id),
  
  getAllCharacters: () => getAllEntities('character'),
  getAllNpcs: () => getAllEntities('npc'),
  getAllLocations: () => getAllEntities('location'),
  getAllItems: () => getAllEntities('item'),
  getAllSessions: () => getAllEntities('session')
};

// Entity store module for components to access consolidated data

import { reactive } from 'vue';
import {
  getEntity,
  getAllSessions,
  getSession,
  getEntityAtSession,
  buildEntityFromHistory
} from './worldData.js';

// Simple reactive store for entity management
const entityStore = reactive({
  // Cache to prevent repeated rebuilding
  entityCache: new Map(),
  sessionCache: null,
  
  // Get an entity by type and ID
  async getEntity(type, id) {
    const cacheKey = `${type}:${id}`;
    
    // Check cache first
    if (this.entityCache.has(cacheKey)) {
      return this.entityCache.get(cacheKey);
    }
    
    // Fetch and cache
    const entity = await getEntity(type, id);
    this.entityCache.set(cacheKey, entity);
    return entity;
  },
  
  // Get all sessions
  async getAllSessions() {
    if (this.sessionCache) {
      return this.sessionCache;
    }
    
    this.sessionCache = await getAllSessions();
    return this.sessionCache;
  },
  
  // Get a specific session
  async getSession(id) {
    if (this.sessionCache) {
      const session = this.sessionCache.find(s => s.id === id);
      if (session) return session;
    }
    
    // If not in cache, fetch directly
    return await getSession(id);
  },
  
  // Get entity as it was at a specific session
  async getEntityAtSession(type, id, sessionId) {
    const cacheKey = `${type}:${id}:${sessionId}`;
    
    if (this.entityCache.has(cacheKey)) {
      return this.entityCache.get(cacheKey);
    }
    
    const entity = await getEntityAtSession(type, id, sessionId);
    this.entityCache.set(cacheKey, entity);
    return entity;
  },
  
  // Clear all caches
  clearCache() {
    this.entityCache.clear();
    this.sessionCache = null;
  }
});

export default entityStore;

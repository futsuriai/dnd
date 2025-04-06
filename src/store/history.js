// History data store - the main source of truth for all entity changes
// Uses an event-sourced model where entities are created and modified through session events

// Initial data import (will be converted to events)
import { characters as initialCharacters } from './characters.js';
import { npcs as initialNpcs } from './npcs.js';
import { locations as initialLocations } from './locations.js';
import { items as initialItems } from './items.js';
import { sessions as initialSessions } from './sessions.js';
import { worldHistory } from './worldHistory.js';

// History entries - chronological log of all changes to entities
export const historyEntries = [
  // Session 0 (website setup) - initial state setup
  // All existing entities will be created here with "session-minus-1" ID

  // Characters
  ...initialCharacters.map(character => ({
    sessionId: 'session-minus-1',
    timestamp: '2025-04-02',
    type: 'create',
    entityType: 'character',
    entityId: character.id,
    data: { ...character, connections: [] }, // Store initial state without connections
    description: `Added character: ${character.name}`
  })),

  // NPCs
  ...initialNpcs.map(npc => ({
    sessionId: 'session-minus-1',
    timestamp: '2025-04-02',
    type: 'create',
    entityType: 'npc',
    entityId: npc.id,
    data: { ...npc, connections: [] }, // Store initial state without connections
    description: `Added NPC: ${npc.name}`
  })),

  // Locations
  ...initialLocations.map(location => ({
    sessionId: 'session-minus-1',
    timestamp: '2025-04-02',
    type: 'create',
    entityType: 'location',
    entityId: location.id,
    data: { ...location, connections: [] }, // Store initial state without connections
    description: `Added location: ${location.name}`
  })),

  // Items
  ...initialItems.map(item => ({
    sessionId: 'session-minus-1',
    timestamp: '2025-04-02',
    type: 'create',
    entityType: 'item',
    entityId: item.id,
    data: { ...item, connections: [] }, // Store initial state without connections
    description: `Added item: ${item.name}`
  })),

  // Add connections as separate events
  // Characters connections
  ...initialCharacters.flatMap(character =>
    (character.connections || []).map(connection => ({
      sessionId: 'session-minus-1',
      timestamp: '2025-04-02',
      type: 'connect',
      entityType: 'character',
      entityId: character.id,
      targetEntityType: connection.type,
      targetEntityId: connection.id,
      data: { reason: connection.reason },
      description: `Connected character "${character.name}" to ${connection.type} with reason: ${connection.reason}`
    }))
  ),

  // NPCs connections
  ...initialNpcs.flatMap(npc =>
    (npc.connections || []).map(connection => ({
      sessionId: 'session-minus-1',
      timestamp: '2025-04-02',
      type: 'connect',
      entityType: 'npc',
      entityId: npc.id,
      targetEntityType: connection.type,
      targetEntityId: connection.id,
      data: { reason: connection.reason },
      description: `Connected NPC "${npc.name}" to ${connection.type} with reason: ${connection.reason}`
    }))
  ),

  // Locations connections
  ...initialLocations.flatMap(location =>
    (location.connections || []).map(connection => ({
      sessionId: 'session-minus-1',
      timestamp: '2025-04-02',
      type: 'connect',
      entityType: 'location',
      entityId: location.id,
      targetEntityType: connection.type,
      targetEntityId: connection.id,
      data: { reason: connection.reason },
      description: `Connected location "${location.name}" to ${connection.type} with reason: ${connection.reason}`
    }))
  ),

  // Items connections
  ...initialItems.flatMap(item =>
    (item.connections || []).map(connection => ({
      sessionId: 'session-minus-1',
      timestamp: '2025-04-02',
      type: 'connect',
      entityType: 'item',
      entityId: item.id,
      targetEntityType: connection.type,
      targetEntityId: connection.id,
      data: { reason: connection.reason },
      description: `Connected item "${item.name}" to ${connection.type} with reason: ${connection.reason}`
    }))
  ),

  // Session 0 (character creation) - future setup

  // Session 1 events - The Adventure Begins
  {
    sessionId: 'session-1',
    timestamp: '2025-04-14',
    type: 'create',
    entityType: 'session',
    entityId: 'session-1',
    data: {
      id: 'session-1',
      title: 'Session 1',
      subtitle: 'The Adventure Begins',
      date: 'April 14, 2025',
      description: 'The party meets in Thaumanar\'s Whispering Tavern and accepts Lord Silverhand\'s mission to investigate an awakening Active Node in the Whisperwood region.',
      highlights: [
        'Party members introduced themselves and formed a group',
        'Met Lord Silverhand who explained the recent surge in Active Node awakenings',
        'Accepted the quest to investigate strange occurrences in Whisperwood',
        'Purchased supplies from Grimshaw the Merchant',
        'Discovered an ancient map fragment depicting Whisperwood before the Sundering'
      ]
    },
    description: 'Created session: The Adventure Begins'
  },

  // Update to Grimshaw NPC with more details
  {
    sessionId: 'session-1',
    timestamp: '2025-04-14',
    type: 'update',
    entityType: 'npc',
    entityId: 'grimshaw',
    data: {
      inventory: 'Ancient trinkets, map fragments, enchanted baubles, and "perfectly legal" relics',
      quote: '"Everything\'s for sale, friend! Even some things that probably shouldn\'t be."'
    },
    description: 'Added detail to Grimshaw after party interacted with him'
  },

  // Add new NPC discovered in session 1
  {
    sessionId: 'session-1',
    timestamp: '2025-04-14',
    type: 'create',
    entityType: 'npc',
    entityId: 'vex',
    data: {
      id: 'vex',
      name: 'Vex the Barkeeper',
      location: 'Thaumanar',
      role: 'Tavern Owner & Information Broker',
      description: 'A burly dwarf with a magnificent beard adorned with tiny metal trinkets that softly chime when he moves. Vex hears all the rumors in Thaumanar and sells information almost as readily as he does ale.',
      status: 'Neutral',
      quote: '"First round\'s on the house. Information costs extra."'
    },
    description: 'Added NPC: Vex the Barkeeper'
  },

  // Connect Vex to other entities
  {
    sessionId: 'session-1',
    timestamp: '2025-04-14',
    type: 'connect',
    entityType: 'npc',
    entityId: 'vex',
    targetEntityType: 'location',
    targetEntityId: 'thaumanar',
    data: { reason: 'Owns the Whispering Tavern in the lower district of Thaumanar' },
    description: 'Connected Vex to Thaumanar'
  },
  {
    sessionId: 'session-1',
    timestamp: '2025-04-14',
    type: 'connect',
    entityType: 'npc',
    entityId: 'vex',
    targetEntityType: 'npc',
    targetEntityId: 'grimshaw',
    data: { reason: 'Provides a safe meeting place for Grimshaw\'s "less legal" transactions' },
    description: 'Connected Vex to Grimshaw'
  },

  // New location discovered during session 1
  {
    sessionId: 'session-1',
    timestamp: '2025-04-14',
    type: 'create',
    entityType: 'location',
    entityId: 'whispering-tavern',
    data: {
      id: 'whispering-tavern',
      name: 'The Whispering Tavern',
      type: 'poi',
      subtype: 'tavern',
      region: 'Thaumanar Lower District',
      description: 'A cozy tavern built into the side of one of Thaumanar\'s ancient spires. The establishment gets its name from the faint whispers that occasionally emanate from the spire walls—echoes of Ancient technology still active within.'
    },
    description: 'Added location: The Whispering Tavern'
  },

  // Connect the tavern to other entities
  {
    sessionId: 'session-1',
    timestamp: '2025-04-14',
    type: 'connect',
    entityType: 'location',
    entityId: 'whispering-tavern',
    targetEntityType: 'location',
    targetEntityId: 'thaumanar',
    data: { reason: 'Located in the lower district of Thaumanar' },
    description: 'Connected Whispering Tavern to Thaumanar'
  },
  {
    sessionId: 'session-1',
    timestamp: '2025-04-14',
    type: 'connect',
    entityType: 'location',
    entityId: 'whispering-tavern',
    targetEntityType: 'npc',
    targetEntityId: 'vex',
    data: { reason: 'Owned and operated by Vex the Barkeeper' },
    description: 'Connected Whispering Tavern to Vex'
  },

  // Update character information based on session 1
  {
    sessionId: 'session-1',
    timestamp: '2025-04-14',
    type: 'update',
    entityType: 'character',
    entityId: 'thorne',
    data: {
      quote: '"The Ancients left their mark on this world. We\'d be fools to ignore their warnings."',
      inventory: 'Frostbite Blade, Ancient armor fragments, 25 gold pieces, Thaumanar map'
    },
    description: 'Updated Thorne with session details'
  },

  // New connection made during session
  {
    sessionId: 'session-1',
    timestamp: '2025-04-14',
    type: 'connect',
    entityType: 'character',
    entityId: 'lyra',
    targetEntityType: 'character',
    targetEntityId: 'thorne',
    data: { reason: 'Lyra recognized that Thorne\'s armor has symbols matching those around her transformed village' },
    description: 'Connected Lyra to Thorne'
  },

  // Session 2 events - Into the Whisperwood
  {
    sessionId: 'session-2',
    timestamp: '2025-04-21',
    type: 'create',
    entityType: 'session',
    entityId: 'session-2',
    data: {
      id: 'session-2',
      title: 'Session 2',
      subtitle: 'Into the Whisperwood',
      date: 'April 21, 2025',
      description: 'The party journeys to Whisperwood Village to investigate the Active Node. They encounter transformed wildlife and discover the village has been altered in strange and beautiful ways by the Node\'s energy.',
      highlights: [
        'Traveled through increasingly unusual terrain as the party approached Whisperwood',
        'Encountered intelligent forest creatures who recognized Lyra',
        'Discovered the village transformed - buildings partly merged with living trees and plants',
        'Met with the village elder who explained the changes began three months ago',
        'Found a hidden entrance to an Ancient facility beneath the village center'
      ]
    },
    description: 'Created session: Into the Whisperwood'
  },

  // Update to Lyra's character
  {
    sessionId: 'session-2',
    timestamp: '2025-04-21',
    type: 'update',
    entityType: 'character',
    entityId: 'lyra',
    data: {
      quote: '"The forest speaks differently now, but it still remembers those who care for it."',
      specialAbility: 'Nature Communion - Can communicate with plant life and transformed creatures near Active Nodes'
    },
    description: 'Updated Lyra with new ability discovered during session'
  },

  // New NPC discovered in session 2
  {
    sessionId: 'session-2',
    timestamp: '2025-04-21',
    type: 'create',
    entityType: 'npc',
    entityId: 'elder-wenna',
    data: {
      id: 'elder-wenna',
      name: 'Elder Wenna',
      location: 'Whisperwood Village',
      role: 'Village Elder & Keeper of Balance',
      description: 'An elderly human woman with bark-like patches on her skin and small leaves growing in her silver hair. Wenna has embraced the changes from the Active Node, developing a symbiotic relationship with the transformed forest.',
      status: 'Ally',
      quote: '"The Ancients didn\'t fall; they transformed. Now we follow their path."'
    },
    description: 'Added NPC: Elder Wenna'
  },

  // Connect Elder Wenna to other entities
  {
    sessionId: 'session-2',
    timestamp: '2025-04-21',
    type: 'connect',
    entityType: 'npc',
    entityId: 'elder-wenna',
    targetEntityType: 'location',
    targetEntityId: 'whisperwood',
    data: { reason: 'Leads Whisperwood Village since the transformation' },
    description: 'Connected Elder Wenna to Whisperwood'
  },
  {
    sessionId: 'session-2',
    timestamp: '2025-04-21',
    type: 'connect',
    entityType: 'npc',
    entityId: 'elder-wenna',
    targetEntityType: 'character',
    targetEntityId: 'lyra',
    data: { reason: 'Taught Lyra to communicate with transformed plant life' },
    description: 'Connected Elder Wenna to Lyra'
  },

  // New location discovered during session 2
  {
    sessionId: 'session-2',
    timestamp: '2025-04-21',
    type: 'create',
    entityType: 'location',
    entityId: 'whisperwood-node',
    data: {
      id: 'whisperwood-node',
      name: 'Whisperwood Active Node',
      type: 'dungeon',
      subtype: 'ruin',
      region: 'Whisperwood',
      description: 'A partially exposed Ancient facility beneath Whisperwood Village. Crystal structures pulse with gentle light, and the walls are covered in intricate patterns that react to touch. Plant life has grown throughout the facility, merging with the technology in harmonious ways.',
      status: 'Active'
    },
    description: 'Added location: Whisperwood Active Node'
  },

  // Connect the node to other entities
  {
    sessionId: 'session-2',
    timestamp: '2025-04-21',
    type: 'connect',
    entityType: 'location',
    entityId: 'whisperwood-node',
    targetEntityType: 'location',
    targetEntityId: 'whisperwood',
    data: { reason: 'Located directly beneath the village center' },
    description: 'Connected Whisperwood Node to Whisperwood Village'
  },

  // Update history with new finding
  {
    sessionId: 'session-2',
    timestamp: '2025-04-21',
    type: 'update',
    entityType: 'history',
    entityId: 'the-modern-age',
    data: {
      newEvent: {
        year: '2100 AR',
        description: 'First documented case of human-plant symbiosis at Whisperwood Village Active Node.'
      }
    },
    description: 'Added historical event about Whisperwood symbiosis'
  },

  // Session 3 events - Secrets of the Node
  {
    sessionId: 'session-3',
    timestamp: '2025-04-28',
    type: 'create',
    entityType: 'session',
    entityId: 'session-3',
    data: {
      id: 'session-3',
      title: 'Session 3',
      subtitle: 'Secrets of the Node',
      date: 'April 28, 2025',
      description: 'The party explores the Whisperwood Active Node and discovers it is designed to restore and balance ecosystems. However, they also find evidence that someone has been attempting to alter its programming for unknown purposes.',
      highlights: [
        'Navigated through the living Ancient facility with guidance from transformed plant entities',
        'Discovered a central chamber with a damaged control interface',
        'Zephyr used his Bloodline Channeler abilities to access partial Node records',
        'Found evidence that someone has been tampering with the Node\'s restoration protocols',
        'Detected unusual energy signatures leading east toward the Dark Spire',
        'Recovered the Amulet of Ecological Balance from the Node\'s core'
      ]
    },
    description: 'Created session: Secrets of the Node'
  },

  // New item discovered in session 3
  {
    sessionId: 'session-3',
    timestamp: '2025-04-28',
    type: 'create',
    entityType: 'item',
    entityId: 'amulet-of-ecological-balance',
    data: {
      id: 'amulet-of-ecological-balance',
      name: 'Amulet of Ecological Balance',
      type: 'Ancient Control Device',
      rarity: 'Very Rare',
      attunement: 'Required (Nature Affinity)',
      description: 'A circular pendant made of a silvery-green metal with a crystal core containing swirling energy patterns resembling a forest ecosystem. It allows the wearer to accelerate plant growth, purify water and soil, and communicate with plant life even outside Active Node influence.',
      found: 'Core chamber of the Whisperwood Active Node',
      owner: 'Lyra Moonshadow'
    },
    description: 'Added item: Amulet of Ecological Balance'
  },

  // Connect the amulet to other entities
  {
    sessionId: 'session-3',
    timestamp: '2025-04-28',
    type: 'connect',
    entityType: 'item',
    entityId: 'amulet-of-ecological-balance',
    targetEntityType: 'location',
    targetEntityId: 'whisperwood-node',
    data: { reason: 'Retrieved from the core chamber of the Node' },
    description: 'Connected Amulet to Whisperwood Node'
  },
  {
    sessionId: 'session-3',
    timestamp: '2025-04-28',
    type: 'connect',
    entityType: 'item',
    entityId: 'amulet-of-ecological-balance',
    targetEntityType: 'character',
    targetEntityId: 'lyra',
    data: { reason: 'Bonded with Lyra due to her connection with the transformed forest' },
    description: 'Connected Amulet to Lyra'
  },

  // New connection discovered during session
  {
    sessionId: 'session-3',
    timestamp: '2025-04-28',
    type: 'connect',
    entityType: 'location',
    entityId: 'whisperwood-node',
    targetEntityType: 'location',
    targetEntityId: 'dark-spire',
    data: { reason: 'Unusual energy signatures detected leading from Whisperwood toward Dark Spire' },
    description: 'Connected Whisperwood Node to Dark Spire'
  },

  // Update to Zephyr's character
  {
    sessionId: 'session-3',
    timestamp: '2025-04-28',
    type: 'update',
    entityType: 'character',
    entityId: 'zephyr',
    data: {
      quote: '"The Nodes aren\'t just waking up—they\'re talking to each other. And I don\'t think they all agree."',
      knowledge: 'Partial understanding of Ecological Node protocols and communication networks'
    },
    description: 'Updated Zephyr with knowledge gained from Node interaction'
  },

  // Update to Kragnor NPC with new information
  {
    sessionId: 'session-3',
    timestamp: '2025-04-28',
    type: 'update',
    entityType: 'npc',
    entityId: 'kragnor',
    data: {
      plans: 'Evidence suggests Kragnor is attempting to override ecological restoration protocols in Active Nodes to increase weapon production capabilities'
    },
    description: 'Updated Kragnor with plans discovered at the Node'
  },

  // Connect Kragnor to Whisperwood Node
  {
    sessionId: 'session-3',
    timestamp: '2025-04-28',
    type: 'connect',
    entityType: 'npc',
    entityId: 'kragnor',
    targetEntityType: 'location',
    targetEntityId: 'whisperwood-node',
    data: { reason: 'Has been remotely tampering with Node protocols, leaving behind evidence of intrusion' },
    description: 'Connected Kragnor to Whisperwood Node'
  }
];

// Helper functions to process the history

// Get all events for a specific session
export function getSessionEvents(sessionId) {
  return historyEntries.filter(entry => entry.sessionId === sessionId);
}

// Get all events for a specific entity
export function getEntityEvents(entityType, entityId) {
  return historyEntries.filter(
    entry => (entry.entityType === entityType && entry.entityId === entityId) ||
      (entry.targetEntityType === entityType && entry.targetEntityId === entityId)
  );
}

// Get all session-related events (creation and entities affected in that session)
export function getAllSessionRelatedEvents(sessionId) {
  return historyEntries.filter(entry => entry.sessionId === sessionId);
}

// Build an entity from history
export function buildEntityFromHistory(entityType, entityId) {
  // Get creation event
  const createEvent = historyEntries.find(
    entry => entry.type === 'create' && entry.entityType === entityType && entry.entityId === entityId
  );

  if (!createEvent) return null;

  // Start with creation data
  let entity = { ...createEvent.data };

  // Apply all updates
  const updateEvents = historyEntries.filter(
    entry => entry.type === 'update' && entry.entityType === entityType && entry.entityId === entityId
  );

  updateEvents.forEach(event => {
    entity = { ...entity, ...event.data };
  });

  // Get all connection events where this entity is the source
  const connectionEvents = historyEntries.filter(
    entry => entry.type === 'connect' && entry.entityType === entityType && entry.entityId === entityId
  );

  // Build connections array
  entity.connections = connectionEvents.map(event => ({
    type: event.targetEntityType,
    id: event.targetEntityId,
    reason: event.data.reason,
    sessionId: event.sessionId // Add which session this connection was made
  }));

  // Add history array to track changes by session
  entity.history = getEntityEventsBySession(entityType, entityId);

  return entity;
}

// Group entity events by session
export function getEntityEventsBySession(entityType, entityId) {
  const events = getEntityEvents(entityType, entityId);

  // Group by sessionId
  const sessionGroups = {};
  events.forEach(event => {
    if (!sessionGroups[event.sessionId]) {
      sessionGroups[event.sessionId] = [];
    }
    sessionGroups[event.sessionId].push(event);
  });

  // Convert to array format
  return Object.entries(sessionGroups).map(([sessionId, events]) => ({
    sessionId,
    events
  }));
}

// Get all entities of a specific type
export function getAllEntities(entityType) {
  // Find all unique entityIds for the given type that have a 'create' event
  const entityIds = [...new Set(
    historyEntries
      .filter(entry => entry.type === 'create' && entry.entityType === entityType)
      .map(entry => entry.entityId)
  )];

  // Build each entity from history
  return entityIds.map(id => buildEntityFromHistory(entityType, id));
}

// Export as our main data access model
export default {
  historyEntries,
  getSessionEvents,
  getEntityEvents,
  getAllSessionRelatedEvents,
  buildEntityFromHistory,
  getEntityEventsBySession,
  getAllEntities
};
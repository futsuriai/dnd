// Central data store for world information with bidirectional relationships

// CHARACTERS
export const characters = [
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
      { 
        type: 'location', 
        id: 'thaumanar', 
        reason: 'Discovered ancient armor in the ruins that bonded to him, granting paladin abilities.' 
      },
      {
        type: 'location',
        id: 'oracle-nexus',
        reason: 'Visited the Oracle to learn more about his ancient armor and received a cryptic prophecy.'
      },
      {
        type: 'npc',
        id: 'silverhand',
        reason: 'Silverhand has hired Thorne multiple times for relic hunting expeditions.'
      }
    ]
  },
  {
    id: 'lyra',
    name: 'Lyra Moonshadow',
    player: 'Player Name 2',
    race: 'Elf',
    class: 'Ranger',
    level: 5,
    background: 'Survivor of Node Awakening',
    bio: 'Lyra\'s village was transformed when an Active Node awakened nearby. The sudden surge of magical energy changed the surrounding environment and wildlife, giving her a mystical connection to the altered creatures.',
    dndBeyondLink: 'https://www.dndbeyond.com/characters/789012',
    connections: [
      { 
        type: 'location', 
        id: 'whisperwood', 
        reason: 'Home village was transformed by an Active Node awakening, giving her connection to the altered wildlife.' 
      },
      {
        type: 'npc',
        id: 'morana',
        reason: 'Morana has been teaching Lyra to understand the entities that now inhabit Whisperwood.'
      }
    ]
  },
  {
    id: 'zephyr',
    name: 'Zephyr Stormwind',
    player: 'Player Name 3',
    race: 'Tiefling',
    class: 'Sorcerer',
    level: 5,
    background: 'Bloodline Channeler',
    bio: 'Descendant of the Ancients, Zephyr\'s blood resonates with the remnants of the Ethereal Lattice. He possesses one of the rare Crystal Minds and can access fragments of Ancient knowledge through it.',
    dndBeyondLink: 'https://www.dndbeyond.com/characters/345678',
    connections: [
      {
        type: 'location',
        id: 'dark-spire',
        reason: 'Seeks to recover the Orb of Dragonkind from Kragnor\'s vault.'
      },
      {
        type: 'npc',
        id: 'kragnor',
        reason: 'Bitter rival who also seeks to control Ancient technology through blood connection.'
      },
      {
        type: 'location',
        id: 'crystal-gardens',
        reason: 'Discovered his Bloodline Channeler abilities while meditating in the gardens.'
      },
      {
        type: 'location',
        id: 'spire-central',
        reason: 'Studied at the Academy of Channelers located near the central spire.'
      },
      {
        type: 'npc',
        id: 'grimshaw',
        reason: 'Regular customer who purchases Crystal Mind fragments to expand his knowledge.'
      }
    ]
  },
  {
    id: 'brom',
    name: 'Brom Oakenshield',
    player: 'Player Name 4',
    race: 'Human',
    class: 'Fighter',
    level: 5,
    background: 'Former Oracle Guard',
    bio: 'Once a dedicated protector of the Oracle of Nexus, Brom left his post after hearing a disturbing prophecy. He now seeks to prevent another Sundering by monitoring the increasing Ancient activity.',
    dndBeyondLink: 'https://www.dndbeyond.com/characters/901234',
    connections: [
      { 
        type: 'location', 
        id: 'nexus', 
        reason: 'Served as a guard at the Oracle temple before leaving after hearing a disturbing prophecy.' 
      },
      { 
        type: 'location', 
        id: 'oracle-nexus', 
        reason: 'Former guardian of the Oracle before abandoning his post.' 
      },
      {
        type: 'npc',
        id: 'silverhand',
        reason: 'Distrusts Silverhand\'s interpretations of the Oracle\'s messages.'
      }
    ]
  }
];

// NPCS
export const npcs = [
  {
    id: 'silverhand',
    name: 'Lord Bartholomew Silverhand',
    location: 'Spire Central',
    role: 'High Councilor & Oracle Interpreter',
    description: 'A distinguished noble descended from the Luminar Dynasty, Silverhand claims partial Ancient bloodline. He leads excavation efforts at Active Nodes and consults regularly with the Oracle of Nexus.',
    status: 'Ally',
    connections: [
      { 
        type: 'location', 
        id: 'spire-central', 
        reason: 'Leads the High Council that governs from Spire Central.' 
      },
      {
        type: 'character',
        id: 'thorne',
        reason: 'Has hired Thorne multiple times for relic hunting expeditions.'
      },
      {
        type: 'character',
        id: 'brom',
        reason: 'Sees Brom as potentially dangerous due to his knowledge of a disturbing Oracle prophecy.'
      },
      {
        type: 'location',
        id: 'oracle-nexus',
        reason: 'Official interpreter of the Oracle\'s messages for the Seven Spires Confederation.'
      },
      {
        type: 'location',
        id: 'nexus',
        reason: 'Maintains a residence in the city to stay close to the Oracle.'
      }
    ]
  },
  {
    id: 'grimshaw',
    name: 'Grimshaw the Merchant',
    location: 'Traveling between Ancient Sites',
    role: 'Relic Trader & Member of Blazing Sigil',
    description: 'A rotund, jovial halfling bearing a faint luminous mark on his palm. Specializes in Ancient relics and Crystal Mind fragments. Rumored to have a collection of working Ethereal Lattice shards.',
    status: 'Neutral',
    connections: [
      {
        type: 'character',
        id: 'zephyr',
        reason: 'Regular supplier of Crystal Mind fragments to Zephyr.'
      },
      {
        type: 'location',
        id: 'thaumanar',
        reason: 'Operates a secret shop in the lower districts selling rare relics.'
      },
      {
        type: 'location',
        id: 'eternal-flame',
        reason: 'Uses the Eternal Flame to power and recharge certain Ancient devices.'
      }
    ]
  },
  {
    id: 'morana',
    name: 'Morana Shadowweaver',
    location: 'Regions near Active Nodes',
    role: 'Voidspeaker Mystic',
    description: 'A mysterious woman who communes with entities from beyond the Sundering. She claims to hear whispers from the Luminous Concord and warns of the dangers in reactivating Ancient technology.',
    status: 'Unknown',
    connections: [
      { 
        type: 'location', 
        id: 'crimson-desert', 
        reason: 'Studies the effects of the first documented Active Node awakening and communes with entities near it.' 
      },
      {
        type: 'character',
        id: 'lyra',
        reason: 'Has been teaching Lyra to understand the entities that now inhabit Whisperwood.'
      }
    ]
  },
  {
    id: 'kragnor',
    name: 'Kragnor the Merciless',
    location: 'The Dark Spire',
    role: 'Warlord & Guardian Subjugator',
    description: 'A massive orc chieftain who has managed to control Ancient guardians using a modified Crystal Mind. Commands an army enhanced with repurposed Ancient technology from his fortress built around an Active Node.',
    status: 'Enemy',
    connections: [
      { 
        type: 'location', 
        id: 'dark-spire', 
        reason: 'Built a fortress around this Active Node and controls Ancient guardians from it.' 
      },
      {
        type: 'character',
        id: 'zephyr',
        reason: 'Bitter rival to Zephyr, competing for control of Ancient technology through blood connection.'
      }
    ]
  }
];

// LOCATIONS
export const locations = [
  {
    id: 'thaumanar',
    name: 'Thaumanar',
    type: 'city',
    subtype: 'magic',
    region: 'Eastern Spire Territory',
    description: 'The first major settlement established after the Restoration, built around the Whispering Spires. Known for its ancient architecture and the Wielders Guild headquarters. The city\'s foundations incorporate Ancient technology that still hums with power.',
    connections: [
      { 
        type: 'character', 
        id: 'thorne', 
        reason: 'Where Thorne discovered ancient armor that bonded to him, granting paladin abilities.' 
      },
      {
        type: 'npc',
        id: 'grimshaw',
        reason: 'Grimshaw operates a secret shop in the lower districts selling rare relics.'
      }
    ]
  },
  {
    id: 'nexus',
    name: 'Nexus',
    type: 'city',
    subtype: 'capital',
    region: 'Central Confederation',
    description: 'Built around the Oracle temple, Nexus is a city of scholars, priests, and pilgrims. The Nexus Priesthood interprets the Oracle\'s cryptic wisdom, making the city a political and spiritual center of the known world.',
    connections: [
      { 
        type: 'character', 
        id: 'brom', 
        reason: 'Where Brom served as a guard at the Oracle temple before hearing a disturbing prophecy.' 
      },
      {
        type: 'npc',
        id: 'silverhand',
        reason: 'Silverhand maintains a residence in the city to stay close to the Oracle.'
      }
    ]
  },
  {
    id: 'spire-central',
    name: 'Spire Central',
    type: 'city',
    subtype: 'capital',
    region: 'Heart of the Confederation',
    description: 'The capital of the Seven Spires Confederation, defined by seven towering Ancient structures that emit protective fields. The High Council chambers sit at the base of the tallest spire, where representatives gather to govern the confederation.',
    connections: [
      { 
        type: 'npc', 
        id: 'silverhand', 
        reason: 'Base of operations for Lord Silverhand as High Councilor.' 
      },
      {
        type: 'character',
        id: 'zephyr',
        reason: 'Location of the Academy of Channelers where Zephyr studied.'
      }
    ]
  },
  {
    id: 'dark-spire',
    name: 'Dark Spire Fortress',
    type: 'dungeon',
    subtype: 'fortress',
    region: 'Northern Wastes',
    description: 'A fortress built around an Active Node, where Ancient guardians patrol under the control of a modified Crystal Mind. The surrounding area has been twisted by wild energies, creating dangerous and surreal landscapes.',
    connections: [
      { 
        type: 'npc', 
        id: 'kragnor', 
        reason: 'Headquarters of Kragnor\'s army, where he controls Ancient guardians using a modified Crystal Mind.' 
      },
      {
        type: 'character',
        id: 'zephyr',
        reason: 'Target of Zephyr\'s quest to recover the Orb of Dragonkind.'
      }
    ]
  },
  {
    id: 'crystal-gardens',
    name: 'Crystal Gardens of Luminar',
    type: 'poi',
    subtype: 'natural',
    region: 'Southern Territories',
    description: 'Vast gardens where crystalline plants grow, emitting gentle light that keeps darkness at bay. Many believe the gardens were once a recreational area for the Ancients, now overgrown and wild after millennia of neglect.',
    connections: [
      {
        type: 'character',
        id: 'zephyr',
        reason: 'Where Zephyr discovered his Bloodline Channeler abilities while meditating.'
      }
    ]
  },
  {
    id: 'eternal-flame',
    name: 'Eternal Flame of Pyrothar',
    type: 'poi',
    subtype: 'magic',
    region: 'Western Confederation',
    description: 'A massive flame that has burned without fuel since before recorded history. The surrounding city harnesses its heat for industry and comfort. Scholars theorize it may be a controlled breach in the Ethereal Lattice.',
    connections: [
      {
        type: 'npc',
        id: 'grimshaw',
        reason: 'Grimshaw uses the Eternal Flame to power and recharge certain Ancient devices.'
      }
    ]
  },
  {
    id: 'oracle-nexus',
    name: 'Oracle of Nexus',
    type: 'poi',
    subtype: 'monument',
    region: 'Central Confederation',
    description: 'A vast thinking engine of Ancient design that awakens periodically to offer cryptic wisdom. The Great Temple built around it is the center of the Nexus Priesthood\'s power and influence.',
    connections: [
      { 
        type: 'character', 
        id: 'brom', 
        reason: 'Where Brom served as a guard before leaving his post after receiving a disturbing prophecy.' 
      },
      {
        type: 'character',
        id: 'thorne',
        reason: 'Thorne visited to learn more about his ancient armor and received a cryptic prophecy.'
      },
      {
        type: 'npc',
        id: 'silverhand',
        reason: 'Silverhand is the official interpreter of the Oracle\'s messages for the Seven Spires Confederation.'
      }
    ]
  },
  {
    id: 'whisperwood',
    name: 'Whisperwood Village',
    type: 'poi',
    subtype: 'natural',
    region: 'Far Eastern Frontier',
    description: 'Once an ordinary settlement, this village was transformed when an Active Node awakened nearby. The forest surrounding it has evolved rapidly, with plants and animals exhibiting unusual properties and intelligence.',
    connections: [
      { 
        type: 'character', 
        id: 'lyra', 
        reason: 'Lyra\'s home village, transformed by an Active Node awakening.' 
      }
    ]
  },
  {
    id: 'crimson-desert',
    name: 'Crimson Desert Active Node',
    type: 'poi',
    subtype: 'magic',
    region: 'Far Southern Reaches',
    description: 'The first documented Active Node to awaken in the modern era, transforming the surrounding wasteland into a lush landscape. Ancient mechanisms hum beneath the sands, and strange creatures adapted to the new environment roam the periphery.',
    connections: [
      { 
        type: 'npc', 
        id: 'morana', 
        reason: 'Site where Morana communes with entities from beyond the Sundering and studies the effects of Node awakening.' 
      }
    ]
  },
];

// Helper functions to get data and connections
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

export function getEntityConnections(type, id) {
  let entity;
  if (type === 'location') {
    entity = getLocation(id);
  } else if (type === 'character') {
    entity = getCharacter(id);
  } else if (type === 'npc') {
    entity = getNpc(id);
  } else if (type === 'item') {
    // Placeholder for future item connections
    entity = null;
  }

  if (!entity || !entity.connections) return [];
  
  return entity.connections.map(conn => {
    let connectedEntity;
    if (conn.type === 'location') {
      connectedEntity = getLocation(conn.id);
    } else if (conn.type === 'character') {
      connectedEntity = getCharacter(conn.id);
    } else if (conn.type === 'npc') {
      connectedEntity = getNpc(conn.id);
    } else if (conn.type === 'item') {
      // Placeholder for future item connections
      connectedEntity = null;
    }
    
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

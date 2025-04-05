// NPC data for the world

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

export default npcs;
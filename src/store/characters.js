// Character data for the world

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

export default characters;
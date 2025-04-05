// Item data for the world

export const items = [
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
      {
        type: 'character',
        id: 'thorne',
        reason: 'Currently wielded by Thorne after it bonded with his paladin abilities.'
      },
      {
        type: 'location',
        id: 'crimson-desert',
        reason: 'Found in the depths of this Active Node, suggesting a link to the original Frozen Wastes.'
      }
    ]
  },
  {
    id: 'amulet-of-true-sight',
    name: 'Amulet of True Sight',
    type: 'Luminous Concord Relic',
    rarity: 'Very Rare',
    attunement: 'Required (Any Wielder)',
    description: 'This silver amulet contains a fragment of a Celestial Lens from the Age of Wonders. The purple gemstone is actually a compressed data storage unit that interfaces with the wearer\'s visual cortex, allowing perception of invisible entities and the Ethereal Plane remnants.',
    found: 'Gift from Lord Silverhand after helping secure an Ancient archive',
    owner: 'Party Treasure',
    connections: [
      {
        type: 'npc',
        id: 'silverhand',
        reason: 'Silverhand gifted this item to the party as payment for securing an Ancient archive.'
      }
    ]
  },
  {
    id: 'cloak-of-elvenkind',
    name: 'Cloak of Elvenkind',
    type: 'Adapted Ancient Technology',
    rarity: 'Uncommon',
    attunement: 'Not Required',
    description: 'This cloak incorporates threads from materials created by the Ancients. It contains microscopic adaptive camouflage nodes that respond to surroundings, granting advantage on Stealth checks and disadvantage to those perceiving the wearer.',
    found: 'Hidden cache in the Whispering Spires of Thaumanar',
    owner: 'Lyra Moonshadow',
    connections: [
      {
        type: 'character',
        id: 'lyra',
        reason: 'Used by Lyra to enhance her ranger abilities when tracking transformed creatures.'
      },
      {
        type: 'location',
        id: 'thaumanar',
        reason: 'Discovered in a hidden cache within the Whispering Spires.'
      }
    ]
  },
  {
    id: 'orb-of-dragonkind',
    name: 'Orb of Dragonkind',
    type: 'Crystal Mind (Specialized)',
    rarity: 'Legendary',
    attunement: 'Required (Bloodline Channeler only)',
    description: 'One of the legendary Crystal Minds containing Ancient knowledge specific to draconic entities. The Ancients studied and possibly created dragons as guardians. This orb can access those control protocols, but only for red dragons. Contains partial instructions from the Eternity Working that caused the Sundering.',
    found: 'Kragnor\'s vault in the Dark Spire Active Node',
    owner: 'Zephyr Stormwind',
    connections: [
      {
        type: 'character',
        id: 'zephyr',
        reason: 'Target of Zephyr\'s quest and now in his possession, enhancing his connection to Ancient knowledge.'
      },
      {
        type: 'npc',
        id: 'kragnor',
        reason: 'Previously owned by Kragnor who used it to control Ancient guardians in his fortress.'
      },
      {
        type: 'location',
        id: 'dark-spire',
        reason: 'Recovered from Kragnor\'s vault deep within the Dark Spire.'
      }
    ]
  }
];

export default items;
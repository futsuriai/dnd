// Location data for the world

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

export default locations;
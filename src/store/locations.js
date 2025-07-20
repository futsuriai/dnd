// Location data for the world

export const locations = [
  {
    id: 'hieroterra',
    name: 'Hieroterra',
    type: 'province', // Added type
    description: 'An imperial province of The Hariolar Empire and the campaign’s setting, said to be the birthplace of Nites. The province is divided by a canal around which the capital, Bastion City, arose.',
    connections: [
      { type: 'lore', id: 'nites', reason: 'Birthplace of Nites' },
      { type: 'lore', id: 'pilgrimage-enlightened', reason: 'Starting point of the Pilgrimage' }
    ]
  },
  {
    id: 'bastion-city',
    name: 'Bastion City',
    type: 'capital',
    description: 'The capital of Hieroterra, where the campaign begins.',
    tags: ['major city', 'hieroterra'],
    connections: [
      { type: 'location', id: 'hieroterra', relationship: 'Located In' }
    ]
  },
  {
    id: 'pharus',
    name: 'Pharus',
    type: 'capital',
    tags: ['major city', 'ordonne'],
    description: 'The imperial throne’s seat and the heart of the Eulogia of the Eternal Light. Said to be where Nites sacrificed herself to defeat the Shadowed Monarch, the city was founded by The First Emperor.',
    connections: [
      { type: 'location', id: 'ordonne', reason: 'Located within Ordonne' },
      { type: 'lore', id: 'nites', reason: 'Site of Nites\'s sacrifice' }, // Escaped apostrophe
      { type: 'lore', id: 'first-emperor', reason: 'Founded by the First Emperor' }
    ]
  },
  {
    id: 'ordonne',
    name: 'Ordonne',
    type: 'province', // Added type
    description: 'A western imperial province and the heart of The Hariolar Empire. It houses the imperial capital of Pharus.',
    connections: [
      { type: 'location', id: 'pharus', reason: 'Contains Pharus (Capital)' },
      { type: 'lore', id: 'pilgrimage-enlightened', reason: 'Ending point of the Pilgrimage' }
    ]
  },
  {
    id: 'duskbreaker-lighthouse',
    name: 'Duskbreaker Lighthouse',
    type: 'landmark', // Or 'poi' if you prefer
    description: 'A tall lighthouse on the coast of Bastion City, known for its magical beacon.',
    fullText: 'The locus of [[Light Crystal]] research in the empire. Composed of various magic users, artificers, and artisans, they all work together to develop the latest technology.\n\nDespite being headquartered in a tall tower in the east side of [[Bastion City]], most of its finding are exported to [[Pharus]]. The first use case of light crystals were replacing the candlelit streetlamps in Bastion City.',
    tags: ['landmark', 'bastion city'],
    connections: [
      { type: 'location', id: 'bastion-city', relationship: 'Located In' }
    ]
  },
  {
    id: 'eulogian-seminary',
    name: 'Eulogian Seminary',
    type: 'poi',
    description: 'A religious school and center of the Eulogia of the Eternal Light located in West Bastion, where acolytes like Ellara train in theology and ritual.',
    tags: ['seminary', 'west bastion'],
    connections: [
      { type: 'location', id: 'bastion-city', relationship: 'Located In' }
    ]
  },
  {
    id: 'drunken-goose',
    name: 'The Drunken Goose Tavern',
    type: 'tavern',
    description: 'A favorite tavern of artisans, soldiers, and working-class folk in West Bastion. The party often meets here to gather information and unwind.',
    tags: ['tavern', 'west bastion'],
    connections: [
      { type: 'location', id: 'bastion-city', relationship: 'Located In' }
    ]
  }
];

export default locations;
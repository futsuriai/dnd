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
  }
];

export default locations;
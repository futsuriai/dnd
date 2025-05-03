// Lore data for the world

export const lore = [
  {
    id: 'nites', // Added ID
    term: 'Nites',
    description: 'The title for The Eternal Light when she walked this land. From Latin *nitēs*, present 2nd person singular, meaning "to shine, sparkle, radiant."\n\nPronounced knee-tehz.',
    connections: [ // Added connection
      { type: 'location', id: 'hieroterra', reason: 'Birthplace' },
      { type: 'location', id: 'pharus', reason: 'Sacrificed herself here' }
    ]
  },
  {
    id: 'eternal-light', // Added ID
    term: 'The Eternal Light',
    description: 'The ascended form of Nites after her sacrifice. While mortal, Nites was a woman; as a divine she has ascended beyond physical mortal limitations and is depicted genderless.'
  },
  {
    id: 'eulogia-eternal-light', // Added ID
    term: 'Eulogia of the Eternal Light',
    description: 'The religion of The Hariolar Empire.'
  },
  {
    id: 'first-emperor', // Added ID
    term: 'The First Emperor',
    description: 'One of the original followers of Nites and witness to her sacrifice. Little is known about this figure.',
    connections: [ // Added connection
      { type: 'location', id: 'pharus', reason: 'Founded the city' }
    ]
  },
  {
    id: 'curse-shadowed', // Added ID
    term: 'The Curse of the Shadowed',
    description: '> May your hearth bear not warmth, your labour no fruits. In history’s Light, may your names be ever Shadowed.\n\nThese were Nites’s dying words before her ascension. The Eulogia of the Eternal Light records that she cursed all who did not join her against the Shadowed Monarch; from then on, they were known as the Shadowed.'
  },
  {
    id: 'pilgrimage-enlightened', // Added ID
    term: 'The Pilgrimage of the Enlightened',
    description: 'The three‑year trek of Nites from her homeland of Hieroterra to Ordonne; those who followed her became known as the Enlightened Peoples.',
    connections: [ // Added connection
      { type: 'location', id: 'hieroterra', reason: 'Starting point' },
      { type: 'location', id: 'ordonne', reason: 'Ending point' }
    ]
  }
];

export default lore;

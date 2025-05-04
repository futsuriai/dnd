// Lore data for the world

export const lore = [
  {
    id: 'light-crystals',
    term: 'Light Crystals',
    description: 'A recently discovered technology revolutionizing The Hariolar Empire, involving magically rechargeable crystals found in ancient ruins.',
    fullText: `A recently discovered technology that is causing a technological revolution in [[The Hariolar Empire/The Hariolar Empire|The Hariolar Empire]]. The study and development of light crystal technology is headquartered by the [[Duskbreaker Lighthouse]] in [[Bastion City]].

Their first public use were replacing the candle-powered streetlamps of Bastion City.

## Discovery

Light crystals were first found by researchers who were exploring old [[Shadowed]] ruins from the [[Timeline of the World#The Age of Shadow]]. Further study was needed and researchers from across the empire came to Bastion City to study the crystals. Eventually, it was discovered that these crystals have an innate magical energy that can be used to power various things. Moreover, with little effort magic users can recharge these crystals.

This innovation led to more research around Shadowed ruins where upon further digging in various ruins through the [[Hieroterra]] discovered a bounty of crystals. Since then a strong link between the Shadowed and the light crystals have been established.

8 years ago (643 AE) , it was also discovered that deep within the Sunstone Quarry. Curiously, among them were the "Standing Stones", apparent artifacts from The Age of Shadow. 

This led to further explorations of the quarry and mines within the empire, wherein more light crystals were found among ruins from the Age of Shadow.

## Initial Controversy

At first, the [[Eulogia of the Eternal Light]] opposed the usage of these crystals as they were found among the ruins of the Shadowed. The crystals and their research were deemed blasphemous in the eyes of the Eulogia given their obvious ties to the Shadowed.

It was only after anonymous pamphlets were spread around the empire, arguing that the light crystals were a means of repent for the Shadowed that the Eulogia's stance changed.

Rumours have it that the Imperial Family as well as the aristocracy favoured the technology. In even quieter whispers, it seemed the Eulogia itself was divided on the issue. The pamphlets gave the theological out that the Eulogia needed. Today, the Eulogia fully supports the research and is one of the main sponsors of the [[Duskbreaker Lighthouse]].`,
    connections: [
      { type: 'location', id: 'hariolar-empire', reason: 'Technological revolution centered here' },
      { type: 'location', id: 'duskbreaker-lighthouse', reason: 'Headquarters for research' },
      { type: 'location', id: 'bastion-city', reason: 'First public use (streetlamps), research hub' },
      { type: 'lore', id: 'curse-shadowed', reason: 'Found in Shadowed ruins, initial controversy' },
      { type: 'location', id: 'hieroterra', reason: 'Found in ruins here' },
      // Note: Sunstone Quarry is mentioned but doesn't have a specific ID yet. Add if created.
      { type: 'lore', id: 'eulogia-eternal-light', reason: 'Initial opposition, later support' }
    ]
  },
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

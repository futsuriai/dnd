// Lore data for the world

export const lore = [
  {
    id: 'light-crystals',
    term: 'Light Crystals',
    description: 'A recently discovered technology revolutionizing The Hariolar Empire, involving magically rechargeable crystals found in ancient ruins. Session 6 revealed that the Lighthouse secretly synthesizes enhanced crystals by consuming living Shadowed beings.',
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

Rumours have it that the Imperial Family as well as the aristocracy favoured the technology. In even quieter whispers, it seemed the Eulogia itself was divided on the issue. The pamphlets gave the theological out that the Eulogia needed. Today, the Eulogia fully supports the research and is one of the main sponsors of the [[Duskbreaker Lighthouse]].

## Synthesis Program (Classified)

Session 6 revealed that the Lighthouse conducts a secret basement program to synthesize enhanced light crystals by consuming living Shadowed beings. According to basement technician Dawn, "light crystals are forged from Shadowed ones" with "alive at initiation" producing the best results. The process completely consumes the subject. Synthetic crystals are more powerful and hold more magic than found crystals, which suffer from cross-contamination. Previously, two floral specimens (somewhat humanoid) were processed; Meri was the first fauna test subject. Processed crystals are sent upstairs to current projects. The program appears to be sanctioned by the Lightkeepers and involves Eulogian liaison Donnathan Reeves delivering subjects "per protocol."`,
    connections: [
      { type: 'location', id: 'hariolar-empire', reason: 'Technological revolution centered here' },
      { type: 'location', id: 'duskbreaker-lighthouse', reason: 'Headquarters for research and synthesis' },
      { type: 'location', id: 'bastion-city', reason: 'First public use (streetlamps), research hub' },
      { type: 'lore', id: 'curse-shadowed', reason: 'Found in Shadowed ruins; synthesis source for enhanced crystals' },
      { type: 'location', id: 'hieroterra', reason: 'Found in ruins here' },
      { type: 'location', id: 'basement-lab', reason: 'Secret synthesis facility' },
      { type: 'lore', id: 'eulogia-eternal-light', reason: 'Initial opposition, later support and complicity' },
      { type: 'npc', id: 'donnathan-reeves', reason: 'Oversees subject procurement for synthesis' }
    ],
    history: [
      { session: 1, note: 'Introduced as new technology from the Duskbreaker Lighthouse.' },
      { session: 3, note: 'Discovered powering warforged constructs on the Old Trade Road.' },
      { session: 5, note: 'Research into phosphorus additives to increase capacity tenfold is revealed.' },
      { session: 6, note: 'Secret synthesis program revealed: enhanced crystals are forged from living Shadowed beings.' }
    ]
  },
  {
    id: 'warforged',
    term: 'Warforged Constructs',
    description: 'Magically powered constructs deployed by the Duskbreaker Lighthouse. Early field units were rusted and used light crystals; newer models are cleaner designs with research into continuous operation and autonomous commands.',
    history: [
      { session: 3, note: 'First encountered as a trio of rusted constructs in an ambush on the Old Trade Road.' },
      { session: 5, note: 'Upgraded units and a titan-scale chassis were observed during the Lighthouse infiltration.' },
      { session: 6, note: 'The goal of continuous operation is linked to the synthetic crystal program.' }
    ],
    connections: [
      { type: 'location', id: 'duskbreaker-lighthouse', reason: 'Manufactured and researched here' },
      { type: 'location', id: 'old-trade-road', reason: 'Ambush site for early models' },
      { type: 'lore', id: 'light-crystals', reason: 'Powered by light crystals' }
    ]
  },
  {
    id: 'lightkeepers',
    term: 'The Lightkeepers',
    description: 'The governing council of the Duskbreaker Lighthouse overseeing arcane research, engineering priorities, and political relations.',
    history: [
      { session: 5, note: 'Mentioned as having a keen interest in the results of warforged field tests.' },
      { session: 6, note: 'Implied to have sanctioned the secret synthesis program.' }
    ],
    connections: [
      { type: 'location', id: 'duskbreaker-lighthouse', reason: 'Ruling council' }
    ]
  },
  {
    id: 'nites', // Added ID
    term: 'Nites',
    description: 'The title for The Eternal Light when she walked this land. From Latin *nitēs*, present 2nd person singular, meaning "to shine, sparkle, radiant."\n\nPronounced knee-tehz.',
    history: [
      { session: 3, note: 'Mentioned by Eduard in a discussion about languages.' }
    ],
    connections: [ // Added connection
      { type: 'location', id: 'hieroterra', reason: 'Birthplace' },
      { type: 'location', id: 'pharus', reason: 'Sacrificed herself here' }
    ]
  },
  {
    id: 'hyr',
    term: 'Hyr',
    description: 'A village goddess revered by some goliath communities as the heart of love, kinship, and seasonal rites such as long-grass braiding.',
    history: [
      { session: 1, note: 'Named by Ysidor during introductions and blessings.' },
      { session: 3, note: 'Ysidor explains the goddess and her rituals to Ellara on the road.' },
      { session: 6, note: 'Ysidor performs an atonement rite for Stanley, invoking his values.' }
    ],
    connections: [
      { type: 'character', id: 'ysidor', reason: 'Personal devotion and village traditions' }
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
    description: 'The religion of The Hariolar Empire.',
    history: [
      { session: 1, note: 'Introduced as the dominant faith and the organizer of the Alms Giving event.' },
      { session: 2, note: 'Proctor Eduard\'s involvement in Meri\'s custody transfer is discovered.' },
      { session: 4, note: 'Tensions with the Duskbreaker Lighthouse over ambition and control are discussed by Eduard.' },
      { session: 6, note: 'Implicated in the secret synthesis program through liaison Donnathan Reeves, who delivers subjects.' }
    ],
    connections: [
      { type: 'npc', id: 'proctor-eduard', reason: 'Clergy member (Proctor)' },
      { type: 'npc', id: 'donnathan-reeves', reason: 'Liaison for subject procurement' }
    ]
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
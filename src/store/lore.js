// Lore data for the world

export const lore = [
  {
    id: 'black-swan',
    term: 'The Black Swan',
    description: 'A mysterious patron on bounty-hunter contract boards, known for reliable, high-risk, high-reward work. Posted a 250g bounty to "remove" Meri using ambiguous language. Nyx suspects this may be Grand Duke Valerian Oliander.',
    history: [
      { session: 11, note: 'Black Swan commission first revealed: 250g bounty on Meri' },
      { session: 12, note: 'Party discussed taking the contract to protect Meri; Nyx suspects the Black Swan is the Grand Duke' }
    ],
    connections: [
      { type: 'npc', id: 'meri', reason: 'Target of bounty' },
      { type: 'npc', id: 'duke-valerian-oliander', reason: 'Suspected patron' }
    ]
  },
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
      { session: 6, note: 'Secret synthesis program revealed: enhanced crystals are forged from living Shadowed beings.' },
      { session: 8, note: 'Ellara\'s vision of a screaming lamp highlights the suffering infused into every synthetic crystal.' },
      { session: 14, note: 'Berridin briefed Ardwin that shadowed goliaths were being converted into crystals for newer warforged units.' }
    ]
  },
  {
    id: 'warforged',
    term: 'Warforged Constructs',
    description: 'Magically powered constructs deployed by the Duskbreaker Lighthouse. Early field units were rusted and used light crystals; newer models are cleaner designs with research into continuous operation and autonomous commands, with reserve units reportedly stockpiled for larger deployments.',
    history: [
      { session: 3, note: 'First encountered as a trio of rusted constructs in an ambush on the Old Trade Road.' },
      { session: 5, note: 'Upgraded units and a titan-scale chassis were observed during the Lighthouse infiltration.' },
      { session: 6, note: 'The goal of continuous operation is linked to the synthetic crystal program.' },
      { session: 7, note: 'New-model units posted at Bastion East Gate (inactive) and on Lighthouse exterior watch as security posture shifts.' },
      { session: 11, note: 'Reeves mentioned "new models" could easily handle the resistance.' },
      { session: 14, note: 'Party warned Hýrda that dozens of dormant units were stored at the Lighthouse and could be deployed as reinforcements.' }
    ],
    connections: [
      { type: 'location', id: 'duskbreaker-lighthouse', reason: 'Manufactured and researched here' },
      { type: 'location', id: 'old-trade-road', reason: 'Ambush site for early models' },
      { type: 'lore', id: 'light-crystals', reason: 'Powered by light crystals' },
      { type: 'location', id: 'bastion-east-gate', reason: 'Deployed as part of city security' },
      { type: 'location', id: 'hyrta-ducal-encampment', reason: 'Potential reinforcement target in the Hýrda mine conflict' }
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
      { session: 6, note: 'Implicated in the secret synthesis program through liaison Donnathan Reeves, who delivers subjects.' },
      { session: 9, note: 'Schism regarding warforged mentioned; Eduard argues they are gifts of light.' }
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
  },
  {
    id: 'torchlight-college',
    term: 'Torchlight College',
    description: 'The premiere educational institution of The Hariolar Empire, located in Ordonne province about a day\'s wagon ride from Pharus. A five-year boarding program for nobility and aristocracy beginning at age 16.',
    fullText: `The premiere educational institution of The Hariolar Empire, located within Ordonne imperial province, about a day's wagon ride from Pharus.

## Education and Enrollment

At the age of 16, members of the nobility and aristocracy attend to complete their education as well as socialize with their peers. It is a 5-year boarding program with boarding facilities.

The primary goal is to network among current generations to ensure they have ties they can call upon when they are in positions of power. All first-born, heir apparent, and heir presumptive are sent, while second-born and even third-born are not uncommon. Gifted nobility will also be sent. Lesser children will complete their education elsewhere.

## Recent Changes

Recently, the college has opened its doors to the newly rich, if they are willing to pay enough. There has also been a scholarship system available, funded by the Duskbreaker Lighthouse.`,
    connections: [
      { type: 'location', id: 'hariolar-empire', reason: 'Educational institution' },
      { type: 'location', id: 'ordonne', reason: 'Located in this province' },
      { type: 'location', id: 'pharus', reason: 'About a day\'s travel away' },
      { type: 'location', id: 'duskbreaker-lighthouse', reason: 'Funds scholarship program' },
      { type: 'npc', id: 'donnathan-reeves', reason: 'Alumnus' },
      { type: 'npc', id: 'duke-valerian-oliander', reason: 'Alumnus' },
      { type: 'npc', id: 'lady-ophelia-xanteres-oliander', reason: 'Recent graduate' }
    ],
    history: [
      { session: 8, note: 'Revealed as alma mater where Reeves and Duke Valerian met' },
      { session: 10, note: 'Lady Ophelia returned from the college, sparking the ball in her honor' }
    ]
  },
  {
    id: 'marchenbau',
    term: 'Marchenbau',
    description: 'Noble family from the imperial province of Boixden. Proctor Eduard is the fifth son of the previous Marchioness.',
    connections: [
      { type: 'location', id: 'boixden', reason: 'Family seat' },
      { type: 'npc', id: 'proctor-eduard', reason: 'Fifth son of previous Marchioness' },
      { type: 'npc', id: 'empress-consort-lyssandra', reason: 'Family member, Eduard\'s grand-niece' }
    ],
    history: [
      { session: 8, note: 'Eduard\'s noble lineage revealed during conversation with Reeves' }
    ]
  },
  {
    id: 'imperial-peerage',
    term: 'Imperial Peerage System',
    description: 'The hierarchical system of nobility in The Hariolar Empire, including ranks from Emperor/Empress down through Grand Duke/Duchess, Marquess/Marchioness, Count/Countess, Viscount/Viscountess, to Baron/Baroness.',
    fullText: `The formal system of nobility and forms of address in The Hariolar Empire.

## Direct Speech

| Rank                       | Formal                                                       | Styled Subsequent |
| -------------------------- | ------------------------------------------------------------ | ----------------- |
| Emperor / Empress          | Your Holy Radiance, Emperor / Empress of the Hariolar Empire | Your Radiance     |
| Grand Duke / Grand Duchess | Your Grace Grand Duke / Duchess of {Land}                    | Your Grace        |
| Marquess / Marchioness     | Your Most Honorable Marquess / Marchioness of {Land}         | My Lord / Lady    |
| Count / Countess           | Your Right Honorable Count / Countess of {Land}              | My Lord / Lady    |
| Viscount / Viscountess     | Your Honorable Viscount / Viscountess of {Land}              | My Lord / Lady    |
| Baron / Baroness           | Your Honorable Baron / Baroness of {Land}                    | My Lord / Lady    |

## Indirect Speech

| Rank                       | Option 1                                                          | Option 2                           |
| -------------------------- | ----------------------------------------------------------------- | ---------------------------------- |
| Emperor / Empress          | His / Her Holy Radiance, Emperor / Empress of the Hariolar Empire | His / Her Radiance                 |
| Grand Duke / Grand Duchess | Grand Duke / Duchess {First Name}                                 | His Grace {Family Name} / {Land}   |
| Marquess / Marchioness     | Marquess / Marchioness {First Name}                               | Lord / Lady {Family Name} / {Land} |
| Count / Countess           | Count / Countess {First Name}                                     | Lord / Lady {Family Name} / {Land} |
| Viscount / Viscountess     | Viscount / Viscountess {First Name}                               | Lord / Lady {Family Name} / {Land} |
| Baron / Baroness           | Baron / Baroness {First Name}                                     | Lord / Lady {Family Name} / {Land} |`,
    connections: [
      { type: 'location', id: 'hariolar-empire', reason: 'Governing system' }
    ],
    history: [
      { session: 8, note: 'Forms of address referenced in noble interactions' }
    ]
  },
  {
    id: 'whitaker-family',
    term: 'The Whitaker Brothers',
    description: 'A noble family from County Cork in Vaselia. The six Whitaker brothers are each identified by a signature color.',
    fullText: `The Whitaker family holds lands in County Cork, an inland province of Vaselia. Lord Whitaker has six sons, each associated with a signature color:

| Brother | Color | Status |
| ------- | ----- | ------ |
| Whitaker I | Red | Heir to the family lands |
| Whitaker II | Blue | Attended Torchlight College |
| Whitaker III | Orange | Exiled after a scandal involving a viscount's daughter at a ball |
| Whitaker IV | Brown | Explorer, currently traveling in Boaden |
| Whitaker V | Yellow | Joined the Eulogian clergy |
| Whitaker VI (Witty) | Purple | Aspiring alchemist in Bastion City |

The family employs halfling servants who traditionally adopt "normal" human names. Witty's manservant Jarvis has recently gone missing, along with a large portion of Witty's wardrobe.`,
    connections: [
      { type: 'location', id: 'vaselia', reason: 'Family province' },
      { type: 'character', id: 'witty', reason: 'Sixth son' },
      { type: 'lore', id: 'torchlight-college', reason: 'Whitaker II attended' }
    ],
    history: [
      { session: 10, note: 'Brothers referenced when party adopted Whitaker identities for the ball' },
      { session: 11, note: 'Cover used for the Grand Duke\'s ball; Reeves and the Duke suspect/know the brothers are fakes.' }
    ]
  }
];

export default lore;

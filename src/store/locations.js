// Location data for the world

export const locations = [
  {
    id: 'dunston-and-kirks',
    name: 'Dunston & Kirk\'s',
    type: 'poi',
    description: 'A bespoke workshop in Bastion City where gnomes, dwarves, halflings, and elves craft custom devices including hot air balloons. They do not stock inventory—everything is made to order with a minimum 4-week turnaround.',
    tags: ['workshop', 'bastion city'],
    history: [
      { session: 12, note: 'Party visited to procure a balloon but learned 4-week minimum turnaround made it impractical' }
    ],
    connections: [
      { type: 'location', id: 'bastion-city', reason: 'Located in' }
    ]
  },
  {
    id: 'the-golden-goose',
    name: 'The Golden Goose',
    type: 'inn',
    description: 'An upscale hotel in Bastion City where Nyx has booked a room using a sickle as collateral. Often mistakenly called "The Golden Dove."',
    tags: ['hotel', 'bastion city'],
    history: [
      { session: 10, note: 'Nyx booked a room here; party used it as meeting point' }
    ],
    connections: [
      { type: 'location', id: 'bastion-city', reason: 'Located In' }
    ]
  },
  {
    id: 'lord-whitakers-estate',
    name: 'Lord Whitaker\'s Estate',
    type: 'poi',
    description: 'The Bastion City residence of Lord Whitaker the 6th, located on the West Side. Used as staging ground for the ball infiltration.',
    tags: ['residence', 'west bastion'],
    history: [
      { session: 10, note: 'Party prepared for the ball here; Berridin cooked spicy curry' },
      { session: 12, note: 'Party regrouped here morning after the ball; discussed Black Swan bounty via sending stones' }
    ],
    connections: [
      { type: 'location', id: 'bastion-city', reason: 'Located in West Bastion' },
      { type: 'npc', id: 'lord-whitaker-6th', reason: 'Owner' }
    ]
  },
  {
    id: 'hieroterra',
    name: 'Hieroterra',
    type: 'province',
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
    id: 'hariolar-empire',
    name: 'The Hariolar Empire',
    type: 'empire',
    description: 'The imperial polity encompassing provinces like Hieroterra and Ordonne; home of the Eulogia of the Eternal Light.',
    connections: [
      { type: 'location', id: 'boixden', reason: 'Province within the empire' },
      { type: 'location', id: 'hieroterra', reason: 'Province within the empire' },
      { type: 'location', id: 'ordonne', reason: 'Province within the empire' },
      { type: 'location', id: 'vaselia', reason: 'Province within the empire' },
      { type: 'location', id: 'pharus', reason: 'Seat of imperial power' }
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
      { type: 'lore', id: 'nites', reason: 'Site of Nites\'s sacrifice' }, 
      { type: 'lore', id: 'first-emperor', reason: 'Founded by the First Emperor' }
    ]
  },
  {
    id: 'ordonne',
    name: 'Ordonne',
    type: 'province',
    description: 'A western imperial province and the heart of The Hariolar Empire. It houses the imperial capital of Pharus.',
    connections: [
      { type: 'location', id: 'pharus', reason: 'Contains Pharus (Capital)' },
      { type: 'lore', id: 'pilgrimage-enlightened', reason: 'Ending point of the Pilgrimage' }
    ]
  },
  {
    id: 'torchlight-college',
    name: 'Torchlight College',
    type: 'poi',
    description: 'The empire\'s premier university in Ordonne, alma mater to nobles like Donnathan Reeves and Duke Valerian Oliander.',
    tags: ['academy', 'ordonne'],
    history: [
      { session: 8, note: 'Reeves planned to visit while coordinating with Grand Duke Valerian Oliander.' }
    ],
    connections: [
      { type: 'location', id: 'ordonne', relationship: 'Located In' },
      { type: 'npc', id: 'donnathan-reeves', reason: 'Alumnus' },
      { type: 'npc', id: 'duke-valerian-oliander', reason: 'Alumnus' },
      { type: 'lore', id: 'torchlight-college', reason: 'Central institution' }
    ]
  },
  {
    id: 'duskbreaker-lighthouse',
    name: 'Duskbreaker Lighthouse',
    type: 'landmark', // Or 'poi' if you prefer
    description: 'A tall lighthouse on the coast of Bastion City, known for its magical beacon.',
    fullText: 'The locus of [[Light Crystal]] research in the empire. Composed of various magic users, artificers, and artisans, they all work together to develop the latest technology.\n\nDespite being headquartered in a tall tower in the east side of [[Bastion City]], most of its finding are exported to [[Pharus]]. The first use case of light crystals were replacing the candlelit streetlamps in Bastion City.',
    tags: ['landmark', 'bastion city'],
    history: [
      { session: 1, note: 'Introduced as the source of new light crystal technology.' },
      { session: 3, note: 'Linked to warforged constructs encountered outside the city.' },
      { session: 4, note: 'Spider recon reveals a deep underground complex beneath the structure.' },
      { session: 5, note: 'Infiltration maps R&D floors; titan chassis and advanced warforged observed.' },
      { session: 6, note: 'Basement lab confirmed to be synthesizing crystals from living subjects.' },
      { session: 7, note: 'Security increased with modern warforged deployment' },
      { session: 8, note: 'Security breach; party\'s rune passes compromised; forecourt battle with warforged' }
    ],
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
    history: [
      { session: 2, note: 'Ellara learns of Meri\'s transfer to Proctor Eduard\'s custody.' },
      { session: 3, note: 'Ellara confronts Proctor Eduard, who says he gave orders to releas Meri.' },
      { session: 4, note: 'Ellara reports the warforged attack; Eduard pledges to escalate the matter.' },
      { session: 7, note: 'Eduard introduces Reeves to Ellara in mess hall' },
      { session: 12, note: 'Ellara received Eduard\'s blessing and a theology book before departing for Hýrda' }
    ],
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
    history: [
      { session: 3, note: 'Party waits while Ellara meets with Eduard; Tsi\'Nyra tries alcohol for the first time.' }
    ],
    connections: [
      { type: 'location', id: 'bastion-city', relationship: 'Located In' }
    ]
  },
  {
    id: 'stone-span-bridge',
    name: 'Stone-span Bridge',
    type: 'landmark',
    description: 'The wrought-iron and stone bridge connecting East and West Bastion. Site of many crossings and first impressions.',
    history: [
      { session: 2, note: 'Party crosses into West Bastion for the first time to investigate the prisons.' }
    ],
    connections: [
      { type: 'location', id: 'bastion-city', relationship: 'Within city' }
    ]
  },
  {
    id: 'old-trade-road',
    name: 'Old Trade Road',
    type: 'poi',
    description: 'An old artery out of Bastion City leading eastward. Recent ambush site by rusted warforged constructs.',
    fullText: 'Near-dawn campfire remnants and cart tracks led to three rusted warforged powered by light crystals, staged as an ambush beyond the east gate. Crystalline cores were recovered as evidence.',
    tags: ['road', 'ambush'],
    history: [
      { session: 3, note: 'Site of the ambush by three rusted warforged constructs, which were confirmed to be from the Lighthouse.' },
      { session: 4, note: 'Party determines the trap was not for Meri and returns to the city.' }
    ],
    connections: [
      { type: 'location', id: 'bastion-city', relationship: 'Begins at East Gate' },
      { type: 'lore', id: 'warforged', reason: 'Field test encounter' },
      { type: 'lore', id: 'light-crystals', reason: 'Recovered crystal cores' }
    ]
  },
  {
    id: 'faberge-workshop',
    name: "Faberge's Workshop",
    type: 'poi',
    description: 'Personal laboratory of Michelle Faberge in West Bastion, used for research notes on crystal power concurrency and civic water purification.',
    tags: ['workshop', 'west bastion'],
    history: [
      { session: 5, note: 'Ellara meets Darius here where he remarks on Ms. Faberge\'s absence.' },
      { session: 6, note: 'Darius returns, realizes Faberge is actually missing, and goes to report it.' }
    ],
    connections: [
      { type: 'location', id: 'bastion-city', relationship: 'Located In' },
      { type: 'lore', id: 'light-crystals', reason: 'Energy concurrency research' }
    ]
  },
  {
    id: 'guard-bar-west',
    name: 'Unnamed Guard Bar',
    type: 'poi',
    description: 'A nondescript bar frequented by Lighthouse guards for poker and drinks. Source of shift gossip and lax security culture.',
    tags: ['bar', 'west bastion'],
    history: [
      { session: 5, note: 'Berridin overhears guard chatter about poker and routines, exposing lax security.' }
    ],
    connections: [
      { type: 'location', id: 'bastion-city', relationship: 'Located In' },
      { type: 'location', id: 'duskbreaker-lighthouse', relationship: 'Guards off-duty hangout' }
    ]
  },
  {
    id: 'stonewall-tower',
    name: 'Stonewall Tower',
    type: 'prison',
    description: 'A three-story watch-prison in West Bastion with an adamant door. Bribed guard admitted Meri was held then transferred a month prior.',
    tags: ['prison', 'west bastion'],
    history: [
      { session: 2, note: 'Bribed inquiry reveals Meri was held then transferred; Berridin finds the transfer ledger naming Proctor Eduard.' }
    ],
    connections: [
      { type: 'location', id: 'bastion-city', relationship: 'Located In' },
      { type: 'npc', id: 'proctor-eduard', reason: 'Named on custody transfer ledger' }
    ]
  },
  {
    id: 'halfling-quarter',
    name: 'Halfling Quarter',
    type: 'poi',
    description: 'A residential area in East Bastion, home to a close-knit halfling community. Mentioned in Session 1.',
    tags: ['residential', 'east bastion'],
    history: [
      { session: 1, note: 'Berridin led Ysidor here after the Alms Giving, where Ysidor met the local children.' }
    ],
    connections: [
      { type: 'location', id: 'bastion-city', relationship: 'Located In' }
    ]
  },
  {
    id: 'lighthouse-med-bay',
    name: 'Lighthouse Medical Bay',
    type: 'poi',
    description: 'Medical facility within the Duskbreaker Lighthouse where subjects from the basement program are monitored.',
    tags: ['medical', 'lighthouse'],
    history: [
      { session: 6, note: 'Meri was moved here from the lab before being extracted via Dimension Door.' }
    ],
    connections: [
      { type: 'location', id: 'duskbreaker-lighthouse', reason: 'Medical facility within the Lighthouse' }
    ]
  },
  {
    id: 'old-growth-tree',
    name: 'Old Growth Tree',
    type: 'poi',
    description: 'A large ancient gnarled tree outside Bastion City used as a rendezvous point. Distinguished from any "mangled" trees in the area.',
    tags: ['natural', 'meeting point'],
    history: [
      { session: 6, note: 'The party regrouped here after escaping the Lighthouse with Meri.' },
      { session: 7, note: 'Starting point for the night flight and party discussions' }
    ],
    connections: [
      { type: 'location', id: 'bastion-city', reason: 'Outside the city limits' }
    ]
  },
  {
    id: 'basement-lab',
    name: 'Basement Synthesis Laboratory',
    type: 'facility',
    description: 'Hidden laboratory beneath the Duskbreaker Lighthouse where light crystals are synthesized from living Shadowed subjects.',
    history: [
      { session: 4, note: 'Existence hinted at by spider reconnaissance revealing a deep underground complex.' },
      { session: 6, note: 'Infiltrated by Berridin; Meri found as a test subject for crystal synthesis.' }
    ],
    connections: [
      { type: 'location', id: 'duskbreaker-lighthouse', reason: 'Located beneath' }
    ]
  },
  {
    id: 'lighthouse-deep-basement',
    name: 'Deep Underground Complex',
    type: 'facility',
    description: 'Deep, cold underground levels beneath the Lighthouse discovered by spider reconnaissance. Contains extensive insect populations and mysterious depths.',
    history: [
      { session: 4, note: 'Spider reconnaissance reveals deep underground complex with strange noises.' },
      { session: 5, note: 'Mentioned as unexplored depths below the main facilities.' }
    ],
    connections: [
      { type: 'location', id: 'duskbreaker-lighthouse', reason: 'Deep levels beneath' }
    ]
  },
  {
    id: 'lighthouse-engineering-floor',
    name: 'Engineering Floor (Floor 10)',
    type: 'facility',
    description: 'Engineering department of the Lighthouse where Beth works on Titan application files and prototype development.',
    history: [
      { session: 5, note: 'Berridin visits but finds Beth absent; acquires a prototype device.' }
    ],
    connections: [
      { type: 'location', id: 'duskbreaker-lighthouse', reason: 'Floor 10 of the Lighthouse' }
    ]
  },
  {
    id: 'lighthouse-arcana-floor',
    name: 'High Arcana Floor (Wizard Scriptorium)',
    type: 'facility', 
    description: 'Upper floor of the Lighthouse housing wizard consultants, arcane libraries, and advanced magical research. Where Lex works.',
    history: [
      { session: 5, note: 'Berridin explores, finding an extensive magical library and that Lex is absent.' }
    ],
    connections: [
      { type: 'location', id: 'duskbreaker-lighthouse', reason: 'Upper floor of the Lighthouse' }
    ]
  },
  {
    id: 'nyxs-townhouse',
    name: "Nyx's Townhouse",
    type: 'poi',
    description: 'A five-story, unassuming building in East Bastion serving as Nyx\'s residence. Modestly upscale with polished wood and nice fixtures.',
    tags: ['residence', 'east bastion'],
    history: [
      { session: 1, note: 'Introduced as Nyx\'s residence where he receives a letter and hosts Tsi\'Nyra.' },
      { session: 2, note: 'Described as modestly upscale for East Bastion with nice fixtures.' },
      { session: 10, note: 'Berridin and Ysidor stayed here; raided Nyx\'s cache for gold' }
    ],
    connections: [
      { type: 'location', id: 'bastion-city', reason: 'Located In' }
    ]
  },
  {
    id: 'abandoned-barn',
    name: 'Abandoned Barn',
    type: 'poi',
    description: 'A decrepit barn north of Bastion City used as shelter during the party\'s escape.',
    tags: ['shelter', 'north bastion'],
    history: [
      { session: 7, note: 'Used as shelter during escape from the Lighthouse' }
    ],
    connections: [
      { type: 'location', id: 'bastion-city', reason: 'North of the city' }
    ]
  },
  {
    id: 'hyrta',
    name: 'Hýrda',
    type: 'village',
    description: 'A goliath village in the mountains, home to Meri and Ysidor. Currently threatened by imperial mining interests with soldiers encamped nearby under a ducal decree.',
    tags: ['village', 'goliath', 'mountains'],
    history: [
      { session: 1, note: 'Ysidor\'s home village.' },
      { session: 7, note: 'Meri is heading home as it is facing mining disputes' },
      { session: 12, note: '~20 soldiers encamped nearby under ducal decree; party en route by carriage' }
    ],
    connections: [
      { type: 'location', id: 'hieroterra', reason: 'Village within the province' }
    ]
  },
  {
    id: 'bastion-east-gate',
    name: 'Bastion East Gate',
    type: 'poi',
    description: 'The eastern entrance to Bastion City, now featuring increased security with modern warforged posted as of Session 7.',
    tags: ['gate', 'security', 'bastion city'],
    history: [
      { session: 7, note: 'New warforged security measures implemented' }
    ],
    connections: [
      { type: 'location', id: 'bastion-city', reason: 'Eastern entrance' },
      { type: 'location', id: 'old-trade-road', reason: 'Gate leads to the old trade road' }
    ]
  },
  {
    id: 'small-watch-house',
    name: 'Small Watch-House (Prison #1)',
    type: 'prison',
    description: 'A modest prison facility in West Bastion. Guard attempted bribery but provided minimal information.',
    tags: ['prison', 'west bastion'],
    history: [
      { session: 2, note: 'Party attempts bribery for information; directed to "try Eighth Avenue."' }
    ],
    connections: [
      { type: 'location', id: 'bastion-city', reason: 'Located In' }
    ]
  },
  {
    id: 'shadier-bar-east',
    name: 'Shadier Bar (East Bastion)',
    type: 'tavern',
    description: 'A watering hole in a shadier area of East Bastion where Nyx gathers information from locals and guards.',
    tags: ['tavern', 'east bastion', 'information'],
    history: [
      { session: 1, note: 'Nyx visits to seek information about missing folk; learns about Meri from a guard who becomes ill.' }
    ],
    connections: [
      { type: 'location', id: 'bastion-city', reason: 'Located In' }
    ]
  },
  {
    id: 'civic-hall-of-records',
    name: 'Civic Hall of Records',
    type: 'poi',
    description: 'Administrative center in West Bastion holding housing and property records.',
    tags: ['government', 'west bastion'],
    history: [
      { session: 9, note: 'Nyx accessed records to find Reeves\' estate address.' }
    ],
    connections: [
      { type: 'location', id: 'bastion-city', relationship: 'Located In' }
    ]
  },
  {
    id: 'lady-jacintas-estate',
    name: 'Lady Jacinta\'s Estate',
    type: 'poi',
    description: 'The manor of Lady Jacinta in West Bastion. A place of aggressive hospitality.',
    tags: ['residence', 'west bastion'],
    history: [
      { session: 9, note: 'Ysidor was taken here for medical attention; Nyx retrieved him.' },
      { session: 11, note: 'Witty woke up here after the ball; Jacintha provided breakfast and gossip.' },
      { session: 12, note: 'Witty and Berridin visited to inquire about balloon procurement and horses' }
    ],
    connections: [
      { type: 'location', id: 'bastion-city', relationship: 'Located In' },
      { type: 'npc', id: 'lady-jacinta', reason: 'Owner' }
    ]
  },
  {
    id: 'the-golden-dove',
    name: 'The Golden Dove',
    type: 'tavern',
    description: 'A high-end tavern near the Ducal Palace. Nyx has claimed to be staying here as part of a cover story.',
    tags: ['tavern', 'luxury', 'west bastion'],
    history: [
      { session: 9, note: 'Scouted by Ellara and Berridin; Nyx claims to be staying here.' }
    ],
    connections: [
      { type: 'location', id: 'bastion-city', relationship: 'Located In' },
      { type: 'location', id: 'ducal-palace', relationship: 'Nearby' }
    ]
  },
  {
    id: 'boaden',
    name: 'Boaden',
    type: 'location',
    description: 'A distant location where Whitaker 4 (Nyx\'s cover) was supposedly traveling. Mentioned by Donnathan Reeves as being far from Bastion.',
    history: [
      { session: 11, note: 'Mentioned by Donnathan Reeves as a place difficult to reach from Bastion.' }
    ],
    connections: []
  },
  {
    id: 'badwater-well',
    name: 'Badwater Well',
    type: 'poi',
    description: 'An obscure landmark in East Bastion used as a discreet meeting point.',
    tags: ['meeting point', 'east bastion'],
    history: [
      { session: 8, note: 'Designated as rendezvous point after the Lighthouse gate incident' },
      { session: 9, note: 'Party rendezvous point; Nyx confirms safety.' }
    ],
    connections: [
      { type: 'location', id: 'bastion-city', reason: 'Located In' }
    ]
  },
  {
    id: 'luxembough',
    name: 'Luxembough',
    type: 'capital',
    description: 'The fortified capital of the province of Boixden and ancestral seat of the Marchenbau family.',
    tags: ['capital', 'boixden'],
    history: [
      { session: 8, note: 'Identified as the Marchenbau family\'s provincial seat during the Meri investigation.' }
    ],
    connections: [
      { type: 'location', id: 'boixden', relationship: 'Province Capital' },
      { type: 'lore', id: 'marchenbau', reason: 'Family seat' }
    ]
  },
  {
    id: 'boixden',
    name: 'Boixden',
    type: 'province',
    description: 'An imperial province of The Hariolar Empire, home to the noble Marchenbau family.',
    history: [
      { session: 8, note: 'Revealed as home province of Proctor Eduard\'s family' }
    ],
    connections: [
      { type: 'lore', id: 'marchenbau', reason: 'Home of the Marchenbau family' }
    ]
  },
  {
    id: 'vaselia',
    name: 'Vaselia',
    type: 'province',
    description: 'A fertile coastal province of the Hariolar Empire renowned for its luminous vineyards and viscounties.',
    history: [
      { session: 8, note: 'Viscount Donnathan Reeves referenced his family holdings here while departing Bastion.' }
    ],
    connections: [
      { type: 'npc', id: 'donnathan-reeves', reason: 'Holds the title Viscount Sommeil here' }
    ]
  },
  {
    id: 'sommeil',
    name: 'Sommeil',
    type: 'town',
    description: 'The viscounty seat of Donnathan Reeves, nestled among Vaselia\'s vineyards and famed for luminous wines.',
    tags: ['town', 'vaselia', 'vineyards'],
    history: [
      { session: 8, note: 'Reeves confirmed his title as Viscount Sommeil before departing for the ducal palace.' }
    ],
    connections: [
      { type: 'location', id: 'vaselia', relationship: 'Viscounty within the province' },
      { type: 'npc', id: 'donnathan-reeves', reason: 'Title holder' }
    ]
  },
  {
    id: 'ducal-palace',
    name: 'Ducal Palace',
    type: 'landmark',
    description: 'The residence and seat of power for Duke Valerian Oliander in Bastion City. Director Reeves frequently visits for days at a time.',
    tags: ['palace', 'bastion city'],
    history: [
      { session: 8, note: 'Reeves announced plans to visit for several days' },
      { session: 9, note: 'Scouted by Ellara and Berridin; deactivated warforged observed at gates.' },
      { session: 10, note: 'Site of the Grand Duke\'s ball; party infiltrated as Whitaker brothers' },
      { session: 11, note: 'The ball continued here; party gathered intel and eavesdropped on the leadership.' }
    ],
    connections: [
      { type: 'location', id: 'bastion-city', reason: 'Located In' },
      { type: 'npc', id: 'duke-valerian-oliander', reason: 'Ducal residence' },
      { type: 'npc', id: 'donnathan-reeves', reason: 'Frequent visitor' }
    ]
  }
];

export default locations;
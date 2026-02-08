// NPC data for the world

export const npcs = [
    // Major NPCs (show like CharactersView with portraits/avatars)
    {
        id: 'lady-ophelia-xanteres-oliander',
        name: 'Lady Ophelia Xanteres Oliander',
        role: 'Marchioness of Bastion City',
        location: 'Ducal Palace, Bastion City',
        description: 'Grand Duke Valerian Oliander\'s niece and heir. Recently returned from Torchlight College. The ball was held in her honor.',
        history: [
            { session: 10, note: 'Introduced at the ball; hinted at army delays at a mining town' },
            { session: 11, note: 'Danced with Berridin; discussed "false light" with Ellara; revealed knowledge of resistance.' }
        ],
        connections: [
            { type: 'npc', id: 'duke-valerian-oliander', reason: 'Niece and heir' },
            { type: 'lore', id: 'torchlight-college', reason: 'Recent graduate' },
            { type: 'location', id: 'ducal-palace', reason: 'Resides at' }
        ]
    },
    {
        id: 'meri',
        name: 'Meri',
        role: 'Goliath Mentor',
    location: 'Heading to Hýrda',
        description: 'Mentor to Ysidor. Arrested in Bastion City after speaking against the Lighthouse; later found captive beneath the Lighthouse and rescued. Is now heading to her home village with Ysidor\'s sending stone.',
        fullText: 'A towering goliath of granite-gray skin and lilac-silver hair, Meri served as Ysidor\'s mentor, drilling him in blessing and stance with her characteristic phrase: "Hold your guard higher, little hill." After being reported as violent and dangerous following an altercation near the Lighthouse, she was transferred under Proctor Eduard\'s custody and ultimately subjected to horrific basement experiments involving crystal synthesis. She was rescued partway through the process and is now recovering from her ordeal.',
        history: [
            { session: 1, note: 'Established as Ysidor\'s missing mentor.' },
            { session: 2, note: 'Rumored transfer under Proctor Eduard after arrest in Bastion City.' },
            { session: 3, note: 'No sign in the old road.' },
            { session: 6, note: 'Found alive in basement lab; extracted to safety from the lighthouse.' },
            { session: 7, note: 'Rescued and freed; departed for Hýrda' },
            { session: 11, note: 'Target of a "Black Swan" commission: a 250g bounty on her head.' },
            { session: 12, note: 'Reported ~20 soldiers encamped near Hýrda under ducal decree; party contacted via sending stone' },
            { session: 13, note: 'A bounty hunter sent after her was killed on the road; a note read "Hyrda".' }
        ],
        connections: [
            { type: 'character', id: 'ysidor', reason: 'Mentor and guardian' },
            { type: 'location', id: 'duskbreaker-lighthouse', reason: 'Held captive beneath the Lighthouse' },
            { type: 'location', id: 'hyrta', reason: 'Home village' },
            { type: 'lore', id: 'light-crystals', reason: 'Subject of crystal synthesis process' }
        ]
    },
    {
        id: 'samantha',
        name: 'Samantha',
        role: 'Bounty Hunter (Disguised)',
        location: 'Road to Hýrda',
        description: 'A bounty hunter who posed as a desperate mother to infiltrate the party; killed at their campfire.',
        history: [
            { session: 13, note: 'Posed as a traveler with a baby to ambush the party; killed in the ensuing fight.' }
        ],
        connections: [
            { type: 'npc', id: 'meri', reason: 'Targeted for bounty' },
            { type: 'location', id: 'hyrta', reason: 'Heading toward Hýrda to find Meri' }
        ]
    },
    {
        id: 'lady-jacinta',
        name: 'Lady Jacinta',
        role: 'Noblewoman',
        location: 'West Bastion',
        description: 'Elderly, wealthy widow with an "open heart" who is friends with Donnathan Reeves\' mother.',
        history: [
            { session: 9, note: 'Mistook Ysidor for a sickly boy and "rescued" him; revealed Reeves\' relationship with the Duke.' },
            { session: 11, note: 'Hosted Witty after the ball; shared gossip about Ophelia and the Duke.' },
            { session: 12, note: 'Advised Witty to visit Dunston & Kirk\'s for a balloon; warned him about Berridin as a swindler' }
        ],
        connections: [
            { type: 'npc', id: 'donnathan-reeves', reason: 'Family friend' },
            { type: 'location', id: 'lady-jacintas-estate', reason: 'Resides at' }
        ]
    },
    {
        id: 'guard-diane',
        name: 'Diane',
        role: 'Ducal Guard',
        location: 'The Golden Dove',
        description: 'A pious Eulogian guard stationed at The Golden Dove.',
        history: [
            { session: 9, note: 'Confirmed Proctor Eduard attends ducal functions.' }
        ],
        connections: [
            { type: 'location', id: 'the-golden-dove', reason: 'Stationed at' }
        ]
    },
    {
        id: 'michelle-faberge',
        name: 'Michelle Faberge',
        role: 'Director of Research, Duskbreaker Lighthouse',
        location: 'West Bastion',
        prominence: 'minor',
        description: 'Once brilliant artificer-scientist leading research at the Lighthouse; killed during a pursuit in West Bastion. Her workshop held notes on power concurrency and a Dimension Door rune. Deceased.',
        fullText: 'Michelle Faberge was a brilliant artificer-scientist who served as Director of Research at the Duskbreaker Lighthouse. Her workshop revealed extensive notes on power concurrency problems affecting both warforged long-term energy systems and east-side water purification infrastructure. Among her personal effects was a disturbing notation questioning "How much more blood will this cost." She possessed experimental runestones capable of casting spells like Dimension Door, suggesting she was preparing contingency plans. Her death during a street pursuit has created gaps in the Lighthouse\'s research hierarchy and security protocols.',
        history: [
            { session: 5, note: 'Killed during pursuit; her pass and notes enabled infiltration.' },
            { session: 6, note: 'Reported missing; workshop examined; Darius alarmed.' }
        ],
        connections: [
            { type: 'location', id: 'duskbreaker-lighthouse', reason: 'Director of Research' },
            { type: 'location', id: 'faberge-workshop', reason: 'Personal laboratory' },
            { type: 'lore', id: 'light-crystals', reason: 'Core research domain' }
        ]
    },
    {
        id: 'proctor-eduard',
        name: 'Proctor Eduard',
        role: 'Eulogian Proctor',
        location: 'Eulogian Seminary, West Bastion',
        description: 'Ellara\'s mentor at the Seminary. As the fifth son of the previous Marchioness of Marchenbau, he was sent to the seminary instead of Torchlight College. He is the grand-uncle of Empress Consort Lyssandra. Directly implicated by Meri as a figure she saw after being captured.',
        fullText: 'Proctor Eduard projects calm authority and orthodoxy within the Eulogian Seminary. As the fifth son of the previous Marchioness of Marchenbau, he was sent to the seminary instead of Torchlight College. He is the grand-uncle of Empress Consort Lyssandra. He warned of Lighthouse hubris and claimed to have set Meri free, directing concerned parties away from further investigation. However, Meri\'s testimony directly identified him as the priest who attached her to the synthesis machine. This revelation paints his previous actions and denials in a sinister light, suggesting deep complicity in the Lighthouse\'s atrocities, despite his outward piety and condemnation of their "ambition."',
        history: [
            { session: 2, note: 'Named on custody transfer ledger for Meri.' },
            { session: 3, note: 'Claimed to have released Meri, directing the party out of the city.' },
            { session: 4, note: 'Expressed shock; promised to escalate investigation.' },
            { session: 6, note: 'Complicity questioned via Reeves hand-offs; stance uncertain.' },
            { session: 7, note: 'Directly implicated by Meri since she was able to describe him after her capture' },
            { session: 8, note: 'Reveals Marchenbau heritage and cautions Ellara that Reeves is bound to his own ambitions.' },
            { session: 10, note: 'Invited Ellara to the Grand Duke\'s ball; escorted her as his guest' },
            { session: 11, note: 'Privately claimed to control Ellara, stating she will "do as expected."' },
            { session: 12, note: 'Gave Ellara his blessing to travel and gifted her "Josephine\'s Insights on the Nature of Eulogia"' }
        ],
        connections: [
            { type: 'character', id: 'ellara', reason: 'Mentor at the Seminary' },
            { type: 'location', id: 'eulogian-seminary', reason: 'Post and influence' },
            { type: 'location', id: 'stonewall-tower', reason: 'Named in custody transfer ledger (Session 2)' },
            { type: 'lore', id: 'eulogia-eternal-light', reason: 'Clergy of the faith' },
            { type: 'lore', id: 'marchenbau', reason: 'Scion of the Marchenbau noble house' },
            { type: 'npc', id: 'donnathan-reeves', reason: 'Old ally and political liaison' },
            { type: 'npc', id: 'empress-consort-lyssandra', reason: 'Grand-uncle' }
        ]
    },
    {
        id: 'donnathan-reeves',
        name: 'Donnathan Reeves',
        role: 'Director of Relations, Duskbreaker Lighthouse',
        location: 'Bastion City & Pharus',
        prominence: 'minor',
        description: 'Viscount Donnathan "Lord Sommeil" Reeves, the Lighthouse\'s diplomatic liaison to imperial nobility and the Eulogians; named as the hand-off agent for living "subjects".',
        fullText: 'Donnathan Reeves serves as the diplomatic face of the Duskbreaker Lighthouse, frequently traveling to maintain relationships with political authorities, particularly in the capital city of Pharus. Basement laboratory testimony has identified him as the crucial liaison who facilitates the delivery of living "subjects" into Lighthouse custody for crystal synthesis experiments. These transfers are conducted "per protocol," suggesting an established and sanctioned arrangement between the Lighthouse and Eulogian authorities. His role makes him a key political lever and potentially the keystone figure in understanding the full scope of the institutional conspiracy. Session 8 revealed that Reeves holds the hereditary title Viscount Sommeil, hails from a vintner family, and maintains direct access to Grand Duke Valerian Oliander, rekindling Torchlight College ties while shuttling between Bastion and the ducal palace. It is an "open secret" that he and the Duke are lovers.',
        history: [
            { session: 5, note: 'Identified as Director of Relations, liaising in Pharus.' },
            { session: 6, note: 'Named as hand-off for delivered "subjects" per protocol.' },
            { session: 7, note: 'Introduced to Ellara by Proctor Eduard in the Seminary mess hall.' },
            { session: 8, note: 'Confirmed as Viscount Sommeil; heading to the ducal palace after conferring with Proctor Eduard.' },
            { session: 9, note: 'Revealed to be the lover of Grand Duke Oliander; stays at the Palace.' },
            { session: 10, note: 'Greeted party at the ball; recognized "Orange" Whitaker with dangerous familiarity' },
            { session: 11, note: 'Confronted Nyx about Whitaker identity; revealed romantic relationship with Grand Duke Oliander.' }
        ],
        connections: [
            { type: 'location', id: 'duskbreaker-lighthouse', reason: 'Executive at the Lighthouse' },
            { type: 'location', id: 'pharus', reason: 'Operating theater in the capital' },
            { type: 'lore', id: 'lightkeepers', reason: 'Operates under/with the council' },
            { type: 'location', id: 'eulogian-seminary', reason: 'Present at Seminary; introduced to Ellara' },
            { type: 'location', id: 'ducal-palace', reason: 'Frequent visitor and liaison to the duke' },
            { type: 'npc', id: 'proctor-eduard', reason: 'Longtime ally coordinating political cover' },
            { type: 'npc', id: 'duke-valerian-oliander', reason: 'College acquaintance and romantic partner' },
            { type: 'lore', id: 'torchlight-college', reason: 'Alumnus; met Valerian at the college' }
        ]
    },
    {
        id: 'duke-valerian-oliander',
        name: 'Duke Valerian Oliander',
        role: 'Duke of Hieroterra',
        location: 'Bastion City',
        description: 'Provincial ruler of Hieroterra; mentioned as having been warned about the Lighthouse hubris and politics around light crystals. Revealed to be the lover of Donnathan Reeves.',
        history: [
            { session: 1, note: 'Named as Duke of Hieroterra during city introduction.' },
            { session: 4, note: 'Eduard claims to have warned the duke about Lighthouse hubris.' },
            { session: 9, note: 'Revealed to be the lover of Donnathan Reeves.' },
            { session: 10, note: 'Hosted the ball celebrating his niece Ophelia\'s return; greeted the party' },
            { session: 11, note: 'Hosted the ball; discussed resistance delays with inner circle.' }
        ],
        connections: [
            { type: 'location', id: 'bastion-city', reason: 'Seat of ducal power' },
            { type: 'location', id: 'hieroterra', reason: 'Province lord' },
            { type: 'npc', id: 'donnathan-reeves', reason: 'Romantic partner' },
            { type: 'npc', id: 'lady-ophelia-xanteres-oliander', reason: 'Niece and heir' }
        ]
    },
    {
        id: 'lex',
        name: 'Lex',
        role: 'Wizard Contractor',
        location: 'Duskbreaker Lighthouse',
        description: 'Contracted wizard working with Michelle Faberge on warforged power solutions and long-term energy storage.',
        history: [
            { session: 5, note: 'Mentioned as collaborator on warforged power systems.' },
            { session: 6, note: 'Research partnership with Faberge on energy bottleneck.' }
        ],
        connections: [
            { type: 'character', id: 'michelle-faberge', reason: 'Research collaborator' },
            { type: 'location', id: 'duskbreaker-lighthouse', reason: 'Contractor' }
        ]
    },
    {
        id: 'cooper',
        name: 'Cooper',
        role: 'Lighthouse Guard',
        location: 'Duskbreaker Lighthouse',
        description: 'Guard partnered with Stanley for specimen transport and security duties.',
        history: [
            { session: 6, note: 'Assisted in moving Meri from lab to medical bay.' }
        ],
        connections: [
            { type: 'character', id: 'stanley-guard', reason: 'Guard partner' },
            { type: 'location', id: 'duskbreaker-lighthouse', reason: 'Security staff' },
            { type: 'location', id: 'lighthouse-med-bay', reason: 'Transported subject to medical bay' }
        ]
    },
    {
        id: 'drunken-goose-barkeep',
        name: 'Barkeep',
        role: 'Tavern Keeper',
        location: 'The Drunken Goose',
        description: 'No-nonsense barkeep who serves the working class clientele. Strict about payment and tips.',
        history: [
            { session: 3, note: 'Served the party; complained about lack of tips.' }
        ],
        connections: [
            { type: 'location', id: 'drunken-goose', reason: 'Works at' }
        ]
    },
    {
        id: 'darius',
        name: 'Darius',
        role: 'Artificer',
        location: 'West Bastion',
        description: 'Curious, artificer skeptical about the Eulogia working on civic water purification and crystal research.',
        history: [
            { session: 5, note: 'Met Ellara; discussed artificer work and set an appointment.' },
            { session: 6, note: 'Returned to workshop; alarmed; intent to report Faberge missing.' }
        ],
        connections: [
            { type: 'location', id: 'faberge-workshop', reason: 'Met Ellara here; collaborator with Faberge' }
        ]
    },
    {
        id: 'denmother',
        name: 'The Denmother',
        role: 'Seminary Matron',
        location: 'Eulogian Seminary',
        description: 'Ellara\'s kindly superior with a fondness for confiscated romance scrolls and gossip. Deeply suspicious of nobility.',
        history: [
            { session: 1, note: 'Ellara sought information about Meri; advised she was likely in an eastern prison.' },
            { session: 2, note: 'Provided rumors about Nyx and Meri\'s transfer; comic relief via "romance scrolls."' },
            { session: 10, note: 'Gave Ellara a book on court manners; warned that nobles are "hedonists"' }
        ],
        connections: [
            { type: 'location', id: 'eulogian-seminary', reason: 'Seminary matron' }
        ]
    },
    {
        id: 'stanley-guard',
        name: 'Stanley',
        role: 'Lighthouse Guard',
        location: 'West Bastion',
        description: 'Guard with a gambling problem and marital troubles; inadvertently aided the party during the infiltration.',
        history: [
            { session: 5, note: 'Lax guard culture exposed via poker; identity used by Nyx.' },
            { session: 6, note: 'Underwent atonement ritual; hopefully reconciled with Aaron(?)' }
        ],
        connections: [
            { type: 'location', id: 'duskbreaker-lighthouse', reason: 'Employed as guard' },
            { type: 'location', id: 'guard-bar-west', reason: 'Frequent patron' },
            { type: 'character', id: 'aaron', reason: 'Spouse' }
        ]
    },
    {
        id: 'aaron',
        name: 'Aaron',
        role: 'Spouse of Stanley',
        location: 'West Bastion',
        description: 'Long-suffering husband of Stanley; reconciled after Ysidor\'s atonement guidance.',
        history: [
            { session: 5, note: 'Stanley\'s husband who is sick of his drinking and gambling.' },
            { session: 6, note: 'Initially resistant to Stanley\'s return; hopefully reconciled?' }
        ],
        connections: [
            { type: 'character', id: 'stanley-guard', reason: 'Spouse' }
        ]
    },
    {
        id: 'beth',
        name: 'Beth',
        role: 'Engineering Contact',
        location: 'Duskbreaker Lighthouse',
        description: 'Engineering department contact on Floor 10 who holds Titan application files. Was absent during Berridin\'s infiltration.',
        history: [
            { session: 5, note: 'Named as Engineering contact with Titan files; absent during infiltration.' }
        ],
        connections: [
            { type: 'location', id: 'lighthouse-engineering-floor', reason: 'Works in Engineering' },
            { type: 'location', id: 'duskbreaker-lighthouse', reason: 'Engineering staff' }
        ]
    },
    {
        id: 'tingle',
        name: 'Tingle',
        role: 'Research Subordinate',
        location: 'Duskbreaker Lighthouse',
        description: 'Nervous subordinate who reported to "Director Faberge" about transverse law complications and phosphorus component breakthroughs for long-term power sources.',
        history: [
            { session: 5, note: 'Provided technical briefing on crystal power enhancement and warforged applications.' }
        ],
        connections: [
            { type: 'character', id: 'michelle-faberge', reason: 'Research subordinate' },
            { type: 'location', id: 'duskbreaker-lighthouse', reason: 'Staff member' }
        ]
    },
    {
        id: 'dawn',
        name: 'Dawn',
        role: 'Lead Technician (Basement Lab)',
        location: 'Duskbreaker Lighthouse',
        description: 'Lead technician overseeing the basement synthesis rig. Briefed "Director Faberge" on protocol, chain of custody via Donnathan Reeves, and the synthesis process using living Shadowed subjects.',
        history: [
            { session: 6, note: 'Disclosed basement synthesis details and Reeves hand-off; complied with orders to halt run and move Meri to Med Bay.' }
        ],
        connections: [
            { type: 'location', id: 'duskbreaker-lighthouse', reason: 'Staff lead' },
            { type: 'location', id: 'basement-lab', reason: 'Operates the synthesis rig' },
            { type: 'character', id: 'michelle-faberge', reason: 'Reported to as Director of Research' },
            { type: 'character', id: 'donnathan-reeves', reason: 'Named as liaison delivering subjects per protocol' },
            { type: 'lore', id: 'light-crystals', reason: 'Operates crystal synthesis process' }
        ]
    },
    {
        id: 'empress-consort-lyssandra',
        name: 'Empress Consort Lyssandra',
        role: 'Empress Consort of The Hariolar Empire',
        location: 'Pharus',
        description: 'Grand-niece of Proctor Eduard who married into the imperial family. Met Donnathan Reeves in Pharus.',
        history: [
            { session: 8, note: 'First mentioned as Eduard\'s grand-niece and acquaintance of Reeves' }
        ],
        connections: [
            { type: 'npc', id: 'proctor-eduard', reason: 'Grand-uncle' },
            { type: 'lore', id: 'marchenbau', reason: 'Family origin' },
            { type: 'npc', id: 'donnathan-reeves', reason: 'Met in Pharus' },
            { type: 'location', id: 'pharus', reason: 'Imperial residence' }
        ]
    }
];

export default npcs;

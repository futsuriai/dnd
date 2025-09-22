// NPC data for the world

export const npcs = [
    // Major NPCs (show like CharactersView with portraits/avatars)
    {
        id: 'meri',
        name: 'Meri',
        role: 'Goliath Mentor',
        location: 'Heading to Hyrta',
        description: 'Mentor to Ysidor. Arrested in Bastion City after speaking against the Lighthouse; later found captive beneath the Lighthouse and rescued. Is now heading to her home village with Ysidor\'s sending stone.',
        fullText: 'A towering goliath of granite-gray skin and lilac-silver hair, Meri served as Ysidor\'s mentor, drilling him in blessing and stance with her characteristic phrase: "Hold your guard higher, little hill." After being reported as violent and dangerous following an altercation near the Lighthouse, she was transferred under Proctor Eduard\'s custody and ultimately subjected to horrific basement experiments involving crystal synthesis. She was rescued partway through the process and is now recovering from her ordeal.',
        history: [
            { session: 1, note: 'Established as Ysidor\'s missing mentor.' },
            { session: 2, note: 'Rumored transfer under Proctor Eduard after arrest in Bastion City.' },
            { session: 3, note: 'No sign in the old road.' },
            { session: 6, note: 'Found alive in basement lab; extracted to safety from the lighthouse.' },
            { session: 7, note: 'Rescued and freed; departed for Hyrta' }
        ],
        connections: [
            { type: 'character', id: 'ysidor', reason: 'Mentor and guardian' },
            { type: 'location', id: 'duskbreaker-lighthouse', reason: 'Held captive beneath the Lighthouse' },
            { type: 'location', id: 'hyrta', reason: 'Home village' },
            { type: 'lore', id: 'light-crystals', reason: 'Subject of crystal synthesis process' }
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
        description: 'Ellara\'s mentor at the Seminary. Directly implicated by Meri as a figure she saw after being captured.',
        fullText: 'Proctor Eduard projects calm authority and orthodoxy within the Eulogian Seminary. He warned of Lighthouse hubris and claimed to have set Meri free, directing concerned parties away from further investigation. However, testimony from basement laboratory staff ties Eulogian liaison Donnathan Reeves to systematic deliveries "per protocol"—leaving Eduard\'s direct role unclear. Whether he was deceived, complicit, or actively opposed to the conspiracy remains to be proven.',
        history: [
            { session: 2, note: 'Named on custody transfer ledger for Meri.' },
            { session: 3, note: 'Claimed to have released Meri, directing the party out of the city.' },
            { session: 4, note: 'Expressed shock; promised to escalate investigation.' },
            { session: 6, note: 'Complicity questioned via Reeves hand-offs; stance uncertain.' },
            { session: 7, note: 'Directly implicated by Meri since she was able to describe him after her capture' }
        ],
        connections: [
            { type: 'character', id: 'ellara', reason: 'Mentor at the Seminary' },
            { type: 'location', id: 'eulogian-seminary', reason: 'Post and influence' },
            { type: 'location', id: 'stonewall-tower', reason: 'Named in custody transfer ledger (Session 2)' },
            { type: 'lore', id: 'eulogia-eternal-light', reason: 'Clergy of the faith' }
        ]
    },
    {
        id: 'donnathan-reeves',
        name: 'Donnathan Reeves',
        role: 'Director of Relations, Duskbreaker Lighthouse',
        location: 'Pharus (often traveling)',
        prominence: 'minor',
        description: 'Political liaison between the Lighthouse and Eulogians. Named as the hand-off agent for "subjects".',
        fullText: 'Donnathan Reeves serves as the diplomatic face of the Duskbreaker Lighthouse, frequently traveling to maintain relationships with political authorities, particularly in the capital city of Pharus. Basement laboratory testimony has identified him as the crucial liaison who facilitates the delivery of living "subjects" into Lighthouse custody for crystal synthesis experiments. These transfers are conducted "per protocol," suggesting an established and sanctioned arrangement between the Lighthouse and Eulogian authorities. His role makes him a key political lever and potentially the keystone figure in understanding the full scope of the institutional conspiracy.',
        history: [
            { session: 5, note: 'Identified as Director of Relations, liaising in Pharus.' },
            { session: 6, note: 'Named as hand-off for delivered “subjects” per protocol.' },
            { session: 7, note: 'Introduced to Ellara by Proctor Eduard in the Seminary mess hall.' }
        ],
        connections: [
            { type: 'location', id: 'duskbreaker-lighthouse', reason: 'Executive at the Lighthouse' },
            { type: 'location', id: 'pharus', reason: 'Operating theater in the capital' },
            { type: 'lore', id: 'lightkeepers', reason: 'Operates under/with the council' },
            { type: 'location', id: 'eulogian-seminary', reason: 'Present at Seminary; introduced to Ellara' }
        ]
    },
    {
        id: 'duke-valerian-oleander',
        name: 'Duke Valerian Oleander',
        role: 'Duke of Hieroterra',
        location: 'Bastion City',
        description: 'Provincial ruler of Hieroterra; mentioned as having been warned about the Lighthouse hubris and politics around light crystals.',
        history: [
            { session: 1, note: 'Named as Duke of Hieroterra during city introduction.' },
            { session: 4, note: 'Eduard claims to have warned the duke about Lighthouse hubris.' }
        ],
        connections: [
            { type: 'location', id: 'bastion-city', reason: 'Seat of ducal power' },
            { type: 'location', id: 'hieroterra', reason: 'Province lord' }
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
        description: 'Ellara\'s kindly superior with a fondness for confiscated romance scrolls and gossip.',
        history: [
            { session: 1, note: 'Ellara sought information about Meri; advised she was likely in an eastern prison.' },
            { session: 2, note: 'Provided rumors about Nyx and Meri’s transfer; comic relief via “romance scrolls.”' }
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
        description: 'Lead technician overseeing the basement synthesis rig. Briefed “Director Faberge” on protocol, chain of custody via Donnathan Reeves, and the synthesis process using living Shadowed subjects.',
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
    }
];

export default npcs;

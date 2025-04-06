// Revised history-based data format with connections as history entries

export const historyBasedDataExpanded = {
    sessions: [
        {
            id: 'session-0',
            title: 'Session 0',
            subtitle: 'Character Creation',
            date: '2025-05-04',
            upcoming: true,
            summary: 'Character creation and world introduction. Come prepared with character concepts and backstory ideas based on Session -1!'
        },
        {
            id: 'session-minus-1',
            title: 'Session -1',
            subtitle: 'Initial world building and general framework discussions',
            date: '2025-04-06',
            summary: 'Hopes, dreams and expectations setting. Discussed the world\'s themes, character concepts, and narrative boundaries.',
            highlights: [
                'Established our world as a Steampunk/Gaslamp Fantasy setting where magic and emerging technology exist in societal tension.',
                'Explored the possibility of an overarching church structure reminiscent of Catholicism, influencing the world\'s spiritual and political landscape.',
                'Discussed how our world\'s society is stratified between nobles and commoners, creating opportunities for diverse character backgrounds.',
                'Shared initial character concepts and considered how each might fit into different societal niches.',
                'Had conversations about narrative boundaries and player comfort zones.',
                'Contemplated whether characters will have pre-existing connections when our adventure begins.'
            ]
        }
    ],

    historyEntries: [
        // Characters provided by user, added to Session -1
        { entityId: 'steff', sessionId: 'session-minus-1', changeType: 'creation', timestamp: '2025-04-06T10:00:00Z', editedBy: '12345', data: { entityType: 'character', id: 'steff', name: 'Steff', player: 'Steff', race: 'Sentient Plant', class: 'Ranger/Beastmaster', level: 3, background: 'Forest Offspring', bio: 'An offspring of a mother tree where the whole forest is one sentient plant. Sent out into the world on a mission, carrying a magical item that is a by-product of the mother tree. Travels with a companion animal.' } },
        { entityId: 'avi', sessionId: 'session-minus-1', changeType: 'creation', timestamp: '2025-04-06T10:01:00Z', editedBy: '12345', data: { entityType: 'character', id: 'avi', name: 'Avi', player: 'Avi', race: 'Unknown', class: 'Bard/Warlock', level: 3, background: 'Outsider', bio: 'Lives on the edge of society and prefers to talk his way out of situations. Skilled in illusion magic and has an outsider perspective on societal norms.' } },
        { entityId: 'alex', sessionId: 'session-minus-1', changeType: 'creation', timestamp: '2025-04-06T10:02:00Z', editedBy: '12345', data: { entityType: 'character', id: 'alex', name: 'Alex', player: 'Alex', race: 'Fey', class: 'Gloomstalker Ranger', level: 3, background: 'Eldritch/Ancient', bio: 'Connected to death, decay, and the darker aspects of nature. Lost their prey and purpose and is now adapting to a strange new world. Has an ancient, eldritch background with fey connections.' } },
        { entityId: 'andres', sessionId: 'session-minus-1', changeType: 'creation', timestamp: '2025-04-06T10:03:00Z', editedBy: '12345', data: { entityType: 'character', id: 'andres', name: 'Andres', player: 'Andres', race: 'Kalashtar', class: 'Druid (Cleric presenting)', level: 3, background: 'Cloister Scholar', bio: 'Hosts a spirit that manifests as an existing god, which embedded itself after death. Lives a cloistered life in a monastery/church and received the spirit as a revelation. Mechanically a druid but spiritually a cleric. Unfamiliar with the ordinary world due to cloistered upbringing.' } },
        { entityId: 'marc', sessionId: 'session-minus-1', changeType: 'creation', timestamp: '2025-04-06T10:04:00Z', editedBy: '12345', data: { entityType: 'character', id: 'marc', name: 'Marc', player: 'Marc', race: 'Unknown', class: 'Paladin', level: 3, background: 'Backwoods Hero', bio: 'A \"himbo\" paladin from the backwoods, traveling to the city due to outside forces. Has taken an oath to a local god/spirit. Simple but good-hearted.' } }
    ]
};

export default historyBasedDataExpanded;

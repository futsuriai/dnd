// Character data for the world

// Dynamically import all avatar images. 'eager: true' imports them immediately.
const avatarModules = import.meta.glob('@/assets/avatars/avatar/*', { eager: true, import: 'default' });
// Dynamically import all portrait images.
const portraitModules = import.meta.glob('@/assets/avatars/portrait/*', { eager: true, import: 'default' });

// Helper function to get the correct image URL based on id and type (avatar/portrait)
// It iterates through the modules and finds the key that includes the character id.
function getImageUrl(modules, id, type) {
    for (const path in modules) {
        // Check if the path includes the character id and the correct subdirectory (avatar/portrait)
        if (path.includes(`/${type}/${id}.`)) {
            return modules[path]; // Return the URL (default export)
        }
    }
    console.warn(`Image not found for type: ${type}, id: ${id}`);
    return null; // Return null or a placeholder if not found
}

export const characters = [
  {
    id: 'tsinyra',
    name: 'Tsi\'nyra',
    race: 'Genasi',
    class: 'Ranger/Beastmaster',
    level: 3,
    background: 'Forest Offspring',
    bio: 'Child of the Mother Tree, her purpose is to experience and learn of the world. How much is imparted onto the world is the individual\'s choice, but the sentient Mother Tree encourages her children to learn and grow for the benefit of the whole. Not much is known of this sentient tree and her children by the outside world, but as their presence grows, they\'ve become hard to ignore. Tsi\'nyra, like many of her other siblings, travels with a companion animal and blessings from the Mother Tree herself.',
    dndBeyondLink: 'https://www.dndbeyond.com/characters/145877243',
    // Dynamically get the URL based on the id 'tsinyra'
    avatarUrl: getImageUrl(avatarModules, 'tsinyra', 'avatar'),
    portraitUrl: getImageUrl(portraitModules, 'tsinyra', 'portrait'),
    connections: []
  },
  {
    id: 'berridin',
    name: 'Berridin',
    race: 'Halfling',
    class: 'Bard - College of Mirages',
    level: 3,
    background: 'City Urchin',
    bio: 'Outwardly charming and quick with a smile, he masks a grim past. The sole survivor of a raid on his distant halfling village, he fled to Bastion City at just fourteen. Orphaned and alone, he endured cruelty from strangers and learned early to distrust most non-halflings. In time, he found refuge among Bastion’s halfling enclave and adapted to the city\'s tangled sprawl. Yet beneath his urban polish, a quiet doubt persists—would he fight for Bastion, or flee it like the last place he called home?',
    dndBeyondLink: 'https://www.dndbeyond.com/characters/143977944',
    avatarUrl: getImageUrl(avatarModules, 'berridin', 'avatar'),
    portraitUrl: getImageUrl(portraitModules, 'berridin', 'portrait'),
    connections: []
  },
  {
    id: 'nyx',
    name: 'Nyx',
    race: 'Shadar-kai',
    class: 'Gloomstalker Ranger',
    level: 3,
    background: 'Ancient Fey',
    bio: 'Connected to death and the darker aspects of nature. An ancient hunter who lost his prey and purpose. Spends his time observing this new world develop.  Will he continue to aimlessly flow with the tides of time or will he finally find prey worth hunting?',
    dndBeyondLink: 'https://www.dndbeyond.com/characters/145878200',
    avatarUrl: getImageUrl(avatarModules, 'nyx', 'avatar'),
    portraitUrl: getImageUrl(portraitModules, 'nyx', 'portrait'),
    connections: []
  },
  {
    id: 'ellara',
    name: 'Ellara',
    race: 'Human',
    class: 'Druid',
    level: 3,
    background: 'Euologian Acolyte',
    bio: 'Lived a cloistered life in a priory in the Highlands and moved to Bastion City recently. A true believe in the Eulogia who misses her hometown and her connections there deeply. Not used to dealing with so many people she doesn\'t know but trying to put on a brave face.',
    dndBeyondLink: 'https://www.dndbeyond.com/characters/144318331',
    avatarUrl: getImageUrl(avatarModules, 'ellara', 'avatar'),
    portraitUrl: getImageUrl(portraitModules, 'ellara', 'portrait'),
    connections: []
  },
  {
    id: 'ysidor', 
    name: 'Ysidor',
    race: 'Goliath',
    class: 'Paladin',
    level: 3,
    background: 'Backwoods Hero',
    bio: 'A simple minded paladin from a small backwoods village at the foot of a mountain. He has taken an oath to the local deity of love and fertility, known as Hyr. His mentor and village elder ventured to the city to deal with a mysterious matter but months have passed and Ysidor must now retrace his elder’s steps.',
    dndBeyondLink: 'https://www.dndbeyond.com/characters/145877274',
    avatarUrl: getImageUrl(avatarModules, 'ysidor', 'avatar'),
    portraitUrl: getImageUrl(portraitModules, 'ysidor', 'portrait'),
    connections: []
  },
  {
    id: 'witty',
    name: 'Whitaker "Witty" Whitman VI',
    race: 'Human',
    class: 'Artificer',
    level: 3,
    background: 'Noble',
    bio: 'The sixth and youngest son of Lord Whitaker, Witty is an eccentric noble obsessed with gases, alchemy, and gaining access to the Duskbreaker Lighthouse. He dreams of founding the "Institute of Philosophical Pneumatics" and came to Bastion City to network with nobility and secure an interview with Director Faberge—unaware she is dead. His manservant Jarvis has gone missing along with much of his wardrobe. Inventor of "Success Gas"—a narcotic mixture of snake venom and sphinx anal glands—which he genuinely believes grants intelligence. Purple is his signature color.',
    dndBeyondLink: 'https://www.dndbeyond.com/characters/155766880',
    avatarUrl: getImageUrl(avatarModules, 'witty', 'avatar'),
    portraitUrl: getImageUrl(portraitModules, 'witty', 'portrait'),
    connections: [
      { type: 'location', id: 'lord-whitakers-estate', reason: 'Resides at' },
      { type: 'npc', id: 'donnathan-reeves', reason: 'Family acquaintance from past balls' }
    ]
  }
];

export default characters;
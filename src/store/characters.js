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
    bio: 'An offspring of a mother tree where the whole forest is one sentient plant. Sent out into the world on a mission, carrying a magical item that is a by-product of the mother tree. Travels with a companion animal.',
    dndBeyondLink: 'https://www.dndbeyond.com/characters/145877243',
    // Dynamically get the URL based on the id 'tsinyra'
    avatarUrl: getImageUrl(avatarModules, 'tsinyra', 'avatar'),
    portraitUrl: getImageUrl(portraitModules, 'tsinyra', 'portrait'),
    connections: []
  },
  {
    id: 'diraaz',
    name: 'Diraaz',
    race: 'Halfling',
    class: 'Bard - College of Mirages',
    level: 3,
    background: 'Aladdin street urchin (TBD)',
    bio: 'Lives on the edge of society and prefers to talk his way out of situations. Skilled in illusion magic and has an outsider perspective on societal norms.',
    dndBeyondLink: 'https://www.dndbeyond.com/characters/143977944',
    avatarUrl: getImageUrl(avatarModules, 'diraaz', 'avatar'),
    portraitUrl: getImageUrl(portraitModules, 'diraaz', 'portrait'),
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
  }
];

export default characters;
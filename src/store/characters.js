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
    background: 'Eldritch/Ancient',
    bio: 'Connected to death, decay, and the darker aspects of nature. Lost their prey and purpose and is now adapting to a strange new world. Has an ancient, eldritch background with fey connections.',
    dndBeyondLink: 'https://www.dndbeyond.com/characters/145878200',
    avatarUrl: getImageUrl(avatarModules, 'nyx', 'avatar'),
    portraitUrl: getImageUrl(portraitModules, 'nyx', 'portrait'),
    connections: []
  },
  {
    id: 'ellara',
    name: 'Ellara',
    race: 'Human (mechanically Kalashtar)',
    class: 'Druid (Cleric presenting)',
    level: 3,
    background: 'Cloister Scholar',
    bio: 'Hosts a spirit that manifests as an existing god, which embedded itself after death. Lives a cloistered life in a monastery/church and received the spirit as a revelation. Mechanically a druid but spiritually a cleric. Unfamiliar with the ordinary world due to cloistered upbringing.',
    dndBeyondLink: 'https://www.dndbeyond.com/characters/144318331',
    avatarUrl: getImageUrl(avatarModules, 'ellara', 'avatar'),
    portraitUrl: getImageUrl(portraitModules, 'ellara', 'portrait'),
    connections: []
  },
  {
    // Note: The id here is 'tbd', but the image files are named 'goliath.*'
    // We need to use 'goliath' to find the images.
    // Consider changing the id to 'goliath' for consistency if this character is finalized.
    id: 'tbd', // Or change to 'goliath'
    name: 'TBD',
    race: 'Goliath',
    class: 'Paladin',
    level: 3,
    background: 'Backwoods Hero',
    bio: 'A "himbo" paladin from the backwoods, traveling to the city due to outside forces. Has taken an oath to a local god/spirit. Simple but good-hearted.',
    dndBeyondLink: 'https://www.dndbeyond.com/characters/145877274',
    // Use 'goliath' to match the filenames
    avatarUrl: getImageUrl(avatarModules, 'goliath', 'avatar'),
    portraitUrl: getImageUrl(portraitModules, 'goliath', 'portrait'),
    connections: []
  }
];

export default characters;
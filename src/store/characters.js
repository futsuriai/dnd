// Character data for the world

export const characters = [
  {
    id: 'steff',
    name: 'Steff',
    player: 'Steff',
    race: 'Sentient Plant',
    class: 'Ranger/Beastmaster',
    level: 3,
    background: 'Forest Offspring',
    bio: 'An offspring of a mother tree where the whole forest is one sentient plant. Sent out into the world on a mission, carrying a magical item that is a by-product of the mother tree. Travels with a companion animal.',
    dndBeyondLink: '',
    connections: [
      {
        type: 'location',
        id: 'mother-forest',
        reason: 'Origin point where the entire forest is one connected sentient plant.'
      }
    ]
  },
  {
    id: 'avi',
    name: 'Avi',
    player: 'Avi',
    race: 'Unknown',
    class: 'Bard/Warlock',
    level: 3,
    background: 'Outsider',
    bio: 'Lives on the edge of society and prefers to talk his way out of situations. Skilled in illusion magic and has an outsider perspective on societal norms.',
    dndBeyondLink: '',
    connections: []
  },
  {
    id: 'alex',
    name: 'Alex',
    player: 'Alex',
    race: 'Eladrin Elf or Aasimar (Eldritch/Nyarlathotep)',
    class: 'Gloomstalker Ranger',
    level: 3,
    background: 'Eldritch/Ancient',
    bio: 'Connected to death, decay, and the darker aspects of nature. Lost their prey and purpose and is now adapting to a strange new world. Has an ancient, eldritch background with fey connections.',
    dndBeyondLink: '',
    connections: []
  },
  {
    id: 'andres',
    name: 'Andres',
    player: 'Andres',
    race: 'Kalashtar',
    class: 'Druid (Cleric presenting)',
    level: 3,
    background: 'Cloister Scholar',
    bio: 'Hosts a spirit that manifests as an existing god, which embedded itself after death. Lives a cloistered life in a monastery/church and received the spirit as a revelation. Mechanically a druid but spiritually a cleric. Unfamiliar with the ordinary world due to cloistered upbringing.',
    // dndBeyondLink: 'https://www.dndbeyond.com/species/260720-kalashtar',
    connections: []
  },
  {
    id: 'marc',
    name: 'Marc',
    player: 'Marc',
    race: 'Unknown',
    class: 'Paladin',
    level: 3,
    background: 'Backwoods Hero',
    bio: 'A "himbo" paladin from the backwoods, traveling to the city due to outside forces. Has taken an oath to a local god/spirit. Simple but good-hearted.',
    dndBeyondLink: '',
    connections: []
  }
];

export default characters;
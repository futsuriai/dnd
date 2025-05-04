// Character data for the world
import tsinyraAvatar from '@/assets/avatars/tsinyra_avatar.jpeg';
import tsinyraPortrait from '@/assets/avatars/tsinyra_portrait.jpeg';
import diraazAvatar from '@/assets/avatars/diraaz_avatar.png';
import diraazPortrait from '@/assets/avatars/diraaz_portrait.jpeg';
import nyxAvatar from '@/assets/avatars/nyx_avatar.png'; // Assuming exists, placeholder if not
import nyxPortrait from '@/assets/avatars/nyx_portrait.png'; // Assuming exists, placeholder if not
import ellaraAvatar from '@/assets/avatars/ellara_avatar.png';
import ellaraPortrait from '@/assets/avatars/ellara_portrait.png';
import goliathAvatar from '@/assets/avatars/goliath_avatar.png'; // Assuming exists, placeholder if not
import goliathPortrait from '@/assets/avatars/goliath_portrait.png'; // Assuming exists, placeholder if not

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
    avatarUrl: tsinyraAvatar, // Use imported variable
    portraitUrl: tsinyraPortrait, // Use imported variable
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
    avatarUrl: diraazAvatar, // Use imported variable
    portraitUrl: diraazPortrait, // Use imported variable
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
    avatarUrl: nyxAvatar, // Use imported variable
    portraitUrl: nyxPortrait, // Use imported variable
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
    avatarUrl: ellaraAvatar, // Use imported variable
    portraitUrl: ellaraPortrait, // Use imported variable
    connections: []
  },
  {
    id: 'tbd',
    name: 'TBD',
    race: 'Goliath',
    class: 'Paladin',
    level: 3,
    background: 'Backwoods Hero',
    bio: 'A "himbo" paladin from the backwoods, traveling to the city due to outside forces. Has taken an oath to a local god/spirit. Simple but good-hearted.',
    dndBeyondLink: 'https://www.dndbeyond.com/characters/145877274',
    avatarUrl: goliathAvatar, // Use imported variable
    portraitUrl: goliathPortrait, // Use imported variable
    connections: []
  }
];

export default characters;
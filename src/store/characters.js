// Character data for the world
import { getCharacterAvatar, getCharacterPortrait } from '../utils/avatars.js';

export const characters = [
  {
    id: 'berridin',
    name: 'Berridin',
    race: 'Halfling',
    class: 'Bard - College of Mirages',
    level: 5,
    background: 'City Urchin',
    bio: 'Outwardly charming and quick with a smile, he masks a grim past. The sole survivor of a raid on his distant halfling village, he fled to Bastion City at just fourteen. Orphaned and alone, he endured cruelty from strangers and learned early to distrust most non-halflings. In time, he found refuge among Bastion’s halfling enclave and adapted to the city\'s tangled sprawl. Yet beneath his urban polish, a quiet doubt persists—would he fight for Bastion, or flee it like the last place he called home?',
    dndBeyondLink: 'https://www.dndbeyond.com/characters/143977944',
    avatarUrl: getCharacterAvatar('berridin'),
    portraitUrl: getCharacterPortrait('berridin'),
    connections: [
      { type: 'location', id: 'bastion-city', reason: 'Home city since age fourteen' },
      { type: 'location', id: 'halfling-quarter', reason: 'Found refuge among Bastion’s halfling enclave' }
    ]
  },
  {
    id: 'nyx',
    name: 'Nyx',
    race: 'Shadar-kai',
    class: 'Gloomstalker Ranger',
    level: 5,
    background: 'Ancient Fey',
    bio: 'Connected to death and the darker aspects of nature. An ancient hunter who lost his prey and purpose. Spends his time observing this new world develop.  Will he continue to aimlessly flow with the tides of time or will he finally find prey worth hunting?',
    dndBeyondLink: 'https://www.dndbeyond.com/characters/145878200',
    avatarUrl: getCharacterAvatar('nyx'),
    portraitUrl: getCharacterPortrait('nyx'),
    connections: [
      { type: 'location', id: 'nyxs-townhouse', reason: 'Residence in East Bastion' }
    ]
  },
  {
    id: 'ellara',
    name: 'Ellara',
    race: 'Human',
    class: 'Druid',
    level: 5,
    background: 'Euologian Acolyte',
    bio: 'Lived a cloistered life in a priory in the Highlands and moved to Bastion City recently. A true believe in the Eulogia who misses her hometown and her connections there deeply. Not used to dealing with so many people she doesn\'t know but trying to put on a brave face.',
    dndBeyondLink: 'https://www.dndbeyond.com/characters/144318331',
    avatarUrl: getCharacterAvatar('ellara'),
    portraitUrl: getCharacterPortrait('ellara'),
    connections: [
      { type: 'location', id: 'eulogian-seminary', reason: 'Acolyte in training' }
    ]
  },
  {
    id: 'ysidor',
    name: 'Ysidor',
    race: 'Goliath',
    class: 'Paladin',
    level: 5,
    background: 'Backwoods Hero',
    bio: 'A simple minded paladin from a small backwoods village at the foot of a mountain. He has taken an oath to the local deity of love and fertility, known as Hyr. His mentor and village elder ventured to the city to deal with a mysterious matter but months have passed and Ysidor must now retrace his elder’s steps.',
    dndBeyondLink: 'https://www.dndbeyond.com/characters/145877274',
    avatarUrl: getCharacterAvatar('ysidor'),
    portraitUrl: getCharacterPortrait('ysidor'),
    connections: [
      { type: 'location', id: 'hyrta', reason: 'Home village' }
    ]
  },
  {
    id: 'witty',
    name: 'Whitaker "Witty" Whitman VI',
    race: 'Human',
    class: 'Artificer',
    level: 5,
    background: 'Noble',
    bio: 'The sixth and youngest son of Lord Whitaker, Witty is an eccentric noble obsessed with gases, alchemy, and gaining access to the Duskbreaker Lighthouse. He dreams of founding the "Institute of Philosophical Pneumatics" and came to Bastion City to network with nobility and secure an interview with Director Faberge—unaware she is dead. His manservant Jarvis has gone missing along with much of his wardrobe. Inventor of "Success Gas"—a narcotic mixture of snake venom and sphinx anal glands—which he genuinely believes grants intelligence. Purple is his signature color.',
    dndBeyondLink: 'https://www.dndbeyond.com/characters/155766880',
    avatarUrl: getCharacterAvatar('witty'),
    portraitUrl: getCharacterPortrait('witty'),
    connections: [
      { type: 'location', id: 'lord-whitakers-estate', reason: 'Resides at' },
      { type: 'npc', id: 'donnathan-reeves', reason: 'Family acquaintance from past balls' }
    ]
  }
];

export default characters;

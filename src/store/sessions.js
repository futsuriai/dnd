// Session data for the world

export const sessions = [
  {
    id: 'session-1',
    title: 'Session 1',
    subtitle: 'The Adventure Begins', // Placeholder subtitle
    date: 'May 18, 2025', // Two weeks after Session 0
    upcoming: true,
    description: 'The first official session of the campaign.' // Placeholder description
  },
  {
    id: 'session-0',
    title: 'Session 0',
    subtitle: 'Character Creation',
    date: 'May 4, 2025',
    upcoming: false,
    description: 'Character creation and world introduction. Come prepared with character concepts and backstory ideas based on Session -1!',
    highlights: [
      'Provided an overview of the world setting.',
      'Discussed the history of Eulogia.',
      'Gave a brief overview of key locations.',
      'Discussed differences between D&D 5e 2014 and 2024 rulesets for character creation.',
      'Compared Point Buy and Standard Array methods for ability scores and decided to use the Point Buy method for ability scores.',
      'Discussed and selected Origin feats for characters.',
      'Explored options for homebrew classes.',
      'Discussed incorporating appropriate jobs/classes fitting the setting.',
      'Set up level 3 characters.'
    ]
  },
  {
    id: 'session-minus-1',
    title: 'Session -1',
    subtitle: 'Initial world building and general framework discussions',
    date: 'April 6, 2025',
    description: 'Hopes, dreams and expectations setting. Discussed the world\'s themes, character concepts, and narrative boundaries.',
    highlights: [
      'Established our world as a Steampunk/Gaslamp Fantasy setting where magic and emerging technology exist in societal tension.',
      'Explored the possibility of an overarching church structure reminiscent of Catholicism, influencing the world\'s spiritual and political landscape.',
      'Discussed how our world\'s society is stratified between nobles and commoners, creating opportunities for diverse character backgrounds.',
      'Shared initial character concepts and considered how each might fit into different societal niches.',
      'Had conversations about narrative boundaries and player comfort zones.',
      'Contemplated whether characters will have pre-existing connections when our adventure begins.'
    ]
  }
];

export default sessions;
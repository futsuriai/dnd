// Session data for the world

export const sessions = [
  {
    id: 'session-2',
    title: 'Session 2',
    subtitle: 'Following the Threads',
    date: 'June 1, 2025',
    upcoming: true,
    description: 'The party continues their investigation into the mysterious disappearances in Bastion City, with focus on the imprisoned goliath and the strange circumstances surrounding the case. As they delve deeper into the city\'s shadows, they\'ll encounter both allies and obstacles in their quest for answers.',
    summaryFile: 'session-2.md'
  },
  {
    id: 'session-1',
    title: 'Session 1',
    subtitle: 'The Adventure Begins',
    date: 'May 18, 2025',
    upcoming: false,
    description: 'Set in the year 651 AE (After Eulogia) in Bastion City, the capital of Hieroterra Province. The party begins their journey in this divided city where the East and West sides represent stark contrasts in wealth and influence. Mysterious disappearances, including that of a powerful goliath, set the stage for the campaign\'s first major storyline.',
    summaryFile: 'session-1.md',
    highlights: [
      'Introduced Bastion City and the political landscape of Hieroterra Province under Duke Valerian Oleander.',
      'Established the East-West divide of the city, with the West being affluent and the East more modest, featuring the Duskbreaker Lighthouse.',
      'Berridin and Ysidor visited the Halfling Quarter, where Berridin showed his connection to the community.',
      'Ellara learned from the Denmother about a missing goliath who was likely imprisoned.',
      'Nyx gathered vital intelligence about missing people and a particularly powerful goliath who was moved from an eastern prison to a western one.',
      'Discovered that the missing goliath had reportedly defeated numerous attackers before being imprisoned.',
      'Observed the mysterious reaction of a guard who became ill when discussing the goliath\'s transfer.'
    ]
  },
  {
    id: 'session-0',
    title: 'Session 0',
    subtitle: 'Character Creation',
    date: 'May 4, 2025',
    upcoming: false,
    description: 'Character creation and world introduction. Come prepared with character concepts and backstory ideas based on Session -1!',
    summaryFile: 'session-0.md',
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
    summaryFile: 'session-minus-1.md',
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
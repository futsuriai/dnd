// Session data for the world

export const sessions = [
  {
    id: 'session-3',
    title: 'Session 3',
    subtitle: 'Confronting the Proctor',
    date: 'June 22, 2025',
    time: '1:00 PM', // Added time
    location: 'Bastion City', // Added location
    upcoming: true,
    description: 'Following the shocking revelation about Proctor Eduard, the party must decide their next move to save Marie. Their investigation will take them deeper into the heart of Bastion City\'s mysteries, testing their resolve and alliances.',
  },
  {
    id: 'session-2',
    title: 'Session 2',
    subtitle: 'Dreams in the Shadow of the Light',
    date: 'Jun 08, 2025',
    upcoming: false,
    description: 'The session begins with the PCs experiencing vivid dreams. Morning activities lead to new information for Ellara about Nyx and Marie. The party then ventures into West Bastion, investigating two prisons to find Ysidor\'s mentor, Marie. They discover that Marie was transferred under the personal custody of Proctor Eduard, deepening the mystery.',
    summaryFile: 'session-2.md',
    highlights: [
      'Each character experiences vivid, revealing, or unsettling dreams, including Ysidor\'s memory of Marie and Ellara hearing foreign words of Eulogia.',
      'Tsi\'Nyra joyfully discovers "breakfast!" at Nyx\'s townhouse, experimenting with various food combinations.',
      'At the Eulogian Seminary, Ellara learns from the Denmother that Nyx is known as a "fixer" and that Marie was moved to a "western" prison.',
      'Proctor Eduard expresses disdain for goliaths, to which Ellara offers a diplomatic rebuttal.',
      'Berridin disguises Ysidor as a tall human named "Moose" for their trip to West Bastion.',
      'The party, including a wide-eyed Tsi\'Nyra and "Moose," gets their first look at the opulent West Bastion.',
      'After a failed bribery attempt at the first prison, Nyx successfully bribes a guard at Stonewall Tower for information.',
      'Berridin cleverly uses Invisibility to slip past guards and discover a ledger entry: "Custody Transfer—His Holy Eminence Proctor Eduard."',
      'A tense confrontation with a Stonewall Tower guard, who warns Ellara about "people much higher" pulling strings, hints at deeper mysteries.',
      'The party confirms Marie was transferred under the personal custody of Proctor Eduard, directly implicating him leaving Ellaria stunned.',
    ],
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
      'Tsi\'Nyra arrived at Nyx\'s at her mother\'s request searching for her missing sisters.',
      'Ellara encountered Berridin and later Ysidor during Alm\'s Giving in the Eastern City.',
      'After a commotion when Tsi\'Nyra and Nyx arrived Ellara took the group aside.',
      'Ellara felt like this connection was meant to be and she was supposed to help desipte the Shadowed in the group',
      'Ysidor asked about his mentor, Meri, who was missing. Ellara mentioned she was likely imprisoned after an incident where she took down 20 guards and shouted about the Lighthouse.',
      'Berridin and Ysidor visited the Halfling Quarter, where Berridin showed his connection to the community. The Candy Incident of 650 AE was mentioned.',
      'Ellara asked her the Denmother about Meri who was likely imprisoned.',
      'Nyx gathered intelligence at a seedy bar from a guard about Meri and learned she was moved from the Eastern prison to one in the West.',
      'The party agreed to meet in 2 days to discuss their next steps.',
    ]
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
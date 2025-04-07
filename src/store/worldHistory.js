// Revised World History Data: Balanced Edition

export const worldHistory = {
  eras: [
    {
      id: 'era-of-wild-magic',
      name: 'Era of Wild Magic',
      period: 'Before the Long Eclipse',
      description: [
        'Before historical records became clouded, the world thrived with varied cultures steeped in powerful and unpredictable magic. Communities ranged from shamanic tribes and arcane conclaves to city-states aligned with elemental beings or Fey courts.',
        'Spirits and mythical beings interacted freely with mortals, forging pacts and influencing civilizations. Power dynamics shifted rapidly, with kingdoms rising and falling based on their mastery or favor of arcane energies.',
        'While danger was constant—magical beasts roamed untamed and rituals could spiral disastrously out of control—many ancient sites still bear testament to the era\'s creativity and diversity.'
      ],
      events: [
        { year: 'Unknown', description: 'Formation of alliances between Fey Courts and mortal kingdoms.' },
        { year: 'Unknown', description: 'Construction of mystical sites, such as the famed Spirit Stones.' },
        { year: 'Unknown', description: 'Localized cults flourish around minor deities and natural forces.' }
      ]
    },
    {
      id: 'the-long-eclipse',
      name: 'The Long Eclipse',
      period: 'The Shrouded Age (Centuries preceding 1 AE)',
      description: [
        'A mysterious event plunged the world into prolonged darkness, disrupting natural and magical orders alike. Fey beings retreated or turned hostile; divine presences vanished or grew silent. Societies collapsed, isolated in fear as knowledge faded.',
        'With darkness came corruption, monsters emerged from shadows, and survivors struggled for generations amid dwindling hope and resources. Stories vary about the cause—cosmic event, magical cataclysm, or divine punishment—but all agree it reshaped civilization.',
        'Small, fortified communities endured by banding together under warlords or wise leaders, fostering new traditions and alliances.'
      ],
      events: [
        { year: 'Unknown', description: 'Fey Courts withdraw support, leading to societal collapse.' },
        { year: 'Unknown', description: 'Emergence of shadow creatures and corrupted wildlife.' },
        { year: 'Unknown', description: 'Disruption of magical ley lines causes widespread instability.' }
      ]
    },
    {
      id: 'the-dawn-of-light',
      name: 'The Dawn of Light',
      period: 'Approx. 1 AE - 200 AE',
      description: [
        'In a world fractured by despair, new forces rose promising unity and renewal. Most famously, the faith of Eulogia began spreading, sparked by a mysterious Guiding Being who sacrificed and was reborn, drawing followers seeking hope amidst darkness.',
        'Yet faith was not the only unifying force: elsewhere, powerful leaders established alliances and foundations for what would become the Empire, driven equally by pragmatic necessity as spiritual belief. The province known today as the Hieroterra Province, paradoxically, remained largely independent, resistant to centralized authority and fiercely protective of its older traditions and knowledge.',
        'This period saw communities across the lands rediscovering hope, knowledge, and order, whether driven by religious fervor or practical governance.'
      ],
      events: [
        { year: '~1 AE', description: 'The Guiding Being leads followers from the Hieroterra Province on the Great Pilgrimage.' },
        { year: '~50 AE', description: 'Formation of the early Imperial Concordat, gradually consolidating scattered communities into a broader political entity.' },
        { year: '~120 AE', description: 'Eulogia solidifies doctrines, coexisting uneasily with older faiths and traditions.' },
        { year: '~180 AE', description: 'Establishment of the new Imperial Capital far from the Hieroterra Province, solidifying political authority distinct from religious centers.' }
      ]
    },
    {
      id: 'the-imperial-age',
      name: 'The Imperial Age',
      period: 'Approx. 200 AE - 500 AE',
      description: [
        'This era marked the height of Imperial power, blending governance, religion, commerce, and emerging technologies. The Empire grew into a structured bureaucracy, integrating distant provinces while fostering trade and infrastructure improvements.',
        'Though the Eulogia church played a significant role in education and social norms, its influence varied considerably. Local regions often retained older traditions, folk magics, and independent governance, leading to intermittent conflicts and negotiations rather than absolute domination.',
        'Technological advances such as early mechanics and steam experimentation began reshaping societies, sparking both excitement and controversy. Guilds, academies, and individual inventors rose alongside clergy and nobility as influential voices.'
      ],
      events: [
        { year: '~250 AE', description: 'Imperial Law codified, incorporating both secular governance and limited religious principles.' },
        { year: '~310 AE', description: 'The Schism of the Whispering Woods; major conflicts erupt with Fey-aligned territories resisting Imperial assimilation.' },
        { year: '~380 AE', description: 'Establishment of Imperial Academies for technological and scientific advancement.' },
        { year: '~450 AE', description: 'Sanctioned use of mechanical "Orderly Machines" gains official recognition.' }
      ]
    },
    {
      id: 'age-of-steel-and-light',
      name: 'Age of Steel and Light',
      period: 'Approx. 500 AE - Present (~603 AE)',
      description: [
        'Rapid technological advancements now define this age, profoundly affecting society, trade, and international relationships. Steam-powered vehicles, elaborate automata, and aether-based innovations have begun reshaping the Imperial core and its periphery.',
        'The Empire, balancing traditional governance with rising guilds and technological societies, faces internal tensions. While the Eulogia religion cautiously endorses technology as symbolic of rational enlightenment, debates flourish over what constitutes appropriate innovation.',
        'Not all provinces embrace these changes equally. Regions such as the Hieroterra Province remain culturally distinct, retaining stronger links to ancient practices, Fey influences, and localized governance. Imperial pressure grows alongside grassroots resistance movements advocating local autonomy and traditional magics.',
        'Strange celestial and Fey-related phenomena have increased in recent decades, causing unease across scholarly and religious institutions alike.'
      ],
      events: [
        { year: '~530 AE', description: 'Expansion of the Imperial Steam Carriage network accelerates commerce and migration.' },
        { year: '~565 AE', description: 'Deployment of technological infrastructures like communication towers and automated street lighting across Imperial territories.' },
        { year: '~580 AE', description: 'Increased reports of unusual Fey activity and unexplained celestial phenomena prompt scholarly investigations.' },
        { year: '~590 AE', description: 'Rise of Technologist Guilds challenges old power structures, advocating innovation and commercial liberalization.' },
        { year: '~598 AE', description: 'A wave of unexplained supernatural occurrences reignites religious fervor and academic curiosity, increasing tension between traditionalists and progressives.' },
        { year: '~603 AE', description: 'Present day: Intensified Imperial presence in Hieroterra Province sparks resistance movements, coinciding with rumors of resurgent magical phenomena and ancient Fey awakenings.' }
      ]
    }
  ]
};

export default worldHistory;

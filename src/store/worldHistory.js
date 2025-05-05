// Revised World History Data: Balanced Edition

export const worldHistory = {
  eras: [
    {
      name: "The Age of Shadow",
      period: "Before 0 AE",
      description: [
        "A dark era dominated by the mysterious Shadowed Monarch and their forces. Little concrete information exists from this time, as most records were destroyed in subsequent conflicts and much knowledge was deliberately suppressed by later regimes.",
        "Archaeological evidence suggests advanced civilizations existed during this time, particularly based on the artifacts and light crystal technology discovered in ruins from this period. The full extent of the Shadowed society remains a topic of vigorous academic debate."
      ],
      events: [
        { year: "c. -300 AE", description: "Height of the Shadowed Monarch's reign according to fragmentary records preserved in protected sites across Hieroterra." },
        { year: "c. -100 AE", description: "Increasing unrest and resistance across Hieroterra against the Shadowed Monarch's rule." },
        { year: "-30 AE", description: "Birth of Nites in a small village in Hieroterra." },
        { year: "-3 AE", description: "Beginning of the Pilgrimage of the Enlightened, led by Nites from Hieroterra to Ordonne." }
      ]
    },
    {
      name: "The Age of Enlightenment",
      period: "0 AE - 250 AE",
      description: [
        "This era began with the sacrifice of Nites and her subsequent ascension as The Eternal Light. Her final words cursed those who did not join her against the Shadowed Monarch, giving birth to the distinction between the Enlightened and the Shadowed.",
        "The First Emperor, who witnessed Nites's sacrifice, founded the city of Pharus and initiated the expansion of what would eventually become The Hariolar Empire. This period was marked by rapid expansion, the establishment of the Eulogia of the Eternal Light as the dominant religion, and the systematic suppression or conversion of Shadowed communities."
      ],
      events: [
        { year: "0 AE", description: "Sacrifice and ascension of Nites, becoming The Eternal Light. The curse of the Shadowed is pronounced." },
        { year: "1 AE", description: "Foundation of Pharus by the First Emperor, establishing the first temple to the Eternal Light." },
        { year: "10 AE", description: "Formation of the Eulogia of the Eternal Light as an organized religious institution." },
        { year: "42 AE", description: "Campaigns against remaining Shadowed strongholds begin across Hieroterra." },
        { year: "87 AE", description: "Completion of the Grand Cathedral in Pharus, becoming the central religious authority in the growing empire." },
        { year: "124 AE", description: "Formal establishment of The Hariolar Empire following the unification of territories across Hieroterra and beyond." },
        { year: "189 AE", description: "Codification of the Imperial Edicts and religious doctrine of the Eulogia." },
        { year: "230 AE", description: "The last known organized resistance of the Shadowed is defeated in the northern mountains." }
      ]
    },
    {
      name: "The Imperial Golden Age",
      period: "250 AE - 500 AE",
      description: [
        "Following the consolidation of power and the subjugation of the last major Shadowed strongholds, The Hariolar Empire entered a period of relative peace and prosperity.",
        "This era saw significant advancements in infrastructure, arts, philosophy, and magical studies (within the constraints of Eulogia doctrine). Imperial roads connected distant provinces, and trade flourished. Grand cities with magnificent architecture devoted to The Eternal Light were constructed, many of which still stand as centers of power today."
      ],
      events: [
        { year: "268 AE", description: "Construction of the Imperial Road network begins, eventually connecting all major cities of the empire." },
        { year: "302 AE", description: "Foundation of the first Imperial Academy in Pharus for the study of approved magics and philosophy." },
        { year: "350 AE", description: "Height of the Classical Imperial architectural style, with iconic structures built across major cities." },
        { year: "398 AE", description: "The Great Codex of the Eternal Light is compiled, standardizing religious practices throughout the empire." },
        { year: "423 AE", description: "Beginning of imperial expansion beyond traditional boundaries, incorporating new cultures into the empire." },
        { year: "467 AE", description: "First recorded theological disputes within the Eulogia regarding interpretation of the Eternal Light's teachings." },
        { year: "489 AE", description: "Signs of political fracturing as provincial governors gain more autonomy in distant regions." }
      ]
    },
    {
      name: "The Age of Division",
      period: "500 AE - 600 AE",
      description: [
        "The imperial central authority gradually weakened due to a combination of overextension, corrupt administration, and theological disputes. Several provinces declared independence or fell under the control of local rulers who maintained only nominal allegiance to the Emperor.",
        "Despite this political fragmentation, the Eulogia maintained its influence across all territories, though regional variations in religious practice developed. This period is characterized by smaller conflicts between breakaway regions and attempts by various emperors to reassert control."
      ],
      events: [
        { year: "512 AE", description: "Eastern provinces declare autonomy while maintaining religious ties to the Eulogia." },
        { year: "527 AE", description: "The Three Emperors Crisis: multiple claimants to the imperial throne lead to a brief civil war." },
        { year: "531 AE", description: "Restoration of central authority under Emperor Lucian III, beginning efforts to reunify the empire." },
        { year: "548 AE", description: "Reform of the Imperial bureaucracy to address corruption and increase loyalty to the center." },
        { year: "567 AE", description: "The Concordat of Faith: agreement between the Emperor and the Eulogia High Clerist defining their respective powers." },
        { year: "589 AE", description: "Reconquest of most breakaway provinces completed, though with greater autonomy granted to local authorities." }
      ]
    },
    {
      name: "The Modern Imperial Era",
      period: "600 AE - Present (651 AE)",
      description: [
        "Following the reunification, the empire entered a new phase characterized by a more federalized governance structure, with stronger provincial autonomy balanced by renewed imperial institutions. The current period has seen remarkable technological advancement, particularly in the last decade with the discovery and development of light crystal technology.",
        "The rediscovery of artifacts from the Age of Shadow, particularly light crystals, has sparked a technological revolution while also raising uncomfortable questions about the supposedly primitive nature of Shadowed civilization. This has led to theological and political tensions, though pragmatic interests in the benefits of these technologies have generally prevailed."
      ],
      events: [
        { year: "607 AE", description: "Foundation of Bastion City as a new administrative center for the northwestern territories." },
        { year: "622 AE", description: "The Great Reform: restructuring of imperial governance to balance central authority with provincial needs." },
        { year: "635 AE", description: "First discovery of light crystals in Shadowed ruins, initially kept secret by imperial researchers." },
        { year: "638 AE", description: "Public announcement of light crystal technology, causing initial religious controversy." },
        { year: "639 AE", description: "Circulation of anonymous pamphlets arguing that light crystals represent the Shadowed's repentance, giving theological justification for their use." },
        { year: "640 AE", description: "The Eulogia officially endorses limited research into light crystals under strict oversight." },
        { year: "643 AE", description: "Discovery of light crystals and Standing Stones in the Sunstone Quarry, suggesting a deeper connection to the Shadowed past." },
        { year: "645 AE", description: "First public implementation of light crystal technology in Bastion City streetlamps." },
        { year: "648 AE", description: "Establishment of the Duskbreaker Lighthouse in Bastion City as the headquarters for light crystal research." },
        { year: "651 AE", description: "Present day: Rapid expansion of light crystal technology throughout the empire, beginning to transform society and industry." }
      ]
    }
  ]
};

export default worldHistory;

// World History Data: Based on DM's Timeline

export const worldHistory = {
  currentYear: 651, // Current year is 651 AE (After Eulogia)
  calendarInfo: "AE (After Eulogia) is the official calendar of The Hariolar Empire and the Eulogia of the Eternal Light. BE (Before Eulogia) marks the period prior to the founding of the Eulogia of the Eternal Light.",
  eras: [
    {
      name: "The Age of Shadow",
      period: "Unknown - 10 BE",
      description: [
        "This is the official name for the time period prior to The Great Cataclysm. Most of the evidence of this time lies in ruins found across the continent. These ruins are often attributed to the Shadowed, this is an anachronistic term since \"Shadowed\" was only coined in 0 AE.",
        "Modern archaeologists and researchers will often use \"precursor people\" but this is only found in academic writings and has not swayed public usage of \"Shadowed ruins\"."
      ],
      events: []
    },
    {
      name: "The Great Cataclysm",
      period: "10 BE - 0 AE",
      description: [
        "This marks a period of great upheaval.",
        "Official Eulogia records note that in 10BE, we saw the rise of the Shadowed Monarch. Modern theology indicates that due to resentment, a conspiracy to rule over the other humanoids began, headed by the Shadowed Monarch. Using profane magic, they ascended to a false godhood, blotting the sky with clouds, spreading natural disasters, and chaos across the land.",
        "Sometime in late 4 BE to early 3 BE, Nites arose against the Shadowed Monarch. Despite years of battle, there was no victory in sight, so she began The Pilgrimage of the Enlightened, taking all those who opposed the Shadowed Monarch to seek new lands and forsaking their birthland. Those who did not join Nites and refused to give shelter to them and their followers would be remembered as the Shadowed.",
        "In 1 BE, after a 3 year trek, the Shadowed Monarch and their armies finally caught up to Nites. In a desperate bid, Nites channeled all her power into her body, causing her to burn brightly. Night turned to day. The clouds burned away revealing the true sky for the first time in a decade. Then there was silence and darkness. A moonless night, with only stars to witness as the Shadowed Monarch and their armies were no more.",
        "The dying Nites spoke these last words: \"May your hearth bear not warmth, your labour no fruits. In history's Light, may your names be ever Shadowed.\"",
        "These words have been memorialized as The Curse of the Shadowed."
      ],
      events: [
        { year: "1 BE", description: "The Shadowed Monarch caught up to Nites, who sacrificed herself to defeat them." },
        { year: "4-3 BE", description: "Nites arose against the Shadowed Monarch and began The Pilgrimage of the Enlightened." },
        { year: "10 BE", description: "Rise of the Shadowed Monarch, who ascended to a false godhood using profane magic." },
      ]
    },
    {
      name: "Ascendance of Nites",
      period: "0 AE",
      description: [
        "Those who followed Nites, now known as the Enlightened Peoples mourned her passing for 4 days. Dawn of the 5th day, instead of the sun, rose a blinding light: The Eternal Light. The Divine Light spoke to those present, declaring she is Nites reborn. Through her sacrifice and death of The Shadowed Monarch, she took upon the divine mantle to protect their people.",
        "This day is marked as the first day of the Eulogian Calendar, 0 AE."
      ],
      events: [
        { year: "0 AE", description: "The Divine Light rose and spoke to those present, declaring she is Nites reborn." }
      ]
    },
    {
      name: "Birth of the Hariolar Empire",
      period: "0 AE - 651 AE (Current Year)",
      description: [
        "The First Emperor, who was among those closest to Nites, built Pharus at the site of her sacrifice."
      ],
      events: [
        { year: "Early in era", description: "The First Emperor built Pharus at the site of Nites's sacrifice." }
      ]
    }
  ]
};

export default worldHistory;

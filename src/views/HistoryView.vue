<template>
    <div class="content-section">
      <h1>World History & Lore</h1>
      <p class="section-intro">The forgotten past and present of the world.</p>
  
      <div class="timeline">
        <div class="era" v-for="(era, index) in eras" :key="index">
          <div class="era-header">
            <h2>{{ era.name }}</h2>
            <span class="era-year">{{ era.period }}</span>
          </div>
          
          <div class="era-content">
            <p v-for="(paragraph, pIndex) in era.description" :key="pIndex">
              {{ paragraph }}
            </p>
            
            <div class="key-events" v-if="era.events && era.events.length">
              <h3>Key Events</h3>
              <ul>
                <li v-for="(event, eIndex) in era.events" :key="eIndex">
                  <span class="event-year">{{ event.year }}:</span> 
                  {{ event.description }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'HistoryView',
    data() {
      return {
        eras: [
          {
            name: 'The Age of Wonders',
            period: 'The Ancient Time',
            description: [
              'Before the Sundering, legends tell of an age when mortals wielded power rivaling the gods. The Ancients commanded the elements, spoke across vast distances without messengers, and traveled among the stars in great sky vessels.',
              'The Luminous Concord, as ancient texts name them, crafted marvels beyond understanding. They built thinking servants of metal and light, created materials that changed shape at a whisper, and wove the Ethereal Lattice—a great invisible web that connected all things.',
              'The Enlightened Ones, those granted sublime wisdom, shaped the very foundations of reality. They crafted the Eternal Engines whose remnants still hum beneath forgotten cities, and the Celestial Lenses that could bend the fabric of creation itself.'
            ],
            events: [
              { year: 'Unknown', description: 'The Luminous Concord unites the world under the Doctrine of Boundless Progress.' },
              { year: 'Unknown', description: 'Completion of the Ethereal Lattice, binding all creation in harmony.' },
              { year: 'Unknown', description: 'The Grand Ascension Project begins, seeking to transcend mortal limitations.' }
            ]
          },
          {
            name: 'The Sundering',
            period: 'The Breaking of the World',
            description: [
              'Pride led to downfall. The Enlightened Ones sought to pierce the veil between realms in their Infinity Working, but instead tore asunder the fabric of reality. The Ethereal Lattice shattered, unleashing wild energies that reshaped the world and burned civilization to ash.',
              'The skies wept fire, the earth trembled and split, and the seas boiled. The Ancients\' wondrous creations turned against them or twisted into abominations. Most perished in an instant, while others fled in great arks to distant shores, never to return.',
              'After the Sundering came the Long Dark—uncounted millennia where the remnants of humanity huddled in the shadows, forgetting their former glory. Wild energies from the broken Lattice saturated the world, altering plants, beasts, and even people in strange and terrible ways.'
            ],
            events: [
              { year: 'The Final Day', description: 'The Infinity Working fails catastrophically, beginning the Sundering.' },
              { year: 'Unknown', description: 'The great cities fall silent as the Ethereal Lattice collapses.' },
              { year: 'Unknown', description: 'Beginning of the Long Dark, where all knowledge was lost.' }
            ]
          },
          {
            name: 'The Age of Awakening',
            period: '1 - 500 AR (After Restoration)',
            description: [
              'From darkness, light returned. Scattered tribes emerged to find a transformed world where strange energies—now called magic—flowed through all things. Some discovered they could channel these forces, becoming the first Wielders. Others found relics of the Ancients that responded to their touch, granting extraordinary abilities.',
              'The first true settlements formed around Ancient remnants. The Whispering Spires of Thaumanar attracted those who could hear the murmurs of forgotten wisdom. The Eternal Flame of Pyrothar, burning without fuel, gathered those seeking warmth and protection. The Crystal Gardens of Luminar housed living lights that kept darkness at bay.',
              'In this time, the Order of the Blazing Sigil emerged, led by those who bore strange marks that glowed when they invoked Ancient power. They gathered and protected fragments of old knowledge, believing the Ancients would one day return to guide humanity once more.'
            ],
            events: [
              { year: '1 AR', description: 'The Calendar of Restoration begins with the founding of Thaumanar around the Whispering Spires.' },
              { year: '87 AR', description: 'The first Wielders Guild established to teach control of magical energies.' },
              { year: '212 AR', description: 'Discovery of the Codex Infinitum, containing symbols that commanded Ancient relics.' },
              { year: '483 AR', description: 'The Council of Seven Settlements forms the first post-Sundering alliance.' }
            ]
          },
          {
            name: 'The Age of Kingdoms',
            period: '500 - 1500 AR',
            description: [
              'As populations grew and knowledge of relic-use expanded, true kingdoms emerged. The Luminar Dynasty claimed divine right through their blood connection to the "Star-Born" Ancients. The Thaumatocracy of Mystral derived power from their mastery of Wielding energies through geometric patterns. The Iron Concordat built war machines from Ancient designs.',
              'Great temples were erected around dormant Ancient engines mistaken for sleeping deities. The most revered was the Oracle of Nexus, a vast thinking engine that awoke periodically to offer cryptic wisdom. The Nexus Priesthood interpreted its proclamations, gaining tremendous influence throughout the known world.',
              'Ancient ruins became sites of pilgrimage and plunder. Relic hunters risked life and sanity seeking treasures, while scholars pored over fragments of Ancient script, trying to decipher their secrets. The most valuable finds were Crystal Minds—small glowing orbs containing vast knowledge that could be accessed by those with the right bloodline.'
            ],
            events: [
              { year: '542 AR', description: 'Coronation of Queen Elara I, founder of the Luminar Dynasty.' },
              { year: '789 AR', description: 'The Oracle of Nexus awakens, issuing the Prophecy of Convergence.' },
              { year: '1024 AR', description: 'The War of Singing Blades, when weapons of the Ancients were turned against their wielders.' },
              { year: '1487 AR', description: 'The Great Conclave establishes the five rules of relic handling still followed today.' }
            ]
          },
          {
            name: 'The Modern Age',
            period: '1500 AR - Present (2103 AR)',
            description: [
              'Today\'s world is a complex tapestry of kingdoms, city-states, and wild territories where Ancient influence still warps reality. Magic—the residual energy of the Ethereal Lattice—flows stronger in some regions, creating zones of wonder and peril. The largest civilization is the Seven Spires Confederation, centered around towering Ancient structures that emit protective fields.',
              'Wielders now organize into colleges based on their approach to channeling energies. Runecrafters inscribe patterns that resonate with specific effects. Bloodline Channelers inherit power through descent from the Ancients. Voidspeakers commune with mysterious entities from beyond the Sundering.',
              'Of growing concern are the recent discoveries of Active Nodes—Ancient facilities gradually reawakening across the land. Some believe these herald a new age of enlightenment, while others fear they signal another Sundering. As Ancient guardians stir and long-dormant systems reactivate, the world stands at a crossroads between rediscovered wonder and catastrophic repetition of past mistakes.'
            ],
            events: [
              { year: '1738 AR', description: 'The Pact of Harmony establishes peace among the major kingdoms after the Century War.' },
              { year: '1892 AR', description: 'First documented Active Node awakens in the Crimson Desert, transforming the surrounding wasteland into lush landscape.' },
              { year: '2067 AR', description: 'The Night of Ascending Stars, when multiple Ancient satellites became visible in the night sky.' },
              { year: '2103 AR', description: 'Present day. Ancient activity increases as the Prophecy of Convergence nears fulfillment.' }
            ]
          }
        ]
      };
    }
  }
  </script>
  
  <style scoped>
  .section-intro {
    text-align: center;
    max-width: 800px;
    margin: 0 auto 2em;
  }
  
  .timeline {
    position: relative;
    margin: 2rem 0;
    padding-left: 3rem;
  }
  
  .timeline::before {
    content: "";
    position: absolute;
    left: 15px;
    top: 0;
    bottom: 0;
    width: 3px;
    background: linear-gradient(to bottom, 
      var(--color-primary) 0%, 
      var(--color-secondary) 50%, 
      var(--color-primary) 100%);
  }
  
  .era {
    position: relative;
    margin-bottom: 3rem;
  }
  
  .era:last-child {
    margin-bottom: 0;
  }
  
  .era::before {
    content: "";
    position: absolute;
    width: 25px;
    height: 25px;
    border-radius: 50%;
    background: var(--color-surface);
    border: 3px solid var(--color-primary);
    left: -4.5rem;
    top: 0.5rem;
  }
  
  .era-header {
    display: flex;
    align-items: baseline;
    margin-bottom: 1rem;
  }
  
  .era-header h2 {
    margin: 0;
    margin-right: 1rem;
    font-family: var(--font-display);
  }
  
  .era-year {
    color: var(--color-text-muted);
    font-style: italic;
  }
  
  .era-content {
    padding-left: 1rem;
    border-left: 1px solid var(--border-color);
  }
  
  .key-events {
    margin-top: 1.5rem;
    background: rgba(0, 0, 0, 0.2);
    padding: 1rem;
    border-radius: 4px;
  }
  
  .key-events h3 {
    margin-top: 0;
    font-family: var(--font-accent);
    color: var(--color-primary);
    font-size: 1.2rem;
  }
  
  .key-events ul {
    margin: 0;
    padding-left: 1.5rem;
  }
  
  .key-events li {
    margin-bottom: 0.5rem;
  }
  
  .key-events li:last-child {
    margin-bottom: 0;
  }
  
  .event-year {
    font-weight: bold;
    color: var(--color-primary);
  }
  
  @media (max-width: 768px) {
    .timeline {
      padding-left: 2rem;
    }
    
    .era::before {
      left: -4.5rem;
      width: 20px;
      height: 20px;
    }
  }
  
  @media (max-width: 480px) {
    .timeline {
      padding-left: 1.5rem;
    }
    
    .era::before {
      left: -2.2rem;
      width: 16px;
      height: 16px;
    }
    
    .era-header {
      flex-direction: column;
    }
    
    .era-year {
      margin-bottom: 0.5rem;
    }
  }
  </style>
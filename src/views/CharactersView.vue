<template>
    <div class="content-section">
      <h1>Player Characters</h1>
      <p class="section-intro">The brave adventurers navigating the perils of the Modern Age as Active Nodes reawaken across the land.</p>
  
      <div class="card-grid">
        <div v-for="char in characters" :key="char.name" class="card character-card">
          <div class="character-header">
            <div class="avatar-container">
              <!-- Avatar placeholder -->
              <div class="avatar-placeholder">
                <span>{{ getInitials(char.name) }}</span>
              </div>
            </div>
            <div class="character-title">
              <h3>{{ char.name }}</h3>
              <p class="character-subtitle">{{ char.race }} {{ char.class }}</p>
            </div>
          </div>
          
          <div class="character-details">
            <div class="detail-row">
              <span class="detail-label">Player:</span>
              <span class="detail-value">{{ char.player }}</span>
            </div>
            
            <div class="detail-row">
              <span class="detail-label">Level:</span>
              <span class="detail-value">{{ char.level }}</span>
            </div>
            
            <div class="detail-row">
              <span class="detail-label">Background:</span>
              <span class="detail-value">{{ char.background }}</span>
            </div>
            
            <div class="detail-row character-bio">
              <p>{{ char.bio }}</p>
            </div>
          </div>
          
          <a :href="char.dndBeyondLink" target="_blank" rel="noopener noreferrer" class="button-link">
            View on D&D Beyond
          </a>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'CharactersView',
    data() {
      return {
        characters: [
          {
            name: 'Thorne Ironheart',
            player: 'Player Name 1',
            race: 'Dwarf',
            class: 'Paladin',
            level: 5,
            background: 'Relic Hunter',
            bio: 'Born into a family of traditional relic hunters, Thorne discovered ancient armor in the ruins of Thaumanar that bonded to him, granting him paladin abilities. He seeks to fulfill the Prophecy of Convergence.',
            dndBeyondLink: 'https://www.dndbeyond.com/characters/123456',
          },
          {
            name: 'Lyra Moonshadow',
            player: 'Player Name 2',
            race: 'Elf',
            class: 'Ranger',
            level: 5,
            background: 'Survivor of Node Awakening',
            bio: 'Lyra\'s village was transformed when an Active Node awakened nearby. The sudden surge of magical energy changed the surrounding environment and wildlife, giving her a mystical connection to the altered creatures.',
            dndBeyondLink: 'https://www.dndbeyond.com/characters/789012',
          },
          {
            name: 'Zephyr Stormwind',
            player: 'Player Name 3',
            race: 'Tiefling',
            class: 'Sorcerer',
            level: 5,
            background: 'Bloodline Channeler',
            bio: 'Descendant of the Ancients, Zephyr\'s blood resonates with the remnants of the Ethereal Lattice. He possesses one of the rare Crystal Minds and can access fragments of Ancient knowledge through it.',
            dndBeyondLink: 'https://www.dndbeyond.com/characters/345678',
          },
          {
            name: 'Brom Oakenshield',
            player: 'Player Name 4',
            race: 'Human',
            class: 'Fighter',
            level: 5,
            background: 'Former Oracle Guard',
            bio: 'Once a dedicated protector of the Oracle of Nexus, Brom left his post after hearing a disturbing prophecy. He now seeks to prevent another Sundering by monitoring the increasing Ancient activity.',
            dndBeyondLink: 'https://www.dndbeyond.com/characters/901234',
          },
        ],
      };
    },
    methods: {
      getInitials(name) {
        return name.split(' ').map(word => word[0]).join('');
      }
    }
  }
  </script>
  
  <style scoped>
  .section-intro {
    text-align: center;
    max-width: 800px;
    margin: 0 auto 2em;
  }
  
  /* Fix for card grid layout */
  .card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 2rem;
    align-items: start;
  }
  
  .character-card {
    display: flex;
    flex-direction: column;
    height: 100%;
    margin: 0; /* Remove any margin that might cause overflow */
  }
  
  .character-header {
    display: flex;
    align-items: center;
    margin-bottom: 1.5rem;
  }
  
  .avatar-container {
    margin-right: 1rem;
  }
  
  .avatar-placeholder {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: var(--color-primary);
    color: var(--color-background);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    font-weight: bold;
    font-family: var(--font-display);
    border: 2px solid var(--color-text);
  }
  
  .character-title {
    flex-grow: 1;
  }
  
  .character-title h3 {
    margin: 0;
    font-size: 1.4rem;
  }
  
  .character-subtitle {
    color: var(--color-text-muted);
    margin: 0.2rem 0 0;
    font-size: 0.9rem;
  }
  
  .character-details {
    flex-grow: 1;
    margin-bottom: 1rem;
  }
  
  .detail-row {
    display: flex;
    margin-bottom: 0.5rem;
  }
  
  .detail-label {
    font-weight: bold;
    color: var(--color-primary);
    width: 100px;
  }
  
  .detail-value {
    flex-grow: 1;
  }
  
  .button-link {
    margin-top: auto;
    align-self: center;
  }

  .character-bio {
    margin-top: 1rem;
    display: block;
  }
  
  .character-bio p {
    margin: 0;
    font-style: italic;
    color: var(--color-text);
    line-height: 1.5;
  }
  </style>
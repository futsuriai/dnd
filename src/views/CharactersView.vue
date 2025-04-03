<template>
  <div class="content-section">
    <h1>Player Characters</h1>
    <p class="section-intro">The brave adventurers navigating the perils of the Modern Age as Active Nodes reawaken across the land.</p>

    <div class="card-grid">
      <div v-for="char in characters" :key="char.id" class="card character-card" :id="char.id">
        <div class="character-content">
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
        
        <EntityConnections :entityType="'character'" :entityId="char.id" />
      </div>
    </div>
  </div>
</template>

<script>
import { characters } from '../store/worldData';
import EntityConnections from '../components/EntityConnections.vue';

export default {
  name: 'CharactersView',
  components: {
    EntityConnections
  },
  data() {
    return {
      characters
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
  align-items: stretch; /* Make rows stretch to equal height */
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

.character-content {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.character-details {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
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
  margin-bottom: 1rem;
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
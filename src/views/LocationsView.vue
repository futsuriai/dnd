<template>
  <div class="content-section">
    <h1>World Locations</h1>
    <p class="section-intro">Explore important places, cities, dungeons, and landmarks in our campaign world.</p>

    <div class="locations-container">
      <div class="location-section">
        <h2>Major Cities</h2>
        <div v-if="getCitiesLocations().length" class="location-cards">
          <div v-for="location in getCitiesLocations()" :key="location.id" class="location-card" :id="location.id">
            <div class="location-content">
              <h3 class="location-title">{{ location.name }}</h3>
              <div class="location-meta">
                <span class="location-icon" v-html="getLocationIcon(location)"></span>
                <span class="location-region" v-if="location.region">{{ location.region }}</span>
              </div>
              <p class="location-description">{{ location.description }}</p>
            </div>
            <EntityConnections :entityType="'location'" :entityId="location.id" />
          </div>
        </div>
        <p v-else class="empty-message">No major cities discovered yet.</p>
      </div>

      <div class="location-section">
        <h2>Dungeons & Ruins</h2>
        <div v-if="getDungeonsLocations().length" class="location-cards">
          <div v-for="location in getDungeonsLocations()" :key="location.id" class="location-card" :id="location.id">
            <div class="location-content">
              <h3 class="location-title">{{ location.name }}</h3>
              <div class="location-meta">
                <span class="location-icon" v-html="getLocationIcon(location)"></span>
                <span class="location-region" v-if="location.region">{{ location.region }}</span>
              </div>
              <p class="location-description">{{ location.description }}</p>
            </div>
            <EntityConnections :entityType="'location'" :entityId="location.id" />
          </div>
        </div>
        <p v-else class="empty-message">No dungeons or ruins explored yet.</p>
      </div>

      <div class="location-section">
        <h2>Points of Interest</h2>
        <div v-if="getPointsOfInterestLocations().length" class="location-cards">
          <div v-for="location in getPointsOfInterestLocations()" :key="location.id" class="location-card" :id="location.id">
            <div class="location-content">
              <h3 class="location-title">{{ location.name }}</h3>
              <div class="location-meta">
                <span class="location-icon" v-html="getLocationIcon(location)"></span>
                <span class="location-region" v-if="location.region">{{ location.region }}</span>
              </div>
              <p class="location-description">{{ location.description }}</p>
            </div>
            <EntityConnections :entityType="'location'" :entityId="location.id" />
          </div>
        </div>
        <p v-else class="empty-message">No notable landmarks discovered yet.</p>
      </div>
    </div>
  </div>
</template>

<script>
import { getLocations } from '../store/worldData';
import EntityConnections from '../components/EntityConnections.vue';

export default {
  name: 'LocationsView',
  components: {
    EntityConnections
  },
  methods: {
    getCitiesLocations() {
      return getLocations('city');
    },
    getDungeonsLocations() {
      return getLocations('dungeon');
    },
    getPointsOfInterestLocations() {
      return getLocations('poi');
    },
    getLocationIcon(location) {
      // More specific and varied icons based on location qualities or subtype
      const cityIcons = {
        capital: '🏛️', // Capital city
        port: '⚓', // Port city
        trading: '🛒', // Trading hub
        magic: '✨', // Magic-focused city
        default: '🏙️' // Default city icon
      };
      
      const dungeonIcons = {
        ruin: '🏚️', // Ancient ruins
        cave: '🕳️', // Cave system
        temple: '🏯', // Ancient temple
        fortress: '🏰', // Fortress or castle
        default: '💀' // Default dungeon icon
      };
      
      const poiIcons = {
        natural: '🌳', // Natural landmark
        magic: '✨', // Magical phenomenon
        shrine: '🔮', // Shrine or sacred site
        monument: '🗿', // Monument
        default: '⭐' // Default POI icon
      };
      
      // Determine the icon based on location type and subtype
      if (location.type === 'city') {
        return cityIcons[location.subtype] || cityIcons.default;
      } else if (location.type === 'dungeon') {
        return dungeonIcons[location.subtype] || dungeonIcons.default;
      } else {
        return poiIcons[location.subtype] || poiIcons.default;
      }
    }
  }
};
</script>

<style scoped>
.section-intro {
  text-align: center;
  max-width: 800px;
  margin: 0 auto 2em;
}

.locations-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.location-section {
  background: var(--gradient-primary);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  padding: 1.5rem;
  box-shadow: var(--shadow-sm);
}

.location-section h2 {
  font-family: var(--font-display);
  color: var(--color-primary);
  margin-top: 0;
  margin-bottom: 1rem;
}

.empty-message {
  font-style: italic;
  color: var(--text-muted, #aaa);
}

.location-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.location-card {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  padding: 1.25rem;
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}

.location-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.location-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}

.location-title {
  margin-top: 0;
  margin-bottom: 0.75rem;
  color: var(--color-primary);
  font-family: var(--font-display);
  font-size: 1.3rem;
}

.location-meta {
  display: flex;
  align-items: center;
  margin-bottom: 0.75rem;
}

.location-icon {
  margin-right: 0.5rem;
  font-size: 1.1rem;
}

.location-region {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  font-style: italic;
}

.location-description {
  margin-bottom: 1rem;
  line-height: 1.6;
  flex: 1; /* Make description take remaining space */
}

@media (max-width: 768px) {
  .location-cards {
    grid-template-columns: 1fr;
  }
}
</style>

<template>
  <div class="content-section">
    <h1>World Locations</h1>
    <p class="section-intro">Explore important places, cities, dungeons, and landmarks in our campaign world.</p>

    <div class="locations-container">
      <div class="location-section">
        <h2>Major Cities</h2>
        <div v-if="getCitiesLocations().length" class="entity-grid">
          <EntityCard 
            v-for="location in getCitiesLocations()" 
            :key="location.id" 
            :entity="location" 
            entityType="location" 
          />
        </div>
        <p v-else class="empty-message">No major cities discovered yet.</p>
      </div>

      <div class="location-section">
        <h2>Dungeons & Ruins</h2>
        <div v-if="getDungeonsLocations().length" class="entity-grid">
          <EntityCard 
            v-for="location in getDungeonsLocations()" 
            :key="location.id" 
            :entity="location" 
            entityType="location" 
          />
        </div>
        <p v-else class="empty-message">No dungeons or ruins explored yet.</p>
      </div>

      <div class="location-section">
        <h2>Points of Interest</h2>
        <div v-if="getPointsOfInterestLocations().length" class="entity-grid">
          <EntityCard 
            v-for="location in getPointsOfInterestLocations()" 
            :key="location.id" 
            :entity="location" 
            entityType="location" 
          />
        </div>
        <p v-else class="empty-message">No notable landmarks discovered yet.</p>
      </div>
    </div>
  </div>
</template>

<script>
import { getLocations } from '../store/worldData';
import { locations } from '../store/worldData'; // Import local data as fallback
import EntityCard from '../components/EntityCard.vue';

export default {
  name: 'LocationsView',
  components: {
    EntityCard
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
    }
  }
};
</script>

<style scoped>
/* Component-specific styles only - common styles moved to global CSS */
</style>

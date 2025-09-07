<template>
  <div class="content-section">
    <h1>World Locations</h1>
    <div class="locations-container">
      <!-- Iterate through Provinces -->
      <div 
        v-for="province in provinces" 
        :key="province.id" 
        class="location-section province-section"
      >
        <!-- Display Province Card -->
        <EntityCard
          :entity="province"
          entityType="location"
          :class="['location-card', `location-type-${province.type}`]"
          @show-full-text="showFullTextModal"
        >
          <!-- Add a link specifically for Bastion City -->
          <template v-if="province.id === 'bastion-city'" #actions>
            <router-link :to="{ name: 'bastion-city' }" class="button-link">View City Locations</router-link>
          </template>
        </EntityCard>
        
        <!-- Nested Locations (Capitals, Cities within this Province) -->
        <div v-if="getLocationsInProvince(province.id).length" class="nested-locations entity-grid">
          <EntityCard
            v-for="location in getLocationsInProvince(province.id)"
            :key="location.id"
            :entity="location"
            entityType="location"
            :class="['location-card', `location-type-${location.type}`]"
            @show-full-text="showFullTextModal"
          />
        </div>
        <p v-else class="empty-message nested-empty">No known locations within {{ province.name }}.</p>
      </div>
      <p v-if="!provinces.length" class="empty-message">No provinces recorded yet.</p>

      <!-- Dungeons & Ruins Section (Conditional) -->
      <div v-if="dungeons.length" class="location-section">
        <h2>Dungeons & Ruins</h2>
        <div class="entity-grid">
          <EntityCard 
            v-for="location in dungeons" 
            :key="location.id" 
            :entity="location" 
            entityType="location" 
            @show-full-text="showFullTextModal"
          />
        </div>
      </div>

      <!-- Points of Interest Section (Conditional) -->
      <div v-if="pointsOfInterest.length" class="location-section">
        <h2>Points of Interest</h2>
        <div class="entity-grid">
          <EntityCard 
            v-for="location in pointsOfInterest" 
            :key="location.id" 
            :entity="location" 
            entityType="location" 
            @show-full-text="showFullTextModal"
          />
        </div>
      </div>
    </div>
    
    <FullTextModal 
      :visible="isModalVisible" 
      :title="modalTitle" 
      :text="modalText" 
      @close="closeModal" 
    />
  </div>
</template>

<script>
// Import the raw data instead of the getter function
import { locations } from '../store/locations'; 
import EntityCard from '../components/EntityCard.vue';
import FullTextModal from '@/components/FullTextModal.vue'; // Import the modal

export default {
  name: 'LocationsView',
  components: {
    EntityCard,
    FullTextModal // Register the modal
  },
  data() {
    return {
      locations: locations,
      isModalVisible: false, // State for modal visibility
      modalText: '', // State for modal content
      modalTitle: '' // Add state for modal title
    };
  },
  computed: {
    // Filter locations directly within the component
    allLocations() {
      // In a real app, this might come from a Vuex store or API call
      return locations; 
    },
    provinces() {
      return this.allLocations.filter(loc => loc.type === 'province');
    },
    dungeons() {
      return this.allLocations.filter(loc => loc.type === 'dungeon');
    },
    pointsOfInterest() {
  const poiTypes = ['poi', 'landmark', 'tavern'];
  return this.allLocations.filter(loc => poiTypes.includes(loc.type));
    }
  },
  methods: {
    getLocationsInProvince(provinceId) {
      // Find locations (like capitals or cities) that list the provinceId in their connections
      return this.allLocations.filter(loc => 
        loc.type !== 'province' && // Exclude the province itself
        loc.connections?.some(conn => conn.type === 'location' && conn.id === provinceId)
      );
    },
    showFullTextModal(payload) { // Accept payload object
      this.modalTitle = payload.title; // Set title
      this.modalText = payload.text; // Set text
      this.isModalVisible = true;
    },
    closeModal() { // Method to hide modal
      this.isModalVisible = false;
      this.modalText = '';
      this.modalTitle = ''; // Clear title on close
    }
    // Keep original getters for potential future use or different views if needed
    // getCitiesLocations() { ... }, 
    // getDungeonsLocations() { ... },
    // getPointsOfInterestLocations() { ... }
  }
};
</script>

<style scoped>
/* Component-specific styles only - common styles moved to global CSS */
.empty-message {
  text-align: center;
  margin-top: 1rem;
  color: var(--text-muted);
}

.location-section {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem; /* Add some space below each section */
  border-bottom: 1px solid var(--background-tertiary); /* Separator line */
}

.location-section:last-child {
  border-bottom: none; /* No line for the last section */
}

.province-section {
  border-bottom: none; /* Provinces manage their own bottom margin */
  margin-bottom: 2.5rem; /* More space after a province and its nested items */
}

.nested-locations {
  margin-top: 1rem; /* Space between province card and nested items */
  /* Removed margin-left and border-left for edge alignment */
  padding-left: 0; /* Remove padding */
  /* border-left: 2px solid var(--background-tertiary); /* Visual indicator for nesting - REMOVED */
}

.nested-empty {
  /* Removed margin-left */
  padding-left: 1rem; /* Add some padding to align text slightly */
  font-style: italic;
}

/* Style Province cards */
:deep(.location-card.location-type-province) {
  border-left: 3px solid var(--color-accent); /* Thinner border */
  background: rgba(var(--background-secondary-rgb), 0.1); /* Less prominent background */
  margin-bottom: 0.5rem; /* Reduce bottom margin */
  padding: 0;
}

:deep(.location-card) {
  padding: 0;
}


:deep(.location-card.location-type-province .entity-description) {
  margin-bottom: 0; /* Remove bottom margin */
}

:deep(.location-card .connections-header) {
  margin-left: 1.25em;
  padding-right: 0.5em;
}



/* Style Capital cards */
:deep(.location-card.location-type-capital) {
  border-left: 3px solid var(--color-primary); /* Example: Thinner primary border */
  /* margin-left: 1rem; /* Adjust or remove if .nested-locations handles indentation */
}

:deep(.location-card.location-type-capital .entity-name) {
  font-weight: bold; /* Bolder name for capitals */
  color: var(--color-primary);
}

</style>

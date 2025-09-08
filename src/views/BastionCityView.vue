<template>
  <div class="content-section">
    <h1>Bastion City</h1>
    <p>The capital of Hieroterra, where the campaign begins.</p>
    
    <div class="entity-grid">
      <EntityCard 
        v-for="location in bastionLocations" 
        :key="location.id" 
        :entity="location" 
        entityType="location"
        @show-full-text="showFullTextModal" 
      />
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
import EntityCard from '@/components/EntityCard.vue';
import FullTextModal from '@/components/FullTextModal.vue'; // Import the modal
import { locations } from '@/store/locations.js';
import { sortEntitiesByLastSession } from '@/utils/entitySorting.js'; // Import sorting utility

export default {
  name: 'BastionCityView',
  components: {
    EntityCard,
    FullTextModal // Register the modal
  },
  data() {
    return {
      isModalVisible: false, // State for modal visibility
      modalText: '', // State for modal content
      modalTitle: '' // Add state for modal title
    };
  },
  computed: {
    bastionLocations() {
      // Filter locations that are explicitly tagged as 'bastion city' 
      // or are connected to 'bastion-city'
      const bastionLocationList = locations.filter(loc => 
        loc.tags?.includes('bastion city') || 
        loc.connections?.some(conn => conn.type === 'location' && conn.id === 'bastion-city')
      );
      return sortEntitiesByLastSession(bastionLocationList);
    }
  },
  methods: {
    showFullTextModal(payload) { // Accept payload object
      this.modalTitle = payload.title; // Set title
      this.modalText = payload.text; // Set text
      this.isModalVisible = true;
    },
    closeModal() { 
      this.isModalVisible = false;
      this.modalText = '';
      this.modalTitle = ''; // Clear title on close
    }
  }
};
</script>

<style scoped>
.empty-message {
  text-align: center;
  margin-top: 1rem;
  color: var(--text-muted);
  font-style: italic;
}

/* Add any specific styles for this view if needed */
</style>

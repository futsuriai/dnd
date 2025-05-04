<template>
  <div class="content-section">
    <h1>Player Characters</h1>

    <div class="entity-grid">
      <EntityCard 
        v-for="character in characters" 
        :key="character.id" 
        :entity="character" 
        entityType="character"
        :showAvatar="true"
        :avatarUrl="character.avatarUrl"
        :portraitUrl="character.portraitUrl"
        @show-full-text="showFullTextModal" 
        @show-portrait="showPortraitModal" 
      />
    </div>
    
    <FullTextModal 
      :visible="isModalVisible" 
      :title="modalTitle" 
      :text="modalText" 
      :imageUrl="modalImageUrl"
      @close="closeModal" 
    />
  </div>
</template>

<script>
import { characters } from '../store/worldData';
import EntityCard from '../components/EntityCard.vue';
import FullTextModal from '@/components/FullTextModal.vue'; // Import the modal

export default {
  name: 'CharactersView',
  components: {
    EntityCard,
    FullTextModal // Register the modal
  },
  data() {
    return {
      characters,
      isModalVisible: false, // State for modal visibility
      modalText: '', // State for modal content
      modalTitle: '', // Add state for modal title
      modalImageUrl: null // Add state for image URL
    };
  },
  methods: {
    showFullTextModal(payload) { // Accept payload object
      this.modalTitle = payload.title; // Set title
      this.modalText = payload.text; // Set text
      this.modalImageUrl = null; // Ensure image is cleared
      this.isModalVisible = true;
    },
    showPortraitModal(payload) { // Handle portrait display
      this.modalTitle = payload.title;
      this.modalImageUrl = payload.imageUrl;
      this.modalText = ''; // Ensure text is cleared
      this.isModalVisible = true;
    },
    closeModal() { 
      this.isModalVisible = false;
      this.modalText = '';
      this.modalTitle = ''; // Clear title on close
      this.modalImageUrl = null; // Clear image URL on close
    }
  }
}
</script>

<style scoped>
/* Component-specific styles only - common styles moved to global CSS */
</style>
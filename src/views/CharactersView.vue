<template>
  <div class="content-section">
    <h1>Player Characters</h1>

    <!-- Character submenu only on main characters page, not on detail pages -->
    <CharacterSubmenu v-if="!characterId" :currentCharacterId="characterId" />

    <!-- Display character detail if ID provided -->
    <CharacterDetailView v-if="characterId" :characterId="characterId" />
    
    <!-- Display list of characters if no ID -->
    <div v-else class="entity-grid">
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
import CharacterSubmenu from '../components/CharacterSubmenu.vue'; // Import the submenu
import CharacterDetailView from './CharacterDetailView.vue'; // Import the detail view

export default {
  name: 'CharactersView',
  components: {
    EntityCard,
    FullTextModal,
    CharacterSubmenu,
    CharacterDetailView
  },
  props: {
    id: {
      type: String,
      default: null
    }
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
  computed: {
    characterId() {
      return this.id;
    }
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
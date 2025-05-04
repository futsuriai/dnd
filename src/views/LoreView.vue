<template>
    <div class="content-section">
      <h1>World Lore</h1>
      <div class="lore-list">
        <!-- Use EntityCard to display each lore item -->
        <EntityCard 
          v-for="(item, index) in loreEntries" 
          :key="index" 
          :entity="item" 
          entityType="lore"
          @show-full-text="showFullTextModal" 
        />
      </div>
      <!-- Add the FullTextModal component -->
      <FullTextModal 
        :visible="isModalVisible" 
        :title="modalTitle" 
        :text="modalText" 
        @close="closeModal" 
      />
    </div>
  </template>
  
  <script>
import { marked } from 'marked'; // Import marked library
import EntityCard from '@/components/EntityCard.vue';
import FullTextModal from '@/components/FullTextModal.vue'; // Import the modal
import EntityConnections from '@/components/EntityConnections.vue'; // Import EntityConnections
import { lore } from '@/store/lore.js';
  
export default {
  name: 'LoreView',
  components: {
    EntityCard,
    FullTextModal, // Register the modal
    EntityConnections // Register EntityConnections
  },
  data() {
    return {
      loreEntries: lore,
      isModalVisible: false, // State for modal visibility
      modalText: '', // State for modal content
      modalTitle: '' // Add state for modal title
    };
  },
  methods: {
      formatDescription(description) {
        // This method might no longer be needed directly in the template 
        // if EntityCard handles description display, but keep it for now 
        // in case EntityCard relies on formatted HTML or if used elsewhere.
        return marked.parse(description || '');
      },
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
  .section-intro {
    text-align: center;
    max-width: 800px;
    margin: 0 auto 2em;
  }
  
  .lore-list {
    display: grid; /* Change to grid for better card layout */
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); /* Responsive grid */
    gap: 1.5rem;
  }
  
  /* Remove styles specific to the old .lore-item structure */
  /* .lore-item { ... } */
  /* .lore-term { ... } */
  /* .lore-description { ... } */
  
  /* Styles for blockquotes/italics might need adjustment if EntityCard handles description differently */
  /* .lore-description :deep(blockquote) { ... } */
  /* .lore-description :deep(em) { ... } */
  </style>
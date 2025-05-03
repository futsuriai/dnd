<template>
  <div class="content-section">
    <h1>Magical Items & Artifacts</h1>
    <p class="section-intro">Ancient relics and magical items from the Age of Wonders, recovered from forgotten ruins.</p>

    <div v-if="items.length" class="entity-grid">
      <EntityCard 
        v-for="(item, index) in items" 
        :key="index" 
        :entity="item" 
        entityType="item"
      />
    </div>
    <p v-else class="empty-message">No items recorded yet.</p> <!-- Added empty message -->
  </div>
</template>

<script>
import EntityCard from '../components/EntityCard.vue';
import { items } from '../store/worldData'; // Import items from worldData

export default {
  name: 'ItemsView',
  components: {
    EntityCard
  },
  data() {
    return {
      items // Use imported items
    };
  }
};
</script>

<style scoped>
/* Component-specific styles only - common styles moved to global CSS */
.empty-message {
  text-align: center;
  margin-top: 2rem;
  color: var(--text-muted);
}
</style>
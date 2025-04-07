<template>
  <div class="content-section">
    <h1>Magical Items & Artifacts</h1>
    <p class="section-intro">Ancient relics and magical items from the Age of Wonders, recovered from forgotten ruins.</p>

    <div class="entity-grid">
      <EntityCard 
        v-for="item in items" 
        :key="item.id" 
        :entity="item" 
        entityType="item"
      />
    </div>
  </div>
</template>

<script>
import EntityCard from '../components/EntityCard.vue';
import { getAllItems } from '../src/store/worldData';

export default {
  name: 'ItemsView',
  components: {
    EntityCard
  },
  data() {
    return {
      items: []
    };
  },
  async created() {
    // Load items from worldData
    this.items = await getAllItems();
  }
};
</script>

<style scoped>
/* Component-specific styles only - common styles moved to global CSS */
</style>
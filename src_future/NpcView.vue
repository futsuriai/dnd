<template>
  <div class="content-section">
    <h1>Notable NPCs</h1>
    <p class="section-intro">Key figures encountered throughout the realm of the Seven Spires Confederation.</p>
    
    <div v-if="npcs.length" class="entity-grid">
      <EntityCard 
        v-for="npc in npcs" 
        :key="npc.id" 
        :entity="npc" 
        entityType="npc"
      />
    </div>
    <p v-else class="empty-message">No NPCs recorded yet.</p>
  </div>
</template>

<script>
import { npcs } from '../src/store/worldData';
import EntityCard from '../components/EntityCard.vue';

export default {
  name: 'NpcView',
  components: {
    EntityCard
  },
  data() {
    return {
      npcs
    };
  }
}
</script>

<style scoped>
/* Component-specific styles only - common styles moved to global CSS */
.empty-message {
  text-align: center;
  margin-top: 2rem;
  color: var(--text-muted);
}
</style>
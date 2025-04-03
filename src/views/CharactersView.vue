<template>
  <div class="content-section">
    <h1>Player Characters</h1>
    <p class="section-intro">The brave adventurers navigating the perils of the Modern Age as Active Nodes reawaken across the land.</p>

    <div class="entity-grid">
      <EntityCard 
        v-for="character in characters" 
        :key="character.id" 
        :entity="character" 
        entityType="character"
        :showAvatar="true"
      />
    </div>
  </div>
</template>

<script>
import { characters } from '../store/worldData';
import EntityCard from '../components/EntityCard.vue';

export default {
  name: 'CharactersView',
  components: {
    EntityCard
  },
  data() {
    return {
      characters
    };
  }
}
</script>

<style scoped>
/* Component-specific styles only - common styles moved to global CSS */
</style>
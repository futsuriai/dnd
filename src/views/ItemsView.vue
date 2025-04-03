<template>
  <div class="content-section">
    <h1>Magical Items & Artifacts</h1>
    <p class="section-intro">Ancient relics and magical items from the Age of Wonders, recovered from forgotten ruins.</p>

    <div class="entity-grid">
      <EntityCard 
        v-for="(item, index) in items" 
        :key="index" 
        :entity="item" 
        entityType="item"
      />
    </div>
  </div>
</template>

<script>
import EntityCard from '../components/EntityCard.vue';

export default {
  name: 'ItemsView',
  components: {
    EntityCard
  },
  data() {
    return {
      items: [
        {
          id: 'frostbite-blade',
          name: 'Frostbite Blade',
          type: 'Ancient Weapon (Ethereal Edge)',
          rarity: 'Rare',
          attunement: 'Required (Bloodline Affinity)',
          description: 'A longsword that appears to be made of translucent blue ice. Analysis suggests it\'s actually a fragment of the Ethereal Lattice, crystallized during the Sundering. It deals an additional 1d6 cold damage and slows targets by manipulating local temporal flow.',
          found: 'Recovered from an Active Node in the former Frozen Wastes, now the Crimson Desert',
          owner: 'Thorne Ironheart'
        },
        {
          id: 'amulet-of-true-sight',
          name: 'Amulet of True Sight',
          type: 'Luminous Concord Relic',
          rarity: 'Very Rare',
          attunement: 'Required (Any Wielder)',
          description: 'This silver amulet contains a fragment of a Celestial Lens from the Age of Wonders. The purple gemstone is actually a compressed data storage unit that interfaces with the wearer\'s visual cortex, allowing perception of invisible entities and the Ethereal Plane remnants.',
          found: 'Gift from Lord Silverhand after helping secure an Ancient archive',
          owner: 'Party Treasure'
        },
        {
          id: 'cloak-of-elvenkind',
          name: 'Cloak of Elvenkind',
          type: 'Adapted Ancient Technology',
          rarity: 'Uncommon',
          attunement: 'Not Required',
          description: 'This cloak incorporates threads from materials created by the Ancients. It contains microscopic adaptive camouflage nodes that respond to surroundings, granting advantage on Stealth checks and disadvantage to those perceiving the wearer.',
          found: 'Hidden cache in the Whispering Spires of Thaumanar',
          owner: 'Lyra Moonshadow'
        },
        {
          id: 'orb-of-dragonkind',
          name: 'Orb of Dragonkind',
          type: 'Crystal Mind (Specialized)',
          rarity: 'Legendary',
          attunement: 'Required (Bloodline Channeler only)',
          description: 'One of the legendary Crystal Minds containing Ancient knowledge specific to draconic entities. The Ancients studied and possibly created dragons as guardians. This orb can access those control protocols, but only for red dragons. Contains partial instructions from the Eternity Working that caused the Sundering.',
          found: 'Kragnor\'s vault in the Dark Spire Active Node',
          owner: 'Zephyr Stormwind'
        }
      ]
    };
  }
};
</script>

<style scoped>
/* Component-specific styles only - common styles moved to global CSS */
</style>
<template>
  <div class="content-section">
    <h1>Magical Items & Artifacts</h1>
    <p class="section-intro">Ancient relics and magical items from the Age of Wonders, recovered from forgotten ruins.</p>

    <div class="items-container">
      <div v-for="(item, index) in items" :key="index" class="item-card">
        <div class="item-content">
          <div class="item-header" :class="item.rarity.toLowerCase()">
            <h3>{{ item.name }}</h3>
            <span class="item-rarity">{{ item.rarity }}</span>
          </div>
          
          <div class="item-properties">
            <div class="property">
              <span class="property-label">Type:</span>
              <span>{{ item.type }}</span>
            </div>
            
            <div class="property">
              <span class="property-label">Attunement:</span>
              <span>{{ item.attunement }}</span>
            </div>
            
            <div class="property description">
              <span class="property-label">Description:</span>
              <p>{{ item.description }}</p>
            </div>
            
            <div class="property">
              <span class="property-label">Found:</span>
              <span>{{ item.found }}</span>
            </div>
            
            <div class="property">
              <span class="property-label">Current Owner:</span>
              <span>{{ item.owner }}</span>
            </div>
          </div>
        </div>
        
        <!-- Add EntityConnections when items have connections -->
        <EntityConnections v-if="hasConnections(item)" :entityType="'item'" :entityId="item.id" />
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ItemsView',
  data() {
    return {
      items: [
        {
          name: 'Frostbite Blade',
          type: 'Ancient Weapon (Ethereal Edge)',
          rarity: 'Rare',
          attunement: 'Required (Bloodline Affinity)',
          description: 'A longsword that appears to be made of translucent blue ice. Analysis suggests it\'s actually a fragment of the Ethereal Lattice, crystallized during the Sundering. It deals an additional 1d6 cold damage and slows targets by manipulating local temporal flow.',
          found: 'Recovered from an Active Node in the former Frozen Wastes, now the Crimson Desert',
          owner: 'Thorne Ironheart'
        },
        {
          name: 'Amulet of True Sight',
          type: 'Luminous Concord Relic',
          rarity: 'Very Rare',
          attunement: 'Required (Any Wielder)',
          description: 'This silver amulet contains a fragment of a Celestial Lens from the Age of Wonders. The purple gemstone is actually a compressed data storage unit that interfaces with the wearer\'s visual cortex, allowing perception of invisible entities and the Ethereal Plane remnants.',
          found: 'Gift from Lord Silverhand after helping secure an Ancient archive',
          owner: 'Party Treasure'
        },
        {
          name: 'Cloak of Elvenkind',
          type: 'Adapted Ancient Technology',
          rarity: 'Uncommon',
          attunement: 'Not Required',
          description: 'This cloak incorporates threads from materials created by the Ancients. It contains microscopic adaptive camouflage nodes that respond to surroundings, granting advantage on Stealth checks and disadvantage to those perceiving the wearer.',
          found: 'Hidden cache in the Whispering Spires of Thaumanar',
          owner: 'Lyra Moonshadow'
        },
        {
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
  },
  methods: {
    // Placeholder method - you might need to implement actual connection checking
    hasConnections(item) {
      // Return false for now since we don't have the data structure set up
      return false;
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

.items-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
  align-items: stretch;
}

.item-card {
  background: var(--gradient-primary);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.item-content {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border-accent);
}

.item-header h3 {
  margin: 0;
  font-family: var(--font-display);
}

.item-properties {
  padding: 1.5rem;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.property {
  margin-bottom: 1rem;
}

.property:last-child {
  margin-bottom: 0;
}

.property-label {
  font-weight: bold;
  color: var(--color-primary);
  margin-right: 0.5rem;
}

.description {
  margin-top: 1.5rem;
  margin-bottom: 1.5rem;
}

.description p {
  margin-top: 0.5rem;
  line-height: 1.6;
}

.item-rarity {
  font-family: var(--font-accent);
  font-size: 0.9em;
  font-weight: bold;
  padding: 0.3em 0.6em;
  border-radius: 4px;
  text-transform: uppercase;
}

/* Rarity styles */
.common {
  background-color: rgba(169, 169, 169, 0.1);
}
.common .item-rarity {
  color: #a9a9a9;
  background-color: rgba(169, 169, 169, 0.2);
}

.uncommon {
  background-color: rgba(75, 175, 80, 0.1);
}
.uncommon .item-rarity {
  color: #4baf50;
  background-color: rgba(75, 175, 80, 0.2);
}

.rare {
  background-color: rgba(33, 150, 243, 0.1);
}
.rare .item-rarity {
  color: #2196f3;
  background-color: rgba(33, 150, 243, 0.2);
}

.very.rare, .very-rare {
  background-color: rgba(156, 39, 176, 0.1);
}
.very.rare .item-rarity, .very-rare .item-rarity {
  color: #9c27b0;
  background-color: rgba(156, 39, 176, 0.2);
}

.legendary {
  background-color: rgba(255, 152, 0, 0.1);
}
.legendary .item-rarity {
  color: #ff9800;
  background-color: rgba(255, 152, 0, 0.2);
}

.artifact {
  background-color: rgba(244, 67, 54, 0.1);
}
.artifact .item-rarity {
  color: #f44336;
  background-color: rgba(244, 67, 54, 0.2);
}
</style>
<template>
  <div class="content-section">
    <h1>World Locations</h1>
    <p class="section-intro">Explore important places, cities, dungeons, and landmarks in our campaign world.</p>

    <div class="locations-container">
      <div class="location-section">
        <h2>Major Cities</h2>
        <div v-if="getCitiesLocations().length" class="location-cards">
          <div v-for="(location, index) in getCitiesLocations()" :key="index" class="location-card">
            <h3 class="location-title">{{ location.name }}</h3>
            <p class="location-description">{{ location.description }}</p>
            <div v-if="location.relatedEntities && location.relatedEntities.length" class="related-entities">
              <span>Notable figures: </span>
              <span v-for="(entity, eIndex) in location.relatedEntities" :key="eIndex" class="entity-link" @click="navigateToEntity(entity)">
                {{ entity.name }}{{ eIndex < location.relatedEntities.length - 1 ? ', ' : '' }}
              </span>
            </div>
          </div>
        </div>
        <p v-else class="empty-message">No major cities discovered yet.</p>
      </div>

      <div class="location-section">
        <h2>Dungeons & Ruins</h2>
        <div v-if="getDungeonsLocations().length" class="location-cards">
          <div v-for="(location, index) in getDungeonsLocations()" :key="index" class="location-card">
            <h3 class="location-title">{{ location.name }}</h3>
            <p class="location-description">{{ location.description }}</p>
            <div v-if="location.relatedEntities && location.relatedEntities.length" class="related-entities">
              <span>Connected to: </span>
              <span v-for="(entity, eIndex) in location.relatedEntities" :key="eIndex" class="entity-link" @click="navigateToEntity(entity)">
                {{ entity.name }}{{ eIndex < location.relatedEntities.length - 1 ? ', ' : '' }}
              </span>
            </div>
          </div>
        </div>
        <p v-else class="empty-message">No dungeons or ruins explored yet.</p>
      </div>

      <div class="location-section">
        <h2>Points of Interest</h2>
        <div v-if="getPointsOfInterestLocations().length" class="location-cards">
          <div v-for="(location, index) in getPointsOfInterestLocations()" :key="index" class="location-card">
            <h3 class="location-title">{{ location.name }}</h3>
            <p class="location-description">{{ location.description }}</p>
            <div v-if="location.relatedEntities && location.relatedEntities.length" class="related-entities">
              <span>Associated with: </span>
              <span v-for="(entity, eIndex) in location.relatedEntities" :key="eIndex" class="entity-link" @click="navigateToEntity(entity)">
                {{ entity.name }}{{ eIndex < location.relatedEntities.length - 1 ? ', ' : '' }}
              </span>
            </div>
          </div>
        </div>
        <p v-else class="empty-message">No notable landmarks discovered yet.</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LocationsView',
  data() {
    return {
      locations: [
        {
          name: 'Thaumanar',
          type: 'city',
          description: 'The first major settlement established after the Restoration, built around the Whispering Spires. Known for its ancient architecture and the Wielders Guild headquarters. The city\'s foundations incorporate Ancient technology that still hums with power.',
          relatedEntities: [
            { type: 'character', name: 'Thorne Ironheart', id: 'thorne' }
          ]
        },
        {
          name: 'Nexus',
          type: 'city',
          description: 'Built around the Oracle temple, Nexus is a city of scholars, priests, and pilgrims. The Nexus Priesthood interprets the Oracle\'s cryptic wisdom, making the city a political and spiritual center of the known world.',
          relatedEntities: [
            { type: 'character', name: 'Brom Oakenshield', id: 'brom' }
          ]
        },
        {
          name: 'Spire Central',
          type: 'city',
          description: 'The capital of the Seven Spires Confederation, defined by seven towering Ancient structures that emit protective fields. The High Council chambers sit at the base of the tallest spire, where representatives gather to govern the confederation.',
          relatedEntities: [
            { type: 'npc', name: 'Lord Bartholomew Silverhand', id: 'silverhand' }
          ]
        },
        {
          name: 'Dark Spire Fortress',
          type: 'dungeon',
          description: 'A fortress built around an Active Node, where Ancient guardians patrol under the control of a modified Crystal Mind. The surrounding area has been twisted by wild energies, creating dangerous and surreal landscapes.',
          relatedEntities: [
            { type: 'npc', name: 'Kragnor the Merciless', id: 'kragnor' }
          ]
        },
        {
          name: 'Crystal Gardens of Luminar',
          type: 'poi',
          description: 'Vast gardens where crystalline plants grow, emitting gentle light that keeps darkness at bay. Many believe the gardens were once a recreational area for the Ancients, now overgrown and wild after millennia of neglect.',
          relatedEntities: []
        },
        {
          name: 'Eternal Flame of Pyrothar',
          type: 'poi',
          description: 'A massive flame that has burned without fuel since before recorded history. The surrounding city harnesses its heat for industry and comfort. Scholars theorize it may be a controlled breach in the Ethereal Lattice.',
          relatedEntities: []
        },
        {
          name: 'Oracle of Nexus',
          type: 'poi',
          description: 'A vast thinking engine of Ancient design that awakens periodically to offer cryptic wisdom. The Great Temple built around it is the center of the Nexus Priesthood\'s power and influence.',
          relatedEntities: [
            { type: 'character', name: 'Brom Oakenshield', id: 'brom' }
          ]
        },
        {
          name: 'Whisperwood Village',
          type: 'poi',
          description: 'Once an ordinary settlement, this village was transformed when an Active Node awakened nearby. The forest surrounding it has evolved rapidly, with plants and animals exhibiting unusual properties and intelligence.',
          relatedEntities: [
            { type: 'character', name: 'Lyra Moonshadow', id: 'lyra' }
          ]
        },
        {
          name: 'Crimson Desert Active Node',
          type: 'poi',
          description: 'The first documented Active Node to awaken in the modern era, transforming the surrounding wasteland into a lush landscape. Ancient mechanisms hum beneath the sands, and strange creatures adapted to the new environment roam the periphery.',
          relatedEntities: [
            { type: 'npc', name: 'Morana Shadowweaver', id: 'morana' }
          ]
        },
      ]
    };
  },
  methods: {
    getCitiesLocations() {
      return this.locations.filter(loc => loc.type === 'city');
    },
    getDungeonsLocations() {
      return this.locations.filter(loc => loc.type === 'dungeon');
    },
    getPointsOfInterestLocations() {
      return this.locations.filter(loc => loc.type === 'poi');
    },
    navigateToEntity(entity) {
      // For future implementation - navigate to character or NPC details
      console.log(`Navigate to ${entity.type} ${entity.name}`);
      // This could use Vue Router to navigate to the appropriate page
      // this.$router.push({ name: entity.type === 'character' ? 'characters' : 'npcs', hash: `#${entity.id}` });
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

.locations-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.location-section {
  background: var(--gradient-primary);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  padding: 1.5rem;
  box-shadow: var(--shadow-sm);
}

.location-section h2 {
  font-family: var(--font-display);
  color: var(--color-primary);
  margin-top: 0;
  margin-bottom: 1rem;
}

.empty-message {
  font-style: italic;
  color: var(--text-muted, #aaa);
}

.location-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.location-card {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  padding: 1.25rem;
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.location-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}

.location-title {
  margin-top: 0;
  margin-bottom: 0.75rem;
  color: var(--color-primary);
  font-family: var(--font-display);
  font-size: 1.3rem;
}

.location-description {
  margin-bottom: 1rem;
  line-height: 1.6;
}

.related-entities {
  font-size: 0.9rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-muted, #aaa);
}

.entity-link {
  color: var(--color-secondary);
  cursor: pointer;
  transition: color 0.2s ease;
  position: relative;
}

.entity-link:hover {
  color: var(--color-primary);
  text-decoration: underline;
}

.entity-link:after {
  content: "";
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 100%;
  height: 1px;
  background-color: var(--color-primary);
  transform: scaleX(0);
  transition: transform 0.2s ease;
}

.entity-link:hover:after {
  transform: scaleX(1);
}

@media (max-width: 768px) {
  .location-cards {
    grid-template-columns: 1fr;
  }
}
</style>

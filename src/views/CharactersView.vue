<template>
  <div class="content-section">
    <div v-if="loading" class="loading-indicator">
      <div class="spinner"></div>
      <p>Loading characters...</p>
    </div>
    
    <div v-else-if="error" class="error-message">
      <p>{{ error }}</p>
    </div>
    
    <div v-else class="entity-grid">
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
import EntityCard from '../components/EntityCard.vue';
import worldData from '../store/worldData';

export default {
  name: 'CharactersView',
  components: {
    EntityCard
  },
  data() {
    return {
      characters: [],
      loading: true,
      error: null,
      // Flag to use Firestore data or fallback to local data (now handled in worldData.js)
      useFirestore: true
    };
  },
  created() {
    // Load character data
    this.loadCharacters();
  },
  methods: {
    async loadCharacters() {
      this.loading = true;
      this.error = null;
      
      try {
        // Initialize worldData to determine data source
        await worldData.initWorldData();
        
        // Get all characters using worldData adapter
        this.characters = await worldData.getAllCharacters();
        
        // Sort characters by name
        this.characters.sort((a, b) => {
          return a.name.localeCompare(b.name);
        });
      } catch (err) {
        console.error('Error loading characters:', err);
        this.error = `Error loading characters: ${err.message}`;
      } finally {
        this.loading = false;
      }
    }
  }
}
</script>

<style scoped>
.entity-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.loading-indicator, .error-message {
  text-align: center;
  padding: 40px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  border-top-color: #2196F3;
  margin: 0 auto 15px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  color: #F44336;
  background-color: rgba(244, 67, 54, 0.1);
  border-radius: 4px;
  padding: 20px;
}

@media (max-width: 768px) {
  .entity-grid {
    grid-template-columns: 1fr;
  }
}
</style>
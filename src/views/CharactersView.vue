<template>
  <div class="content-section">
    <h1>Player Characters</h1>
    <p class="section-intro">The brave adventurers navigating the perils of the Modern Age as Active Nodes reawaken across the land.</p>

    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Loading characters...</p>
    </div>
    
    <div v-else-if="error" class="error-message">
      <p>{{ error }}</p>
      <button @click="loadCharacters" class="retry-button">Try Again</button>
    </div>
    
    <div v-else-if="characters.length === 0" class="empty-state">
      <p>No characters found.</p>
      <p v-if="isEditor" class="editor-hint">
        <router-link to="/admin" class="admin-link">Go to Admin Panel</router-link> to add characters.
      </p>
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
import firestoreService from '../services/FirestoreService';
import authService from '../services/AuthService';
// Import local data as fallback
import { characters as localCharacters } from '../store/worldData';

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
      isEditor: false,
      // Flag to use Firestore data or fallback to local data
      useFirestore: true
    };
  },
  created() {
    // Check if user is editor
    this.unsubscribe = authService.addAuthListener((user, isEditor) => {
      this.isEditor = isEditor;
    });
    
    // Load character data
    this.loadCharacters();
  },
  beforeUnmount() {
    // Clean up auth listener
    if (this.unsubscribe) {
      this.unsubscribe();
    }
  },
  methods: {
    async loadCharacters() {
      this.loading = true;
      this.error = null;
      
      try {
        if (this.useFirestore) {
          // Fetch characters from Firestore
          this.characters = await firestoreService.getAllCharacters();
          
          // If no characters are in Firestore yet, fall back to local data
          if (this.characters.length === 0) {
            console.log('No characters found in Firestore, using local data');
            this.characters = localCharacters;
          }
        } else {
          // Use local data directly
          this.characters = localCharacters;
        }
      } catch (error) {
        console.error('Error loading characters:', error);
        this.error = 'Failed to load characters. Please try again.';
        // Fall back to local data on error
        this.characters = localCharacters;
      } finally {
        this.loading = false;
      }
    }
  }
}
</script>

<style scoped>
/* Component-specific styles only - common styles moved to global CSS */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  border-top-color: var(--color-primary);
  animation: spin 1s ease-in-out infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  background: rgba(220, 53, 69, 0.1);
  border: 1px solid rgba(220, 53, 69, 0.3);
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
  margin: 1rem 0;
}

.retry-button {
  background: var(--color-primary);
  color: var(--color-background);
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  margin-top: 0.5rem;
  cursor: pointer;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  border: 1px dashed var(--border-color);
  margin: 1rem 0;
}

.admin-link {
  color: var(--color-primary);
  text-decoration: underline;
  font-weight: bold;
}

.editor-hint {
  margin-top: 0.5rem;
  font-style: italic;
}
</style>
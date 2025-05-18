<template>
  <div class="character-detail-view">
    <div class="content-section">
      <!-- Character submenu for navigation between characters -->
      <CharacterSubmenu :currentCharacterId="characterId" />
      
      <div v-if="character">
        <div class="character-header">
          <div class="character-avatar">
            <img v-if="character.avatarUrl" :src="character.avatarUrl" :alt="character.name" />
            <div v-else class="avatar-placeholder">{{ getInitials(character.name) }}</div>
          </div>
          
          <div class="character-info">
            <h1>{{ character.name }}</h1>
            <div class="character-subtitle">
              <div>{{ character.race }}</div>
              <div>{{ character.class }} (Level {{ character.level }})</div>
              <div>{{ character.background }}</div>
            </div>
            
            <div class="character-actions">
              <a v-if="character.dndBeyondLink" :href="character.dndBeyondLink" target="_blank" rel="noopener noreferrer" class="dndbeyond-link">
                View on D&D Beyond
              </a>
              <button v-if="character.portraitUrl" @click="showPortrait" class="view-portrait-btn">
                View Full Image
              </button>
            </div>
          </div>
        </div>
        
        <div class="character-bio">
          <h2>Biography</h2>
          <p>{{ character.bio }}</p>
        </div>
        
        <!-- Slot for character-specific content -->
        <slot></slot>
        
        <!-- Character Connections -->
        <div class="character-connections">
          <h2>Connections</h2>
          <EntityConnections 
            entityType="character" 
            :entityId="characterId"
          />
        </div>
      </div>
      
      <div v-else class="character-not-found">
        <h2>Character not found</h2>
        <p>Sorry, the character you're looking for doesn't exist.</p>
        <router-link to="/characters" class="back-link">Return to Characters</router-link>
      </div>
    </div>
    
    <!-- Modal for portrait -->
    <FullTextModal 
      :visible="isModalVisible" 
      :title="modalTitle" 
      :imageUrl="modalImageUrl"
      @close="closeModal" 
    />
  </div>
</template>

<script>
import { characters } from '../store/worldData';
import CharacterSubmenu from '../components/CharacterSubmenu.vue';
import EntityConnections from '../components/EntityConnections.vue';
import FullTextModal from '../components/FullTextModal.vue';

export default {
  name: 'CharacterDetailView',
  components: {
    CharacterSubmenu,
    EntityConnections,
    FullTextModal
  },
  props: {
    characterId: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      isModalVisible: false,
      modalTitle: '',
      modalImageUrl: null
    };
  },
  computed: {
    character() {
      return characters.find(char => char.id === this.characterId);
    }
  },
  methods: {
    getInitials(name) {
      return name.split(' ').map(word => word[0]).join('');
    },
    showPortrait() {
      if (this.character && this.character.portraitUrl) {
        this.modalTitle = this.character.name;
        this.modalImageUrl = this.character.portraitUrl;
        this.isModalVisible = true;
      }
    },
    closeModal() {
      this.isModalVisible = false;
      this.modalTitle = '';
      this.modalImageUrl = null;
    }
  }
};
</script>

<style scoped>
.character-detail-view {
  padding-bottom: 2rem;
}

.character-header {
  display: flex;
  margin-bottom: 2rem;
  gap: 2rem;
}

.character-avatar {
  width: 180px;
  height: 180px;
  flex-shrink: 0;
  border-radius: 10px;
  overflow: hidden;
  border: 3px solid var(--border-color, #333);
  box-shadow: var(--shadow-lg);
}

.character-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  background-color: var(--color-primary, #375a7f);
  color: var(--color-background, #121212);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3rem;
  font-weight: bold;
  font-family: var(--heading-font, inherit);
}

.character-info {
  flex: 1;
}

.character-info h1 {
  margin-top: 0;
  margin-bottom: 0.5rem;
  color: var(--accent-color, #d4af37);
}

.character-subtitle {
  color: var(--color-text-muted, #aaa);
  margin-bottom: 1.5rem;
  font-size: 1.1rem;
}

.character-subtitle > div {
  margin-bottom: 0.2rem;
}

.character-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.dndbeyond-link, .view-portrait-btn {
  padding: 0.7rem 1.4rem;
  border-radius: 4px;
  text-decoration: none;
  display: inline-block;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s ease;
}

.dndbeyond-link {
  background-color: #e40712; /* D&D Beyond color */
  color: white;
  border: none;
}

.dndbeyond-link:hover {
  background-color: #c20510;
}

.view-portrait-btn {
  background-color: var(--color-primary, #375a7f);
  color: white;
  border: none;
}

.view-portrait-btn:hover {
  background-color: var(--color-primary-dark, #2c4a6b);
}

.character-bio {
  margin-bottom: 2rem;
  line-height: 1.7;
  font-size: 1.05rem;
}

.character-bio h2 {
  border-bottom: 1px solid var(--border-color, #333);
  padding-bottom: 0.5rem;
  margin-bottom: 1rem;
}

.character-connections {
  margin-top: 2rem;
}

.character-connections h2 {
  border-bottom: 1px solid var(--border-color, #333);
  padding-bottom: 0.5rem;
  margin-bottom: 1rem;
}

.character-not-found {
  text-align: center;
  padding: 4rem 0;
}

.back-link {
  display: inline-block;
  margin-top: 1rem;
  color: var(--accent-color, #d4af37);
  text-decoration: none;
  font-weight: bold;
}

.back-link:hover {
  text-decoration: underline;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .character-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 1rem;
  }
  
  .character-avatar {
    width: 150px;
    height: 150px;
  }
  
  .character-actions {
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .character-actions {
    flex-direction: column;
    gap: 0.7rem;
  }
  
  .dndbeyond-link, .view-portrait-btn {
    width: 100%;
    text-align: center;
  }
}
</style>

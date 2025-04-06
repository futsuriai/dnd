<template>
  <div class="content-section">
    <h1>Campaign Sessions</h1>
    <p class="section-intro">Chronicles of our adventures and key events from each session.</p>

    <div class="sessions-container">
      <div v-for="session in sessions" :key="session.id" class="session-card" :id="session.id">
        <div class="session-header" :class="{ 'upcoming': session.upcoming }">
          <div class="header-top-line">
            <h3 class="session-title">{{ session.title }}:</h3>
            <span class="session-date">{{ session.date }}</span>
          </div>
          <p class="session-subtitle">{{ session.subtitle }}</p>
        </div>
        
        <div class="session-content">
          <div v-if="session.upcoming" class="upcoming-message">
            <p>{{ session.description }}</p>
          </div>
          <div v-else class="session-summary">
            <p>{{ session.description }}</p>
            
            <div v-if="session.highlights" class="highlights">
              <h4>Key Moments:</h4>
              <ul>
                <li v-for="(highlight, i) in session.highlights" :key="i">
                  {{ highlight }}
                </li>
              </ul>
            </div>
            
            <!-- Session affected entities section -->
            <div v-if="!session.upcoming && getSessionEntitiesData(session.id).length > 0" class="session-affected-entities">
              <div class="affected-entities-header" @click="toggleEntityChanges(session.id)">
                <h4>Entities Affected</h4>
                <span class="toggle-icon">{{ isEntityChangesOpen(session.id) ? '▼' : '▶' }}</span>
              </div>
              
              <div v-show="isEntityChangesOpen(session.id)" class="affected-entities-content">
                <div class="entity-changes-categories">
                  <!-- Characters -->
                  <div v-if="getSessionEntitiesByType(session.id, 'character').length > 0" class="entity-type-group">
                    <h5>Characters</h5>
                    <div class="session-entity-grid">
                      <div v-for="entity in getSessionEntitiesByType(session.id, 'character')" 
                           :key="entity.id"
                           class="session-entity-card">
                        <div class="entity-name">{{ entity.entity.name }}</div>
                        <div class="entity-changes">
                          <router-link :to="{ name: 'Characters', hash: '#' + entity.id }">
                            View changes
                          </router-link>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- NPCs -->
                  <div v-if="getSessionEntitiesByType(session.id, 'npc').length > 0" class="entity-type-group">
                    <h5>NPCs</h5>
                    <div class="session-entity-grid">
                      <div v-for="entity in getSessionEntitiesByType(session.id, 'npc')" 
                           :key="entity.id"
                           class="session-entity-card">
                        <div class="entity-name">{{ entity.entity.name }}</div>
                        <div class="entity-changes">
                          <router-link :to="{ name: 'NPCs', hash: '#' + entity.id }">
                            View changes
                          </router-link>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Locations -->
                  <div v-if="getSessionEntitiesByType(session.id, 'location').length > 0" class="entity-type-group">
                    <h5>Locations</h5>
                    <div class="session-entity-grid">
                      <div v-for="entity in getSessionEntitiesByType(session.id, 'location')" 
                           :key="entity.id"
                           class="session-entity-card">
                        <div class="entity-name">{{ entity.entity.name }}</div>
                        <div class="entity-changes">
                          <router-link :to="{ name: 'Locations', hash: '#' + entity.id }">
                            View changes
                          </router-link>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Items -->
                  <div v-if="getSessionEntitiesByType(session.id, 'item').length > 0" class="entity-type-group">
                    <h5>Items</h5>
                    <div class="session-entity-grid">
                      <div v-for="entity in getSessionEntitiesByType(session.id, 'item')" 
                           :key="entity.id"
                           class="session-entity-card">
                        <div class="entity-name">{{ entity.entity.name }}</div>
                        <div class="entity-changes">
                          <router-link :to="{ name: 'Items', hash: '#' + entity.id }">
                            View changes
                          </router-link>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- History -->
                  <div v-if="getSessionEntitiesByType(session.id, 'history').length > 0" class="entity-type-group">
                    <h5>History</h5>
                    <div class="session-entity-grid">
                      <div v-for="entity in getSessionEntitiesByType(session.id, 'history')" 
                           :key="entity.id"
                           class="session-entity-card">
                        <div class="entity-name">{{ getHistoryEraName(entity.id) }}</div>
                        <div class="entity-changes">
                          <router-link :to="{ name: 'History' }">
                            View changes
                          </router-link>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getSessionEntities, worldHistory } from '../store/worldData';

export default {
  name: 'SessionsView',
  data() {
    return {
      sessions: [],
      openEntityChanges: {}
    };
  },
  methods: {
    toggleEntityChanges(sessionId) {
      this.openEntityChanges[sessionId] = !this.isEntityChangesOpen(sessionId);
    },
    isEntityChangesOpen(sessionId) {
      return !!this.openEntityChanges[sessionId];
    },
    getSessionEntitiesData(sessionId) {
      return getSessionEntities(sessionId);
    },
    getSessionEntitiesByType(sessionId, type) {
      return this.getSessionEntitiesData(sessionId).filter(entity => entity.type === type);
    },
    getHistoryEraName(eraId) {
      const era = worldHistory.eras.find(e => e.id === eraId);
      return era ? era.name : eraId;
    }
  },
  created() {
    // Import dynamically to ensure the component gets the latest data
    import('../store/worldData')
      .then(module => {
        this.sessions = module.sessions;
      });
  }
};
</script>

<style scoped>
.section-intro {
  text-align: center;
  max-width: 800px;
  margin: 0 auto 2em;
}

.sessions-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.session-card {
  background: var(--gradient-primary);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.session-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border-accent);
}

.header-top-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.session-title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.4rem;
  line-height: 1.2;
  display: inline-block;
}

.session-subtitle {
  margin: 0.25rem 0 0;
  font-size: 0.95rem;
  color: var(--text-muted, #aaa);
  font-style: italic;
  width: 100%;
}

.session-date {
  font-family: var(--font-accent);
  font-size: 0.9em;
  font-weight: bold;
  padding: 0.3em 0.6em;
  border-radius: 4px;
  background-color: rgba(100, 100, 100, 0.2);
  white-space: nowrap;
}

.session-content {
  padding: 1.5rem;
}

.upcoming-message {
  font-style: italic;
  border-left: 3px solid var(--color-primary);
  padding-left: 1rem;
}

.upcoming .session-header {
  background-color: rgba(65, 105, 225, 0.1);
}

.highlights {
  margin-top: 1.5rem;
}

.highlights h4 {
  margin-bottom: 0.5rem;
  color: var(--color-primary);
}

.highlights ul {
  padding-left: 1.5rem;
}

.highlights li {
  margin-bottom: 0.5rem;
}

/* Session affected entities styling */
.session-affected-entities {
  margin-top: 2rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: 1rem;
}

.affected-entities-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  margin-bottom: 1rem;
}

.affected-entities-header h4 {
  margin: 0;
  color: var(--color-primary);
  font-size: 1.1rem;
}

.toggle-icon {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  transition: transform 0.3s ease;
}

.affected-entities-content {
  padding: 0.5rem 0;
}

.entity-type-group {
  margin-bottom: 1.5rem;
}

.entity-type-group h5 {
  margin: 0 0 0.75rem 0;
  font-size: 1rem;
  border-bottom: 1px dashed rgba(255, 255, 255, 0.1);
  padding-bottom: 0.3rem;
}

.session-entity-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.75rem;
}

.session-entity-card {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  padding: 0.5rem 0.75rem;
  transition: all 0.2s ease;
}

.session-entity-card:hover {
  background: rgba(0, 0, 0, 0.3);
}

.entity-name {
  font-weight: bold;
  margin-bottom: 0.3rem;
  font-size: 0.9rem;
}

.entity-changes {
  font-size: 0.8rem;
}

.entity-changes a {
  color: var(--color-primary);
  text-decoration: none;
}

.entity-changes a:hover {
  text-decoration: underline;
}

@media (max-width: 600px) {
  .header-top-line {
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  
  .session-date {
    align-self: flex-start;
  }
  
  .session-subtitle {
    margin-top: 0.5rem;
  }
  
  .session-entity-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  }
}
</style>

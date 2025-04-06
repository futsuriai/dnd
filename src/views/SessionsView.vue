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
            
            <div v-if="session.highlights && session.highlights.length > 0" class="highlights">
              <h4>Key Moments:</h4>
              <ul>
                <li v-for="(highlight, i) in session.highlights" :key="i">
                  {{ highlight }}
                </li>
              </ul>
            </div>
            
            <!-- Session history timeline section -->
            <div v-if="!session.upcoming" class="session-history">
              <div class="history-header" @click="toggleHistory(session.id)">
                <h4>Session History</h4>
                <span class="toggle-icon">{{ isHistoryOpen(session.id) ? '▼' : '▶' }}</span>
              </div>
              
              <div v-show="isHistoryOpen(session.id)" class="history-content">
                <div v-if="getSessionHistoryEvents(session.id).length === 0" class="no-history">
                  <p>No detailed history available for this session.</p>
                </div>
                <div v-else class="history-timeline">
                  <div v-for="(event, index) in getSessionHistoryEvents(session.id)" 
                       :key="index" 
                       class="history-item" 
                       :class="event.type">
                    <div class="history-timestamp">{{ formatTimestamp(event.timestamp) }}</div>
                    <div class="history-content">
                      <span v-html="formatHistoryEvent(event)"></span>
                    </div>
                  </div>
                </div>
              </div>
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
import { getSessionEntities, getAllSessions, worldHistory, getAllSessionRelatedEvents, getEntityTypeFromId } from '../store/worldData';

export default {
  name: 'SessionsView',
  data() {
    return {
      sessions: [],
      sessionEntitiesCache: {}, // Cache for session entities to avoid repeated calls
      sessionHistoryCache: {}, // Cache for session history events
      openEntityChanges: {},
      openHistorySections: {} // Track which history sections are open
    };
  },
  methods: {
    toggleEntityChanges(sessionId) {
      this.openEntityChanges[sessionId] = !this.isEntityChangesOpen(sessionId);
    },
    isEntityChangesOpen(sessionId) {
      return !!this.openEntityChanges[sessionId];
    },
    toggleHistory(sessionId) {
      this.openHistorySections[sessionId] = !this.isHistoryOpen(sessionId);
    },
    isHistoryOpen(sessionId) {
      return !!this.openHistorySections[sessionId];
    },
    async getSessionEntitiesData(sessionId) {
      // Use cache if available to improve performance
      if (!this.sessionEntitiesCache[sessionId]) {
        this.sessionEntitiesCache[sessionId] = await getSessionEntities(sessionId);
      }
      return this.sessionEntitiesCache[sessionId] || [];
    },
    getSessionEntitiesByType(sessionId, type) {
      const entities = this.sessionEntitiesCache[sessionId] || [];
      return entities.filter(entity => entity.type === type);
    },
    getHistoryEraName(eraId) {
      const era = worldHistory.eras.find(e => e.id === eraId);
      return era ? era.name : eraId;
    },
    // Helper method to preload session entities data
    async preloadSessionEntities() {
      for (const session of this.sessions) {
        if (!session.upcoming) {
          await this.getSessionEntitiesData(session.id);
          this.getSessionHistoryEvents(session.id); // Also preload history
        }
      }
    },
    // Get and format session history events
    getSessionHistoryEvents(sessionId) {
      if (!this.sessionHistoryCache[sessionId]) {
        const events = getAllSessionRelatedEvents(sessionId);
        
        // Transform events to a more UI-friendly format
        this.sessionHistoryCache[sessionId] = events.map(event => {
          let description = '';
          let type = event.changeType || 'generic';
          
          // Format based on event type
          if (event.changeType === 'creation') {
            const entityName = event.data.name || event.entityId;
            const entityType = event.data.entityType || 'entity';
            description = `Created new ${entityType}: <strong>${entityName}</strong>`;
          } 
          else if (event.changeType === 'update') {
            const entityType = event.data.entityType || this.getEntityTypeById(event.entityId);
            const entityName = event.data.name || this.getEntityNameById(event.entityId, entityType);
            
            if (event.data.last_action) {
              description = event.data.last_action;
            } else if (event.data.status) {
              description = `${entityName} status changed to: ${event.data.status}`;
            } else {
              description = `Updated ${entityType}: ${entityName}`;
            }
          }
          else if (event.changeType === 'connection_added') {
            const sourceType = this.getEntityTypeById(event.entityId);
            const sourceName = this.getEntityNameById(event.entityId, sourceType);
            const targetType = event.data.connectedEntityType;
            const targetName = this.getEntityNameById(event.data.connectedEntityId, targetType);
            
            description = `Connected <strong>${sourceName}</strong> to <strong>${targetName}</strong>: ${event.data.reason}`;
          }
          else if (event.changeType.includes('connection')) {
            const sourceType = this.getEntityTypeById(event.entityId);
            const sourceName = this.getEntityNameById(event.entityId, sourceType);
            const targetType = event.data.connectedEntityType;
            const targetName = this.getEntityNameById(event.data.connectedEntityId, targetType);
            
            if (event.changeType === 'connection_removed') {
              description = `Removed connection between <strong>${sourceName}</strong> and <strong>${targetName}</strong>`;
            } else {
              description = `Updated connection between <strong>${sourceName}</strong> and <strong>${targetName}</strong>: ${event.data.reason}`;
            }
          }
          
          return {
            type: type.split('_')[0], // Simplify type for CSS
            description: description, 
            timestamp: event.timestamp,
            sourceEvent: event
          };
        }).sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp)); // Sort chronologically
      }
      
      return this.sessionHistoryCache[sessionId] || [];
    },
    // Format the timestamp for display
    formatTimestamp(timestamp) {
      if (!timestamp) return '';
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    },
    // Format history event with links
    formatHistoryEvent(event) {
      // Already has HTML, just return the description
      return event.description;
    },
    // Helper to get entity type by ID
    getEntityTypeById(entityId) {
      // This is a simplified version - ideally we'd use the existing function
      const entityInfo = Object.values(this.sessionEntitiesCache)
        .flat()
        .find(e => e.id === entityId);
      
      return entityInfo ? entityInfo.type : 'entity';
    },
    // Helper to get entity name by ID and type
    getEntityNameById(entityId, entityType) {
      const entityInfo = Object.values(this.sessionEntitiesCache)
        .flat()
        .find(e => e.id === entityId && e.type === entityType);
      
      return entityInfo && entityInfo.entity ? entityInfo.entity.name : entityId;
    }
  },
  created() {
    // Load sessions synchronously since getAllSessions doesn't return a Promise
    this.sessions = getAllSessions();
    
    // After sessions are loaded, preload session entities data
    this.$nextTick(async () => {
      await this.preloadSessionEntities();
      // Force a re-render after data is loaded
      this.$forceUpdate();
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

/* New Session History Timeline Styling */
.session-history {
  margin-top: 2rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: 1rem;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  margin-bottom: 1rem;
}

.history-header h4 {
  margin: 0;
  color: var(--color-primary);
  font-size: 1.1rem;
}

.history-content {
  padding: 0.5rem 0;
}

.history-timeline {
  position: relative;
  margin-left: 1rem;
  padding-left: 2rem;
  border-left: 2px solid rgba(255, 255, 255, 0.1);
}

.history-item {
  position: relative;
  margin-bottom: 1.5rem;
  padding-bottom: 0.5rem;
}

.history-item::before {
  content: '';
  position: absolute;
  left: -2.25rem;
  top: 0.25rem;
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 50%;
  background-color: var(--color-secondary, #666);
}

.history-item.creation::before {
  background-color: #4CAF50;
}

.history-item.update::before {
  background-color: #2196F3;
}

.history-item.connection::before {
  background-color: #FF9800;
}

.history-timestamp {
  font-size: 0.8rem;
  color: var(--text-muted, #aaa);
  margin-bottom: 0.25rem;
}

.history-content {
  font-size: 0.95rem;
  line-height: 1.4;
}

.history-content strong {
  color: var(--color-accent, #f0f0f0);
}

.no-history {
  font-style: italic;
  color: var(--text-muted, #aaa);
}
</style>

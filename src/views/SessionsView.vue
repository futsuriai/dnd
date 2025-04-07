<template>
  <div class="content-section">
    <div class="sessions-container">
      <div v-if="loading" class="loading-indicator">
        <div class="spinner"></div>
        <p>Loading sessions...</p>
      </div>
      
      <div v-else-if="error" class="error-message">
        <p>{{ error }}</p>
      </div>
      
      <div v-else>
        <div v-for="session in sessions" :key="session.id" class="session-card" :id="session.id">
          <div class="session-header">
            <h3 class="session-title">{{ session.title }}</h3>
            <div class="session-date">{{ session.date }}</div>
            <div v-if="session.subtitle" class="session-subtitle">{{ session.subtitle }}</div>
          </div>
          
          <div class="session-content">
            <div v-if="session.upcoming" class="session-upcoming">
              <div class="upcoming-badge">Upcoming</div>
              <div class="session-description">{{ session.description || session.summary }}</div>
            </div>
            
            <div v-else class="session-summary">
              <div class="session-description">{{ session.description || session.summary }}</div>
              
              <div v-if="session.highlights && session.highlights.length > 0" class="session-highlights">
                <h4>Highlights</h4>
                <ul>
                  <li v-for="(highlight, index) in session.highlights" :key="index">{{ highlight }}</li>
                </ul>
              </div>
              
              <div v-if="!session.upcoming" class="session-history">
                <div class="history-header" @click="toggleHistory(session.id)">
                  <h4>Session History</h4>
                  <span class="toggle-icon">{{ isHistoryOpen(session.id) ? '▼' : '▶' }}</span>
                </div>
                
                <div v-show="isHistoryOpen(session.id)" class="history-content">
                  <div v-if="getSessionHistoryEvents(session.id).length === 0" class="no-history">
                    No history events recorded for this session.
                  </div>
                  
                  <div v-else class="history-timeline">
                    <div v-for="(event, index) in getSessionHistoryEvents(session.id)" 
                         :key="index"
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
                          <div class="entity-name">{{ entity.entity?.name || 'Unknown Entity' }}</div>
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
                          <div class="entity-name">{{ entity.entity?.name || 'Unknown Entity' }}</div>
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
                          <div class="entity-name">{{ entity.entity?.name || 'Unknown Entity' }}</div>
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
                          <div class="entity-name">{{ entity.entity?.name || 'Unknown Entity' }}</div>
                          <div class="entity-changes">
                            <router-link :to="{ name: 'Items', hash: '#' + entity.id }">
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
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, computed } from 'vue';
import worldData, { Session, SessionEntity, Entity } from '../store/worldData';
import firestoreService from '../services/FirestoreService';

interface OpenSections {
  history: Record<string, boolean>;
  entityChanges: Record<string, boolean>;
}

interface HistoryEvent {
  type: string;
  description: string;
  timestamp: string;
  entityType?: string;
  changes?: any;
}

export default defineComponent({
  name: 'SessionsView',
  
  setup() {
    const sessions = ref<Session[]>([]);
    const loading = ref<boolean>(true);
    const error = ref<string | null>(null);
    const openSections = ref<OpenSections>({
      history: {},
      entityChanges: {}
    });
    const sessionEntities = ref<Record<string, SessionEntity[]>>({});
    
    // Get sessions when component is mounted
    onMounted(async () => {
      await loadSessions();
    });
    
    // Load sessions with Firestore first, fallback to local data
    async function loadSessions(): Promise<void> {
      loading.value = true;
      error.value = null;
      
      try {
        // Initialize worldData to determine data source
        const dataSource = await worldData.initWorldData();
        console.log(`Using data source: ${dataSource}`);
        
        // Get all sessions using worldData adapter
        sessions.value = await worldData.getAllSessions();
        
        // Sort sessions by date, newest first
        sessions.value.sort((a, b) => {
          // Convert dates to timestamp for comparison
          const dateA = new Date(a.date).getTime();
          const dateB = new Date(b.date).getTime();
          // Sort in descending order (newest first)
          return dateB - dateA;
        });
        
        // Pre-load affected entities for each session
        for (const session of sessions.value) {
          await loadSessionEntities(session.id);
        }
      } catch (err: any) {
        console.error('Error loading sessions:', err);
        error.value = `Error loading sessions: ${err.message}`;
      } finally {
        loading.value = false;
      }
    }
    
    // Load entities affected by a session
    async function loadSessionEntities(sessionId: string): Promise<void> {
      if (!sessionEntities.value[sessionId]) {
        try {
          const entities = await worldData.getSessionEntities(sessionId);
          sessionEntities.value[sessionId] = entities;
        } catch (err) {
          console.error(`Error loading entities for session ${sessionId}:`, err);
          sessionEntities.value[sessionId] = [];
        }
      }
    }
    
    // Get entities affected by a session
    function getSessionEntitiesData(sessionId: string): SessionEntity[] {
      return sessionEntities.value[sessionId] || [];
    }
    
    // Get entities of a specific type for a session
    function getSessionEntitiesByType(sessionId: string, entityType: string): SessionEntity[] {
      const entities = getSessionEntitiesData(sessionId);
      return entities.filter(entity => entity.type === entityType);
    }
    
    // Get history events for a session
    function getSessionHistoryEvents(sessionId: string): HistoryEvent[] {
      const session = sessions.value.find(s => s.id === sessionId);
      return session && session.events ? session.events : [];
    }
    
    // Toggle history visibility
    function toggleHistory(sessionId: string): void {
      openSections.value.history[sessionId] = !openSections.value.history[sessionId];
    }
    
    // Check if history is open
    function isHistoryOpen(sessionId: string): boolean {
      return !!openSections.value.history[sessionId];
    }
    
    // Toggle entity changes visibility
    function toggleEntityChanges(sessionId: string): void {
      openSections.value.entityChanges[sessionId] = !openSections.value.entityChanges[sessionId];
    }
    
    // Check if entity changes are open
    function isEntityChangesOpen(sessionId: string): boolean {
      return !!openSections.value.entityChanges[sessionId];
    }
    
    // Format timestamp for display
    function formatTimestamp(timestamp: string): string {
      if (!timestamp) return '';
      
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    // Format history event for display with HTML
    function formatHistoryEvent(event: HistoryEvent): string {
      if (!event) return '';
      
      // If event has a pre-formatted description, use it
      if (event.description) {
        return `<strong>${event.type.toUpperCase()}:</strong> ${event.description}`;
      }
      
      // Otherwise, create a generic description based on type
      let html = `<strong>${event.type.toUpperCase()}:</strong> `;
      
      switch (event.type) {
        case 'creation':
          html += `Created new ${event.entityType || 'entity'}`;
          break;
        case 'update':
          html += `Updated ${event.entityType || 'entity'} properties`;
          break;
        case 'connection':
          html += `Connected to another entity`;
          break;
        default:
          html += `Event recorded`;
      }
      
      return html;
    }
    
    return {
      sessions,
      loading,
      error,
      toggleHistory,
      isHistoryOpen,
      toggleEntityChanges,
      isEntityChangesOpen,
      getSessionHistoryEvents,
      getSessionEntitiesData,
      getSessionEntitiesByType,
      formatTimestamp,
      formatHistoryEvent
    };
  }
});
</script>

<style scoped>
.content-section {
  padding: 20px;
}

.sessions-container {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.session-card {
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease;
}

.session-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
}

.session-header {
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.session-title {
  margin: 0 0 5px 0;
  font-size: 1.8rem;
}

.session-subtitle {
  font-style: italic;
  margin-top: 5px;
  opacity: 0.8;
}

.session-date {
  opacity: 0.7;
  font-size: 0.9rem;
}

.session-description {
  margin-bottom: 20px;
  line-height: 1.6;
}

.upcoming-badge {
  display: inline-block;
  background-color: #4CAF50;
  color: white;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 0.8rem;
  margin-bottom: 10px;
}

.session-highlights {
  margin-top: 20px;
  padding: 15px;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
}

.session-highlights h4 {
  margin-top: 0;
  margin-bottom: 10px;
}

.session-highlights ul {
  margin: 0;
  padding-left: 20px;
}

.session-highlights li {
  margin-bottom: 5px;
  line-height: 1.5;
}

/* Session history section */
.session-history {
  margin-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: 15px;
}

.history-header, .affected-entities-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  padding: 5px 0;
}

.history-header h4, .affected-entities-header h4 {
  margin: 0;
}

.toggle-icon {
  font-size: 0.8rem;
}

.history-content {
  margin-top: 10px;
  padding: 10px;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
}

.history-timeline {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.history-timestamp {
  font-size: 0.8rem;
  opacity: 0.7;
  margin-bottom: 2px;
}

/* Entity types (for styling different event types) */
.creation {
  background-color: rgba(76, 175, 80, 0.1);
  padding: 10px;
  border-radius: 4px;
  border-left: 3px solid #4CAF50;
}

.update {
  background-color: rgba(33, 150, 243, 0.1);
  padding: 10px;
  border-radius: 4px;
  border-left: 3px solid #2196F3;
}

.connection {
  background-color: rgba(156, 39, 176, 0.1);
  padding: 10px;
  border-radius: 4px;
  border-left: 3px solid #9C27B0;
}

/* Session entities section */
.session-affected-entities {
  margin-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: 15px;
}

.affected-entities-content {
  margin-top: 10px;
}

.entity-type-group {
  margin-bottom: 20px;
}

.entity-type-group h5 {
  margin: 0 0 10px 0;
  font-weight: 600;
}

.session-entity-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
}

.session-entity-card {
  background-color: rgba(0, 0, 0, 0.1);
  padding: 10px;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.entity-name {
  font-weight: 500;
}

.entity-changes a {
  color: #2196F3;
  text-decoration: none;
  font-size: 0.8rem;
}

.entity-changes a:hover {
  text-decoration: underline;
}

.no-history {
  padding: 10px;
  text-align: center;
  opacity: 0.7;
  font-style: italic;
}

/* Loading and error states */
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
  .session-entity-grid {
    grid-template-columns: 1fr;
  }
}
</style>

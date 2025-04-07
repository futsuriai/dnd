<template>
  <div class="entity-history-viewer">
    <div v-if="isLoading" class="loading">
      Loading history...
    </div>
    
    <div v-else-if="errorMessage" class="error-message">
      {{ errorMessage }}
    </div>
    
    <div v-else>
      <!-- Session selector -->
      <div class="session-filter">
        <label for="session-filter">View entity as of session:</label>
        <select 
          id="session-filter" 
          v-model="selectedSessionId"
          class="form-control"
          @change="loadEntityAtSession"
        >
          <option value="">Current state (all sessions)</option>
          <option v-for="session in sessions" :key="session.id" :value="session.id">
            {{ session.title }} ({{ formatDate(session.date) }})
          </option>
        </select>
      </div>
      
      <!-- Entity details -->
      <div v-if="entity" class="entity-details">
        <h3>{{ entity.name }}</h3>
        
        <!-- Different fields based on entity type -->
        <div v-if="entity.entityType === 'character'" class="character-details">
          <div class="detail-row">
            <div class="detail-label">Player</div>
            <div class="detail-value">{{ entity.player || 'N/A' }}</div>
          </div>
          
          <div class="detail-row">
            <div class="detail-label">Race</div>
            <div class="detail-value">{{ entity.race || 'N/A' }}</div>
          </div>
          
          <div class="detail-row">
            <div class="detail-label">Class</div>
            <div class="detail-value">{{ entity.class || 'N/A' }}</div>
          </div>
          
          <div class="detail-row">
            <div class="detail-label">Level</div>
            <div class="detail-value">{{ entity.level || 'N/A' }}</div>
          </div>
          
          <div class="detail-row">
            <div class="detail-label">Background</div>
            <div class="detail-value">{{ entity.background || 'N/A' }}</div>
          </div>
          
          <div v-if="entity.bio" class="biography">
            <div class="detail-label">Biography</div>
            <div class="detail-value">{{ entity.bio }}</div>
          </div>
        </div>
        
        <!-- For NPCs -->
        <div v-else-if="entity.entityType === 'npc'" class="npc-details">
          <!-- Similar structure for NPC specific fields -->
        </div>
        
        <!-- For Locations -->
        <div v-else-if="entity.entityType === 'location'" class="location-details">
          <!-- Location specific fields -->
        </div>
        
        <!-- For Items -->
        <div v-else-if="entity.entityType === 'item'" class="item-details">
          <!-- Item specific fields -->
        </div>
        
        <!-- Show point-in-time notice if viewing historical entity -->
        <div v-if="selectedSessionId" class="point-in-time-notice">
          <p>
            Viewing entity as it appeared after 
            <strong>{{ getSessionTitle(selectedSessionId) }}</strong>
          </p>
        </div>
      </div>
      
      <!-- History timeline -->
      <div class="history-timeline">
        <h4>History</h4>
        
        <div v-if="historyEntries && historyEntries.length > 0" class="history-entries">
          <div 
            v-for="entry in historyEntries" 
            :key="entry.timestamp"
            class="history-entry"
          >
            <div class="entry-header">
              <span class="session-name">{{ getSessionTitle(entry.sessionId) }}</span>
              <span class="entry-date">({{ formatDate(getSessionDate(entry.sessionId)) }})</span>
            </div>
            
            <div class="entry-content">
              <div class="entry-icon" :class="entry.changeType">
                <i v-if="entry.changeType === 'creation'" class="event-icon-creation">+</i>
                <i v-else-if="entry.changeType === 'update'" class="event-icon-update">↻</i>
                <i v-else-if="entry.changeType === 'deletion'" class="event-icon-deletion">×</i>
                <i v-else class="event-icon-generic">•</i>
              </div>
              <div class="entry-details">
                <div class="entry-description">
                  {{ getEntryDescription(entry) }}
                </div>
                <div class="entry-timestamp">{{ formatTime(entry.timestamp) }}</div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-else class="no-history">
          No history events found for this entity.
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { ref, onMounted, watch, defineComponent } from 'vue';
import worldData from '../store/worldData';
import { Entity, HistoryEntry, Session, SessionHistory } from '../store/worldData';

export default defineComponent({
  name: 'EntityHistoryViewer',
  props: {
    entityType: {
      type: String,
      required: true
    },
    entityId: {
      type: String,
      required: true
    }
  },
  setup(props) {
    const entity = ref<Entity | null>(null);
    const sessions = ref<Session[]>([]);
    const historyEntries = ref<HistoryEntry[]>([]);
    const selectedSessionId = ref<string>('');
    const isLoading = ref<boolean>(true);
    const errorMessage = ref<string>('');
    const sessionCache = ref<Record<string, Session>>({});
    
    // Load all sessions for the filter dropdown
    const loadSessions = async (): Promise<void> => {
      try {
        // Get all real sessions
        sessions.value = await worldData.getAllSessions();
        
        // Sort sessions chronologically
        sessions.value.sort((a, b) => {
          // Extract session numbers for proper sorting
          const aNum = parseInt(a.id.split('-')[1]) || 0;
          const bNum = parseInt(b.id.split('-')[1]) || 0;
          
          // Sort sessions by ID (ascending)
          return aNum - bNum;
        });
      } catch (error) {
        console.error('Error loading sessions:', error);
        errorMessage.value = 'Failed to load sessions.';
      }
    };
    
    // Load entity with full history
    const loadEntity = async (): Promise<void> => {
      try {
        isLoading.value = true;
        errorMessage.value = '';
        
        // Get entity with full history
        entity.value = await worldData.buildEntityFromHistory(
          props.entityType,
          props.entityId
        );
        
        if (!entity.value) {
          errorMessage.value = 'Entity not found or has been deleted.';
          return;
        }
        
        // Load history entries for this entity
        const entries = await worldData.getEntityEvents(
          props.entityType,
          props.entityId
        );
        
        // Sort entries chronologically
        historyEntries.value = entries.sort((a, b) => {
          // First sort by session ID
          const aSession = parseInt(a.sessionId.split('-')[1]) || 0;
          const bSession = parseInt(b.sessionId.split('-')[1]) || 0;
          
          if (aSession !== bSession) return bSession - aSession;
          
          // Then by timestamp if in the same session
          return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
        });
      } catch (error) {
        console.error('Error loading entity history:', error);
        errorMessage.value = 'Failed to load entity history.';
      } finally {
        isLoading.value = false;
      }
    };
    
    // Load entity as it was at a specific session
    const loadEntityAtSession = async (): Promise<void> => {
      try {
        if (!selectedSessionId.value) {
          // If no session selected, load current state
          await loadEntity();
          return;
        }
        
        isLoading.value = true;
        errorMessage.value = '';
        
        // Get entity as it was at the selected session
        entity.value = await worldData.getEntityAtSession(
          props.entityType,
          props.entityId,
          selectedSessionId.value
        );
        
        if (!entity.value) {
          errorMessage.value = 'Entity not found at this point in time.';
        }
        
        // Update history entries to only show those up to the selected session
        const entries = await worldData.getEntityEvents(
          props.entityType,
          props.entityId
        );
        
        // Filter entries up to the selected session
        historyEntries.value = entries
          .filter(entry => {
            const entrySessionNum = parseInt(entry.sessionId.split('-')[1]) || 0;
            const selectedSessionNum = parseInt(selectedSessionId.value.split('-')[1]) || 0;
            return entrySessionNum <= selectedSessionNum;
          })
          .sort((a, b) => {
            // First sort by session ID
            const aSession = parseInt(a.sessionId.split('-')[1]) || 0;
            const bSession = parseInt(b.sessionId.split('-')[1]) || 0;
            
            if (aSession !== bSession) return bSession - aSession;
            
            // Then by timestamp if in the same session
            return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
          });
      } catch (error) {
        console.error('Error loading entity at session:', error);
        errorMessage.value = 'Failed to load entity at selected session.';
      } finally {
        isLoading.value = false;
      }
    };
    
    // Format a date string for display
    const formatDate = (dateString: string | undefined): string => {
      if (!dateString) return 'Unknown date';
      
      try {
        const date = new Date(dateString);
        return date.toLocaleDateString(undefined, {
          year: 'numeric',
          month: 'short',
          day: 'numeric'
        });
      } catch (e) {
        return dateString; // Fallback to original string
      }
    };
    
    // Format a timestamp for display
    const formatTime = (timestamp: string | undefined): string => {
      if (!timestamp) return '';
      
      try {
        const date = new Date(timestamp);
        return date.toLocaleTimeString(undefined, {
          hour: '2-digit',
          minute: '2-digit'
        });
      } catch (e) {
        return '';
      }
    };
    
    // Get session title by ID
    const getSessionTitle = (sessionId: string | undefined): string => {
      if (!sessionId) return 'Unknown Session';
      
      // Handle special admin session case
      if (sessionId === 'session-admin') {
        return 'Admin Session';
      }
      
      const session = sessions.value.find(s => s.id === sessionId);
      return session ? session.title : sessionId.replace('session-', 'Session ');
    };
    
    // Get session date by ID
    const getSessionDate = (sessionId: string | undefined): string => {
      if (!sessionId) return '';
      
      // Handle special admin session case
      if (sessionId === 'session-admin') {
        return new Date().toISOString().split('T')[0]; // Today's date
      }
      
      const session = sessions.value.find(s => s.id === sessionId);
      return session ? session.date : '';
    };
    
    // Get human-readable description for a history entry
    const getEntryDescription = (entry: HistoryEntry): string => {
      if (!entry) return '';
      
      switch (entry.changeType) {
        case 'creation':
          return `${capitalizeFirst(props.entityType)} was created`;
        case 'update':
          // Check if there's a custom action description
          if (entry.data && entry.data.last_action) {
            return entry.data.last_action;
          }
          return `${capitalizeFirst(props.entityType)} was updated`;
        case 'deletion':
          return `${capitalizeFirst(props.entityType)} was deleted`;
        case 'connection_added':
          return `Connected to ${entry.data.connectedEntityType} ${entry.data.connectedEntityId}`;
        case 'connection_removed':
          return `Connection removed`;
        default:
          return entry.changeType;
      }
    };
    
    // Utility function to capitalize first letter
    const capitalizeFirst = (str: string): string => {
      if (!str) return '';
      return str.charAt(0).toUpperCase() + str.slice(1);
    };
    
    // Load data on mount
    onMounted(async () => {
      await loadSessions();
      await loadEntity();
    });
    
    // Watch for prop changes to reload data
    watch([() => props.entityType, () => props.entityId], async () => {
      selectedSessionId.value = ''; // Reset session filter
      await loadEntity();
    });
    
    return {
      entity,
      sessions,
      historyEntries,
      selectedSessionId,
      isLoading,
      errorMessage,
      loadEntityAtSession,
      formatDate,
      formatTime,
      getSessionTitle,
      getSessionDate,
      getEntryDescription,
      capitalizeFirst
    };
  }
});
</script>

<style scoped>
.entity-history-viewer {
  width: 100%;
  color: #e0e0e0;
}

.loading, .error-message, .no-history {
  padding: 20px;
  text-align: center;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  margin: 20px 0;
}

.error-message {
  color: #ff6b6b;
}

.session-filter {
  margin-bottom: 20px;
}

.form-control {
  width: 100%;
  padding: 10px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #fff;
  border-radius: 4px;
  margin-top: 8px;
}

.entity-details {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  padding: 20px;
  margin-bottom: 20px;
}

.detail-row {
  display: flex;
  margin-bottom: 10px;
}

.detail-label {
  font-weight: bold;
  width: 120px;
  flex-shrink: 0;
}

.detail-value {
  flex-grow: 1;
}

.biography {
  margin-top: 20px;
}

.biography .detail-label {
  margin-bottom: 8px;
}

.biography .detail-value {
  white-space: pre-line;
  line-height: 1.5;
}

.point-in-time-notice {
  margin-top: 20px;
  padding: 10px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 4px;
  border-left: 4px solid #ffab40;
}

.history-timeline {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  padding: 20px;
}

.history-entries {
  border-left: 2px solid rgba(255, 255, 255, 0.1);
  margin-left: 10px;
  padding-left: 25px;
}

.history-entry {
  margin-bottom: 20px;
  position: relative;
}

.history-entry:last-child {
  margin-bottom: 0;
}

.entry-header {
  margin-bottom: 8px;
  font-weight: 500;
}

.session-name {
  font-size: 1.05rem;
}

.entry-date {
  opacity: 0.7;
  font-size: 0.9rem;
  margin-left: 5px;
}

.entry-content {
  display: flex;
  position: relative;
}

.entry-icon {
  position: absolute;
  left: -35px;
  width: 20px;
  height: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 50%;
  background: #242424;
  font-size: 14px;
  font-weight: bold;
}

.entry-icon.creation i {
  color: #4CAF50;
}

.entry-icon.update i {
  color: #2196F3;
}

.entry-icon.deletion i {
  color: #F44336;
}

.event-icon-creation, .event-icon-update, .event-icon-deletion, .event-icon-generic {
  display: inline-block;
}

.entry-details {
  flex-grow: 1;
}

.entry-description {
  line-height: 1.4;
}

.entry-timestamp {
  font-size: 0.8rem;
  opacity: 0.7;
  margin-top: 4px;
}

/* Event type styles */
.history-entry .creation .entry-description {
  color: #a5d6a7;
}

.history-entry .update .entry-description {
  color: #90caf9;
}

.history-entry .deletion .entry-description {
  color: #ef9a9a;
}

.history-entry .connection_added .entry-description,
.history-entry .connection_removed .entry-description,
.history-entry .connection_updated .entry-description {
  color: #ce93d8;
}

@media (max-width: 768px) {
  .detail-row {
    flex-direction: column;
  }
  
  .detail-label {
    width: 100%;
    margin-bottom: 5px;
  }
}
</style>

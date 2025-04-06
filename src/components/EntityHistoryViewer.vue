<template>
  <div class="entity-history-viewer">
    <div class="history-header">
      <h3>{{ entityType.charAt(0).toUpperCase() + entityType.slice(1) }} History</h3>
      
      <div class="session-selector">
        <label for="session-select">View As Of:</label>
        <select id="session-select" v-model="selectedSessionId">
          <option value="current">Current (Latest)</option>
          <option v-for="session in relevantSessions" :key="session.id" :value="session.id">
            {{ session.title }} ({{ formatDate(session.date) }})
          </option>
        </select>
      </div>
    </div>
    
    <div class="history-timeline" v-if="entityHistory.length > 0">
      <div 
        v-for="(historyItem, index) in sortedHistory" 
        :key="index"
        :class="['history-item', historyItem.type]"
      >
        <div class="history-item-header">
          <div class="history-session">
            {{ getSessionTitle(historyItem.sessionId) }}
          </div>
          <div class="history-date">
            {{ formatDateTime(historyItem.timestamp) }}
          </div>
          <div class="history-type">
            {{ capitalizeFirst(historyItem.type) }}
          </div>
        </div>
        
        <div class="history-item-content">
          <div class="history-description">{{ historyItem.description }}</div>
          
          <div class="history-changes" v-if="historyItem.changes && Object.keys(historyItem.changes).length > 0">
            <div v-for="(value, key) in displayableChanges(historyItem.changes)" :key="key" class="change-item">
              <span class="change-key">{{ formatKey(key) }}:</span>
              <span class="change-value">
                {{ formatValue(value) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-else class="no-history">
      <p>No history available for this entity.</p>
    </div>
    
    <!-- Entity Snapshot for selected session -->
    <div class="entity-snapshot" v-if="entitySnapshot">
      <h4>Entity Snapshot as of {{ getSessionTitle(selectedSessionId) }}</h4>
      
      <div class="snapshot-content">
        <div v-for="(value, key) in displayableEntity(entitySnapshot)" :key="key" class="snapshot-item">
          <span class="snapshot-key">{{ formatKey(key) }}:</span>
          <span class="snapshot-value">
            {{ formatValue(value) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue';
import entityStore from '../store/entityStore';

export default {
  name: 'EntityHistoryViewer',
  props: {
    entityType: {
      type: String,
      required: true,
      validator: value => ['character', 'npc', 'location', 'item'].includes(value)
    },
    entityId: {
      type: String,
      required: true
    }
  },
  setup(props) {
    // State
    const selectedSessionId = ref('current');
    const entitySnapshot = ref(null);
    
    // Get the full entity with history
    const entity = computed(() => entityStore.getEntity(props.entityType, props.entityId));
    
    // Entity history
    const entityHistory = computed(() => entity.value?.history || []);
    
    // Get all sessions where this entity was modified
    const relevantSessions = computed(() => {
      const sessionIds = new Set(entityHistory.value.map(h => h.sessionId));
      return entityStore.getAllSessions()
        .filter(s => sessionIds.has(s.id))
        .sort((a, b) => {
          // Sort by session number
          const aNum = parseInt(a.id.split('-')[1]) || 0;
          const bNum = parseInt(b.id.split('-')[1]) || 0;
          return aNum - bNum;
        });
    });
    
    // Sorted history (newest first)
    const sortedHistory = computed(() => {
      return [...entityHistory.value].sort((a, b) => {
        return new Date(b.timestamp) - new Date(a.timestamp);
      });
    });
    
    // Update entity snapshot when session changes
    watch(selectedSessionId, (newSessionId) => {
      if (newSessionId === 'current') {
        entitySnapshot.value = entity.value;
      } else {
        entitySnapshot.value = entityStore.getEntityAtSession(
          props.entityType, 
          props.entityId, 
          newSessionId
        );
      }
    });
    
    // Initialize with current entity
    onMounted(() => {
      entitySnapshot.value = entity.value;
    });
    
    // Helper function to get session title
    function getSessionTitle(sessionId) {
      if (sessionId === 'current') return 'Current';
      
      const session = entityStore.getSession(sessionId);
      if (!session) return sessionId;
      
      return session.title || sessionId;
    }
    
    // Format dates
    function formatDate(dateString) {
      if (!dateString) return '';
      return new Date(dateString).toLocaleDateString();
    }
    
    function formatDateTime(dateTimeString) {
      if (!dateTimeString) return '';
      return new Date(dateTimeString).toLocaleString();
    }
    
    // Capitalize first letter
    function capitalizeFirst(str) {
      if (!str) return '';
      return str.charAt(0).toUpperCase() + str.slice(1);
    }
    
    // Format object key for display
    function formatKey(key) {
      if (!key) return '';
      // Convert camelCase to Title Case
      return key
        .replace(/([A-Z])/g, ' $1')
        .replace(/^./, str => str.toUpperCase());
    }
    
    // Format value for display
    function formatValue(value) {
      if (value === null || value === undefined) return '';
      if (typeof value === 'object') return JSON.stringify(value);
      return value;
    }
    
    // Filter out non-displayable changes
    function displayableChanges(changes) {
      const filtered = {};
      
      Object.entries(changes).forEach(([key, value]) => {
        // Skip certain keys
        if (['id', 'type', 'connections', 'history'].includes(key)) return;
        
        // Skip undefined values
        if (value === undefined) return;
        
        // Skip complex objects but keep arrays and primitive values
        if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
          // For connection changes, we'll show a simplified version
          if (key === 'connection') {
            filtered[key] = `Connected to ${value.entityType} "${value.entityId}" - ${value.reason}`;
          }
          return;
        }
        
        filtered[key] = value;
      });
      
      return filtered;
    }
    
    // Filter entity for display
    function displayableEntity(entity) {
      if (!entity) return {};
      
      const filtered = {};
      
      Object.entries(entity).forEach(([key, value]) => {
        // Skip certain keys
        if (['history', 'connections'].includes(key)) return;
        
        // Skip undefined values
        if (value === undefined) return;
        
        // Skip complex objects but keep arrays and primitive values
        if (typeof value === 'object' && value !== null && !Array.isArray(value)) return;
        
        filtered[key] = value;
      });
      
      return filtered;
    }
    
    return {
      selectedSessionId,
      entity,
      entityHistory,
      entitySnapshot,
      relevantSessions,
      sortedHistory,
      getSessionTitle,
      formatDate,
      formatDateTime,
      capitalizeFirst,
      formatKey,
      formatValue,
      displayableChanges,
      displayableEntity
    };
  }
};
</script>

<style scoped>
.entity-history-viewer {
  margin: 1rem 0;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 6px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.history-header h3 {
  margin: 0;
  color: var(--color-primary);
}

.session-selector {
  display: flex;
  align-items: center;
}

.session-selector label {
  margin-right: 0.5rem;
  font-weight: bold;
}

.session-selector select {
  padding: 0.3rem 0.5rem;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.2);
  color: var(--color-text);
  border: 1px solid var(--border-color);
}

.history-timeline {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.history-item {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  padding: 1rem;
  position: relative;
  border-left: 4px solid var(--color-text-muted);
}

.history-item.create {
  border-left-color: #4caf50; /* green */
}

.history-item.update {
  border-left-color: #2196f3; /* blue */
}

.history-item.connect {
  border-left-color: #ff9800; /* orange */
}

.history-item-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.8rem;
  font-size: 0.9rem;
  color: var(--color-text-muted);
}

.history-session {
  font-weight: bold;
  color: var(--color-primary);
}

.history-type {
  font-style: italic;
}

.history-description {
  margin-bottom: 0.8rem;
  font-weight: bold;
}

.history-changes {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px dashed var(--border-color);
}

.change-item, .snapshot-item {
  display: flex;
  gap: 0.5rem;
}

.change-key, .snapshot-key {
  font-weight: bold;
  color: var(--color-primary);
  min-width: 150px;
}

.change-value, .snapshot-value {
  word-break: break-word;
}

.entity-snapshot {
  margin-top: 2rem;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  border-left: 4px solid var(--color-primary);
}

.entity-snapshot h4 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: var(--color-primary);
}

.snapshot-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.no-history {
  padding: 2rem;
  text-align: center;
  color: var(--color-text-muted);
  font-style: italic;
}

@media (max-width: 768px) {
  .history-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .history-item-header {
    flex-direction: column;
    gap: 0.3rem;
  }
  
  .change-item, .snapshot-item {
    flex-direction: column;
    gap: 0.2rem;
  }
  
  .change-key, .snapshot-key {
    min-width: unset;
  }
}
</style>

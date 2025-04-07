<template>
  <div class="entity-connections" v-if="connections.length" :class="{ 'is-expanded': expanded }">
    <div class="connections-header" @click="toggleConnections">
      <div class="header-content">
        <h4>Connections</h4>
        <div class="connections-preview" v-if="!expanded">
          <span class="preview-text">{{ connectionNamesPreview }}</span>
        </div>
      </div>
      <span class="toggle-icon">{{ expanded ? '▼' : '▶' }}</span>
    </div>
    <div class="connections-list" :class="{ 'expanded': expanded }">
      <div v-for="(connection, index) in connections" 
           :key="index" 
           class="connection-item">
        <div class="connection-header">
          <span class="connection-name" @click="navigateToEntity(connection.entityType, connection.id)">
            {{ connection.name }}
          </span>
          <span class="connection-type">
            ({{ getConnectionTypeIcon(connection.entityType) }})
          </span>
        </div>
        <p class="connection-reason" v-if="connection.reason">
          {{ connection.reason }}
        </p>
        <div class="connection-session" v-if="expanded && connection.sessionId">
          <span class="session-link" @click="navigateToSession(connection.sessionId)">
            Added in: {{ getSessionName(connection.sessionId) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { ref, computed, onMounted, defineComponent, PropType } from 'vue';
import { useRouter } from 'vue-router';
import worldData from '../store/worldData';
import { DisplayConnection } from '../store/worldData';

export default defineComponent({
  name: 'EntityConnections',
  props: {
    entityType: {
      type: String as PropType<string>,
      required: true
    },
    entityId: {
      type: String as PropType<string>,
      required: true
    }
  },
  setup(props) {
    const router = useRouter();
    const connections = ref<DisplayConnection[]>([]);
    const isLoading = ref<boolean>(true);
    const error = ref<string>('');
    const sessionCache = ref<Record<string, any>>({});
    const expanded = ref<boolean>(false);
    
    // Group connections by type for better display
    const connectionsByType = computed(() => {
      const groupedConnections: Record<string, DisplayConnection[]> = {};
      
      connections.value.forEach(conn => {
        if (!groupedConnections[conn.entityType]) {
          groupedConnections[conn.entityType] = [];
        }
        groupedConnections[conn.entityType].push(conn);
      });
      
      // Sort groups for consistent display
      return Object.keys(groupedConnections)
        .sort()
        .reduce((obj: Record<string, DisplayConnection[]>, key) => {
          obj[key] = groupedConnections[key];
          return obj;
        }, {});
    });
    
    // Create a preview of connection names
    const connectionNamesPreview = computed(() => {
      if (connections.value.length === 0) return '';
      
      const names = connections.value.map(conn => conn.name);
      if (names.length <= 3) {
        return names.join(', ');
      }
      return `${names.slice(0, 2).join(', ')} + ${names.length - 2} more`;
    });
    
    // Toggle connections expanded state
    const toggleConnections = () => {
      expanded.value = !expanded.value;
    };
    
    // Navigate to connected entity when clicked
    const navigateToEntity = (entityType: string, id: string): void => {
      router.push({
        name: getTypeName(entityType).toLowerCase(),
        params: { id }
      });
    };
    
    // Navigate to session
    const navigateToSession = (sessionId: string): void => {
      router.push({
        name: 'session',
        params: { id: sessionId }
      });
    };
    
    // Get connection type icon
    const getConnectionTypeIcon = (entityType: string): string => {
      return getConnectionIcon(entityType);
    };
    
    // Get session name
    const getSessionName = async (sessionId: string): Promise<string> => {
      return formatSessionDate(sessionId);
    };
    
    // Get icon for connection type
    const getConnectionIcon = (entityType: string): string => {
      switch (entityType) {
        case 'character':
          return '👤';
        case 'npc':
          return '🧙';
        case 'location':
          return '📍';
        case 'item':
          return '🧰';
        default:
          return '🔗';
      }
    };
    
    // Get human-readable type name
    const getTypeName = (entityType: string): string => {
      return entityType.charAt(0).toUpperCase() + entityType.slice(1) + 's';
    };
    
    // Load connections for this entity
    const loadConnections = async (): Promise<void> => {
      try {
        isLoading.value = true;
        error.value = '';
        
        connections.value = await worldData.getEntityConnections(
          props.entityType,
          props.entityId
        );
      } catch (err) {
        console.error('Error loading connections:', err);
        error.value = 'Failed to load connections.';
      } finally {
        isLoading.value = false;
      }
    };
    
    // Format session date for display
    const formatSessionDate = async (sessionId: string): Promise<string> => {
      // Cached result
      if (sessionCache.value[sessionId]) {
        return sessionCache.value[sessionId];
      }
      
      // Special cases
      if (sessionId === 'session-admin') {
        sessionCache.value[sessionId] = 'Admin Session';
        return 'Admin Session';
      }
      
      try {
        // Get session details
        const session = await worldData.getSession(sessionId);
        if (session) {
          const formattedDate = `Session ${sessionId.split('-')[1]} (${session.date})`;
          sessionCache.value[sessionId] = formattedDate;
          return formattedDate;
        }
        
        // Default if session not found
        return sessionId;
      } catch (error) {
        console.error(`Error getting session ${sessionId}:`, error);
        return sessionId;
      }
    };
    
    // Load data on component mount
    onMounted(() => {
      loadConnections();
    });
    
    return {
      connections,
      isLoading,
      error,
      connectionsByType,
      expanded,
      connectionNamesPreview,
      toggleConnections,
      navigateToEntity,
      navigateToSession,
      getConnectionTypeIcon,
      getSessionName,
      getConnectionIcon,
      getTypeName,
      formatSessionDate
    };
  }
});
</script>

<style scoped>
.entity-connections {
  margin-top: auto; /* Push to the bottom of flex container */
  margin-bottom: 0.5rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(var(--border-color-rgb, 59, 63, 71), 0.5);
  transition: margin 0.3s ease, padding 0.3s ease;
  width: 100%; /* Ensure full width */
  position: relative;
  z-index: 1;
  overflow: hidden;
  box-sizing: border-box; /* Ensure padding is included in width calculation */
}

/* Add specific rule for location cards */
:deep(.location-card) .entity-connections {
  max-height: calc(100% - 1rem);
  margin-bottom: 0;
  padding-bottom: 0.5rem;
}

:deep(.location-section) {
  position: relative;
  overflow: hidden; /* Prevent content from peeking through */
}

/* Ensure location cards stay within their containers */
:deep(.location-section) :deep(.location-card) {
  max-height: 100%;
  overflow: hidden;
  position: relative;
}

.entity-connections.is-expanded {
  margin-top: 1.5rem;
  margin-bottom: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-color);
  z-index: 2; /* Higher z-index when expanded */
}

/* Adjust connections in location context */
:deep(.location-card) .entity-connections.is-expanded {
  margin-bottom: 0.5rem;
}

.connections-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
  padding: 0 0 0.2rem 0;
  font-size: 0.85rem;
}

.header-content {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.entity-connections h4 {
  font-family: var(--font-display);
  color: var(--color-primary);
  margin: 0;
  font-size: 0.9rem;
  opacity: 0.8;
  font-weight: normal;
  display: inline;
}

.is-expanded h4 {
  font-size: 1.1rem;
  opacity: 1;
  font-weight: bold;
}

.connections-preview {
  display: inline;
}

.preview-text {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  font-style: italic;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 180px;
}

.connections-header:hover h4 {
  opacity: 1;
}

.connections-header:hover .preview-text {
  color: var(--color-text);
}

.connections-list {
  max-height: 0;
  overflow: hidden;
  opacity: 0;
  transition: max-height 0.5s cubic-bezier(0, 1, 0, 1), 
              opacity 0.3s ease,
              margin 0.3s ease;
  pointer-events: none;
}

.connections-list.expanded {
  max-height: 1000px; /* Large enough to contain all content */
  opacity: 1;
  margin-top: 0.8rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  transition: max-height 0.5s cubic-bezier(0.5, 0, 1, 0), 
              opacity 0.3s ease,
              margin 0.3s ease;
  pointer-events: auto;
}

.toggle-icon {
  font-size: 0.7rem;
  color: var(--color-text-muted);
  transition: transform 0.3s ease;
  opacity: 0.6;
}

.is-expanded .toggle-icon {
  font-size: 0.8rem;
  opacity: 1;
}

.connections-header:hover .toggle-icon {
  transform: translateY(2px);
  opacity: 1;
}

.connection-item {
  font-size: 0.85rem;
  padding: 0.5rem 0.7rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  transition: all 0.3s ease;
  max-width: 100%;
  transform-origin: top center;
}

.connections-list.expanded .connection-item {
  animation: fadeIn 0.3s ease forwards;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.connections-list.expanded .connection-item:hover {
  background: rgba(0, 0, 0, 0.3);
}

.connection-header {
  display: flex;
  align-items: center;
  white-space: nowrap;
}

.connection-name {
  color: var(--color-primary);
  font-weight: normal;
  cursor: pointer;
  z-index: 2;
}

.connections-list.expanded .connection-name:hover {
  text-decoration: underline;
}

.connection-type {
  color: var(--color-text-muted);
  margin-left: 0.25rem;
  font-size: 0.8rem;
}

.connection-reason {
  font-size: 0.85rem;
  font-style: italic;
  margin: 0.4rem 0 0;
  color: var(--color-text-muted);
  padding-top: 0.4rem;
  border-top: 1px dotted rgba(255, 255, 255, 0.1);
  white-space: normal;
}

@media (max-width: 768px) {
  .preview-text {
    max-width: 120px;
  }
}

@media (max-width: 480px) {
  .preview-text {
    max-width: 100px;
  }
}

.connection-session {
  font-size: 0.75rem;
  margin-top: 0.4rem;
  color: var(--color-text-muted);
  font-style: italic;
}

.session-link {
  cursor: pointer;
  text-decoration: underline dotted;
}

.session-link:hover {
  color: var(--color-text);
}
</style>

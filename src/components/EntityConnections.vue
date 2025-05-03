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
      </div>
    </div>
  </div>
</template>

<script>
import { getEntityConnections, getLocation } from '../store/worldData'; // Import getLocation
import { locations } from '../store/locations'; // Import locations data

export default {
  name: 'EntityConnections',
  props: {
    entityType: {
      type: String,
      required: true,
      validator: value => ['character', 'npc', 'location', 'item', 'lore'].includes(value)
    },
    entityId: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      expanded: false
    };
  },
  computed: {
    parentProvinceId() {
      if (this.entityType !== 'location') {
        return null;
      }
      const currentLocation = locations.find(loc => loc.id === this.entityId);
      if (!currentLocation || !currentLocation.connections) {
        return null;
      }
      // Find a connection to a location entity that is a province
      const provinceConnection = currentLocation.connections.find(conn => {
        if (conn.type === 'location') {
          const connectedLoc = getLocation(conn.id); // Use getLocation helper
          return connectedLoc && connectedLoc.type === 'province';
        }
        return false;
      });
      return provinceConnection ? provinceConnection.id : null;
    },
    connections() {
      const rawConnections = getEntityConnections(this.entityType, this.entityId);
      
      // If this is a location and we found a parent province, filter out the connection back to it
      if (this.parentProvinceId) {
        return rawConnections.filter(conn => 
          !(conn.entityType === 'location' && conn.id === this.parentProvinceId)
        );
      }
      
      return rawConnections; // Otherwise, return all connections
    },
    connectionNamesPreview() {
      if (this.connections.length === 0) return '';
      
      // Get first 3 names and join with commas
      const names = this.connections.slice(0, 3).map(c => c.name);
      let preview = names.join(', ');
      
      // Add ellipsis if there are more connections
      if (this.connections.length > 3) {
        preview += ` +${this.connections.length - 3} more`;
      }
      
      return preview;
    }
  },
  methods: {
    getConnectionTypeIcon(type) {
      const icons = {
        'location': '📌',
        'character': '👤',
        'npc': '👥',
        'item': '🔮',
        'lore': '📜' // Add icon for lore
      };
      return icons[type] || '🔗'; // Default icon
    },
    toggleConnections() {
      this.expanded = !this.expanded;
    },
    navigateToEntity(entityType, entityId) {
      if (!this.expanded) {
        // If not expanded, just expand instead of navigating
        this.expanded = true;
        return;
      }
      
      let routeName;
      
      if (entityType === 'location') {
        routeName = 'Locations';
      } else if (entityType === 'character') {
        routeName = 'Characters';
      } else if (entityType === 'npc') {
        routeName = 'NPCs';
      } else if (entityType === 'item') {
        routeName = 'Items';
      } else if (entityType === 'lore') { // Add case for lore
        routeName = 'Lore';
      } else {
        return;
      }
      
      this.$router.push({ name: routeName, hash: `#${entityId}` })
        .then(() => {
          this.scrollToElement(entityId);
        });
    },
    scrollToElement(id) {
      setTimeout(() => {
        const element = document.getElementById(id);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 100);
    }
  }
}
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
</style>

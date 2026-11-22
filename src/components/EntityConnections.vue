<template>
  <div class="entity-connections" v-if="connections.length" :class="{ 'is-expanded': expanded }">
    <button
      type="button"
      class="connections-header"
      @click="toggleConnections"
      :aria-expanded="expanded"
    >
      <div class="header-content">
        <h4>
          Connections
          <span class="connections-count">({{ connections.length }})</span>
        </h4>
        <div class="connections-preview" v-if="!expanded">
          <span class="preview-text">{{ connectionNamesPreview }}</span>
        </div>
      </div>
      <span class="toggle-icon" aria-hidden="true">{{ expanded ? '▼' : '▶' }}</span>
    </button>

    <div class="connections-list" :class="{ expanded }">
      <div
        v-for="connection in connections"
        :key="`${connection.type || connection.entityType}:${connection.id}`"
        class="connection-item"
        :class="{ 'is-incoming': connection.direction === 'incoming' }"
      >
        <div class="connection-header">
          <router-link
            :to="resolveConnectionRoute(connection)"
            class="connection-name"
          >
            {{ connection.name }}
          </router-link>
          <span class="connection-type" :title="connection.type || connection.entityType">
            {{ getConnectionTypeIcon(connection.type || connection.entityType) }}
          </span>
          <span
            v-if="connection.direction === 'incoming'"
            class="direction-badge"
            title="Referenced by this entity"
          >
            ← Backlink
          </span>
        </div>
        <p class="connection-reason" v-if="connection.reason">
          {{ connection.reason }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { getEntityConnections, getLocation } from '@/store/worldData.js';
import { locations } from '@/store/locations.js';
import { getEntityRoute } from '@/utils/entityHelpers.js';

const props = defineProps({
  entity: {
    type: Object,
    default: null,
  },
  entityType: {
    type: String,
    default: null,
    validator: (value) =>
      value === null || ['character', 'npc', 'location', 'item', 'lore'].includes(value),
  },
  entityId: {
    type: String,
    default: null,
  },
  filterOutConnectionId: {
    type: String,
    default: null,
  },
  defaultExpanded: {
    type: Boolean,
    default: false,
  },
});

const expanded = ref(props.defaultExpanded);

const resolvedType = computed(() => props.entityType || props.entity?.entityType || null);
const resolvedId = computed(() => props.entityId || props.entity?.id || null);

const parentProvinceId = computed(() => {
  if (resolvedType.value !== 'location' || !resolvedId.value) return null;
  const currentLocation = locations.find((loc) => loc.id === resolvedId.value);
  if (!currentLocation || !Array.isArray(currentLocation.connections)) return null;
  const provinceConn = currentLocation.connections.find((conn) => {
    if (conn.type === 'location') {
      const target = getLocation(conn.id);
      return target && target.type === 'province';
    }
    return false;
  });
  return provinceConn ? provinceConn.id : null;
});

const connections = computed(() => {
  let raw = props.entity
    ? getEntityConnections(props.entity)
    : resolvedType.value && resolvedId.value
      ? getEntityConnections(resolvedType.value, resolvedId.value)
      : [];

  if (props.filterOutConnectionId) {
    raw = raw.filter(
      (conn) =>
        !(
          (conn.type || conn.entityType) === 'location' &&
          conn.id === props.filterOutConnectionId
        )
    );
  }

  // Only suppress parent province when the caller explicitly requested filtering
  // OR for non-province child cards that only want peer connections.
  if (
    props.filterOutConnectionId &&
    parentProvinceId.value &&
    parentProvinceId.value !== props.filterOutConnectionId
  ) {
    raw = raw.filter(
      (conn) =>
        !(
          (conn.type || conn.entityType) === 'location' &&
          conn.id === parentProvinceId.value
        )
    );
  }

  return raw;
});

const connectionNamesPreview = computed(() => {
  if (!connections.value.length) return '';
  const names = connections.value.slice(0, 3).map((c) => c.name);
  let preview = names.join(', ');
  if (connections.value.length > 3) {
    preview += ` +${connections.value.length - 3} more`;
  }
  return preview;
});

function getConnectionTypeIcon(type) {
  const icons = {
    location: '📌',
    character: '👤',
    npc: '👥',
    item: '🔮',
    lore: '📜',
    session: '🗓️',
  };
  return icons[type] || '🔗';
}

function resolveConnectionRoute(connection) {
  return getEntityRoute(connection.type || connection.entityType, connection.id);
}

function toggleConnections() {
  expanded.value = !expanded.value;
}
</script>

<style scoped>
.entity-connections {
  margin-top: auto;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(var(--border-color-rgb), 0.6);
  transition: margin 0.25s ease, padding 0.25s ease;
  width: 100%;
  position: relative;
  z-index: 1;
  box-sizing: border-box;
}

.entity-connections.is-expanded {
  margin-top: 1rem;
  padding-top: 0.9rem;
  border-top-color: var(--border-color);
  z-index: 2;
}

.connections-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  background: transparent;
  border: none;
  color: inherit;
  cursor: pointer;
  user-select: none;
  padding: 0.15rem 0;
  font-size: 0.85rem;
  text-align: left;
  gap: 0.5rem;
}

.connections-header:hover {
  background: transparent;
  color: inherit;
}

.header-content {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 0.45rem;
  min-width: 0;
}

.entity-connections h4 {
  font-family: var(--font-display);
  color: var(--color-primary);
  margin: 0;
  font-size: 0.92rem;
  opacity: 0.9;
  font-weight: 600;
  display: inline-flex;
  align-items: baseline;
  gap: 0.25rem;
}

.connections-count {
  font-family: var(--font-main);
  font-size: 0.78rem;
  color: var(--color-text-muted);
  font-weight: 400;
}

.is-expanded h4 {
  font-size: 1rem;
  opacity: 1;
}

.connections-preview {
  display: inline;
  min-width: 0;
}

.preview-text {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  font-style: italic;
}

.connections-header:hover h4 {
  opacity: 1;
  color: var(--color-highlight);
}

.connections-header:hover .preview-text {
  color: var(--color-text);
}

.toggle-icon {
  font-size: 0.72rem;
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.connections-list {
  display: none;
}

.connections-list.expanded {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  margin-top: 0.75rem;
}

.connection-item {
  font-size: 0.85rem;
  padding: 0.5rem 0.75rem;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(var(--border-color-rgb), 0.55);
  border-radius: 5px;
  transition: background-color 0.2s ease, border-color 0.2s ease;
  max-width: 100%;
  box-sizing: border-box;
}

.connection-item.is-incoming {
  border-style: dashed;
  background: rgba(91, 176, 207, 0.06);
}

.connection-item:hover {
  background: rgba(0, 0, 0, 0.38);
  border-color: rgba(201, 169, 89, 0.5);
}

.connection-header {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.connection-name {
  color: var(--color-link);
  font-weight: 600;
  border-bottom: none;
}

.connection-name:hover {
  color: var(--color-link-hover);
  text-decoration: underline;
}

.connection-type {
  font-size: 0.82rem;
}

.direction-badge {
  font-size: 0.68rem;
  padding: 0.08rem 0.38rem;
  border-radius: 999px;
  background: rgba(91, 176, 207, 0.16);
  color: var(--color-link-hover);
  letter-spacing: 0.02em;
}

.connection-reason {
  font-size: 0.82rem;
  font-style: italic;
  margin: 0.35rem 0 0;
  color: var(--color-text-muted);
  padding-top: 0.35rem;
  border-top: 1px dotted rgba(255, 255, 255, 0.12);
  white-space: normal;
  line-height: 1.4;
}
</style>

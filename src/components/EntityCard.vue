<template>
  <div :class="['entity-card', `${entityType}-card`]" :id="entity.id">
    <div class="entity-content">
      <!-- Header Section -->
      <div class="entity-header" :class="specialClasses">
        <!-- Avatar Section -->
        <div
          v-if="showAvatar"
          class="avatar-container"
          @click="handleAvatarClick"
          :style="{ cursor: entity.portraitUrl ? 'pointer' : 'default' }"
          :title="entity.portraitUrl ? `View ${displayName} portrait` : undefined"
        >
          <div class="avatar-placeholder">
            <img
              v-if="entity.avatarUrl"
              :src="entity.avatarUrl"
              :alt="`${displayName} avatar`"
              class="avatar-image"
            />
            <span v-else>{{ getInitials(displayName) }}</span>
          </div>
        </div>

        <div class="entity-title-container">
          <h3 class="entity-title">
            <router-link v-if="entityType === 'character'" :to="`/characters/${entity.id}`">
              {{ entity.name }}
            </router-link>
            <span v-else>{{ displayName }}</span>
          </h3>

          <div v-if="entityType === 'character'" class="entity-subtitle">
            <div class="char-race">{{ entity.race }}</div>
            <div class="char-class">{{ entity.class }}</div>
          </div>

          <div v-if="currentBadge || fallbackBadge || entityHasHistory" class="entity-badge-row">
            <span
              v-if="currentBadge"
              :class="currentBadge === 'Updated' ? 'badge-updated' : 'badge-new'"
            >
              {{ currentBadge }}
            </span>
            <span v-else-if="fallbackBadge" class="badge-stale">{{ fallbackBadge }}</span>
            <button
              v-if="entityHasHistory"
              type="button"
              class="history-btn"
              @click="showHistory"
              aria-label="View change history"
              title="View change history"
            >
              History
            </button>
          </div>
        </div>

        <span v-if="entityType === 'item' && entity.rarity" class="entity-rarity">
          {{ entity.rarity }}
        </span>
      </div>

      <!-- Metadata Section -->
      <div v-if="hasMetadata" class="entity-meta">
        <template v-if="entityType === 'location'">
          <span class="meta-icon" aria-hidden="true">{{ locationIcon }}</span>
          <span class="meta-value" v-if="entity.region">{{ entity.region }}</span>
          <span class="meta-type-tag" v-else-if="entity.type">{{ formatLocationType(entity.type) }}</span>
        </template>

        <template v-else-if="entityType === 'character'">
          <div class="detail-row">
            <span class="detail-label">Level:</span>
            <span class="detail-value">{{ entity.level }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Background:</span>
            <span class="detail-value">{{ entity.background }}</span>
          </div>
        </template>

        <template v-else-if="entityType === 'npc'">
          <div class="detail-row" v-if="entity.location">
            <span class="detail-inline">📍&nbsp;{{ entity.location }}</span>
          </div>
          <div class="detail-row" v-if="entity.role">
            <span class="detail-inline">👤&nbsp;{{ entity.role }}</span>
          </div>
        </template>

        <template v-else-if="entityType === 'item'">
          <div class="property">
            <span class="property-label">Type:</span>
            <span>{{ entity.type }}</span>
          </div>
          <div class="property">
            <span class="property-label">Attunement:</span>
            <span>{{ entity.attunement }}</span>
          </div>
          <div v-if="entity.found" class="property">
            <span class="property-label">Found:</span>
            <span>{{ entity.found }}</span>
          </div>
          <div v-if="entity.owner" class="property">
            <span class="property-label">Current Owner:</span>
            <span>{{ entity.owner }}</span>
          </div>
        </template>
      </div>

      <!-- Description Section -->
      <div class="entity-description">
        <div class="description-body" v-html="formattedDescription"></div>
        <button
          v-if="entity.fullText"
          type="button"
          class="read-more-link"
          @click="showFullText"
        >
          Read More →
        </button>
      </div>

      <!-- Action Buttons Section (supports custom #actions slot) -->
      <div v-if="hasActions" class="entity-actions">
        <a
          v-if="entityType === 'character' && entity.dndBeyondLink"
          :href="entity.dndBeyondLink"
          target="_blank"
          rel="noopener noreferrer"
          class="button-link"
        >
          View on D&amp;D Beyond
        </a>
        <slot name="actions"></slot>
      </div>
    </div>

    <!-- EntityConnections Component -->
    <EntityConnections
      v-if="entity.id"
      :entity="entity"
      :entityType="entityType"
      :entityId="entity.id"
      :filter-out-connection-id="filterOutConnectionId"
    />
  </div>
</template>

<script setup>
import { computed, useSlots } from 'vue';
import { marked } from 'marked';
import EntityConnections from './EntityConnections.vue';
import {
  badgeLabel,
  fallbackBadgeLabel,
  hasHistory,
  formatHistoryMarkdown,
} from '@/utils/entityHelpers.js';

const props = defineProps({
  entity: {
    type: Object,
    required: true,
  },
  entityType: {
    type: String,
    required: true,
    validator: (value) => ['character', 'npc', 'location', 'item', 'lore'].includes(value),
  },
  showAvatar: {
    type: Boolean,
    default: false,
  },
  filterOutConnectionId: {
    type: String,
    default: null,
  },
});

const emit = defineEmits(['show-full-text', 'show-portrait']);
const slots = useSlots();

const displayName = computed(() =>
  props.entityType === 'lore' ? props.entity.term : props.entity.name
);

const currentBadge = computed(() => badgeLabel(props.entity));
const fallbackBadge = computed(() => fallbackBadgeLabel(props.entity));
const entityHasHistory = computed(() => hasHistory(props.entity));

const hasMetadata = computed(() => {
  if (props.entityType === 'location' && (props.entity.region || props.entity.type)) return true;
  if (props.entityType === 'character') return true;
  if (props.entityType === 'npc') return true;
  if (props.entityType === 'item') return true;
  return false;
});

const hasActions = computed(() => {
  const hasSlot = Boolean(slots.actions && slots.actions().length > 0);
  const hasDndBeyond = props.entityType === 'character' && Boolean(props.entity.dndBeyondLink);
  return hasSlot || hasDndBeyond;
});

const specialClasses = computed(() => {
  const classes = {};
  if (props.entityType === 'item' && props.entity.rarity) {
    classes[props.entity.rarity.toLowerCase().replace(/\s+/g, '-')] = true;
  }
  return classes;
});

const locationIcon = computed(() => {
  if (props.entityType !== 'location') return '';
  const typeIcons = {
    empire: '👑',
    province: '🗺️',
    capital: '🏛️',
    city: '🏙️',
    town: '🏘️',
    village: '⛰️',
    dungeon: '🏚️',
    landmark: '🗼',
    tavern: '🍺',
    inn: '🛏️',
    prison: '⛓️',
    facility: '⚙️',
    poi: '📍',
  };
  return typeIcons[props.entity.type] || '📍';
});

function formatLocationType(type) {
  const labels = {
    poi: 'Point of Interest',
    empire: 'Empire',
    province: 'Province',
    capital: 'Capital',
    city: 'City',
    town: 'Town',
    village: 'Village',
    dungeon: 'Dungeon',
    landmark: 'Landmark',
    tavern: 'Tavern',
    inn: 'Inn',
    prison: 'Prison',
    facility: 'Facility',
  };
  return labels[type] || type;
}

const formattedDescription = computed(() => {
  const raw = props.entity.description || props.entity.bio || '';
  if (!raw) return '';

  const blocks = String(raw)
    .split(/\n\s*\n/)
    .map((block) => block.trim())
    .filter(Boolean);

  return blocks
    .map((block) => {
      if (block.startsWith('>')) {
        const quoteText = block
          .split('\n')
          .map((line) => line.replace(/^>\s?/, ''))
          .join(' ');
        return `<blockquote><p>${marked.parseInline(quoteText)}</p></blockquote>`;
      }
      return `<p>${marked.parseInline(block)}</p>`;
    })
    .join('');
});

function getInitials(name) {
  if (!name) return '?';
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0])
    .join('')
    .toUpperCase();
}

function showFullText() {
  emit('show-full-text', {
    title: displayName.value,
    text: props.entity.fullText,
  });
}

function handleAvatarClick() {
  if (props.entity.portraitUrl) {
    emit('show-portrait', {
      title: props.entity.name,
      imageUrl: props.entity.portraitUrl,
    });
  }
}

function showHistory() {
  const text = formatHistoryMarkdown(props.entity);
  if (!text) return;
  emit('show-full-text', {
    title: `History: ${displayName.value}`,
    text,
  });
}
</script>

<style scoped>
/* Base card styling (single padding layer — no double padding) */
.entity-card {
  background: rgba(0, 0, 0, 0.22);
  border-radius: 8px;
  padding: 1.25rem;
  border: 1px solid var(--border-color);
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.entity-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
  border-color: rgba(201, 169, 89, 0.45);
}

.entity-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  padding: 0;
}

/* Header section */
.entity-header {
  display: flex;
  align-items: center;
  margin-bottom: 0.9rem;
}

.entity-title-container {
  flex-grow: 1;
  min-width: 0;
}

.entity-title {
  margin: 0;
  font-family: var(--font-display);
  color: var(--color-primary);
  font-size: 1.25rem;
  line-height: 1.25;
}

.entity-title a {
  color: var(--color-primary);
  text-decoration: none;
  border-bottom: none;
  transition: color 0.2s ease;
}

.entity-title a:hover {
  color: var(--color-highlight);
  text-decoration: underline;
}

.entity-subtitle {
  color: var(--color-text-muted);
  margin: 0.3rem 0 0.45rem;
  font-size: 0.9rem;
  font-style: italic;
  line-height: 1.45;
}

/* Avatar styling */
.avatar-container {
  margin-right: 1rem;
  flex-shrink: 0;
}

.avatar-placeholder {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: var(--color-primary);
  color: var(--color-background);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.35rem;
  font-weight: bold;
  font-family: var(--font-display);
  border: 2px solid var(--color-primary);
  overflow: hidden;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Metadata section */
.entity-meta {
  margin-bottom: 0.85rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.location-card .entity-meta {
  flex-direction: row;
  align-items: center;
  gap: 0.4rem;
}

.meta-icon {
  font-size: 1rem;
}

.meta-value,
.meta-type-tag {
  font-size: 0.82rem;
  color: var(--color-text-muted);
  font-style: italic;
}

.detail-row {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  font-size: 0.92rem;
}

.detail-label {
  font-weight: bold;
  color: var(--color-primary);
  min-width: 96px;
  margin-right: 0.5rem;
}

.detail-value {
  flex: 1;
  word-wrap: break-word;
  max-width: 100%;
}

.detail-inline {
  display: inline;
  color: var(--color-text-muted);
}

.char-race,
.char-class {
  margin: 0.1rem 0;
  line-height: 1.3;
  color: var(--color-text-muted);
}

.char-class {
  font-weight: 500;
}

/* Description section */
.entity-description {
  flex-grow: 1;
  margin-bottom: 0.85rem;
}

.description-body :deep(p) {
  margin: 0 0 0.6rem 0;
  line-height: 1.62;
}

.description-body :deep(p:last-child) {
  margin-bottom: 0;
}

.description-body :deep(blockquote) {
  margin: 0 0 0.7rem 0;
  padding: 0.5rem 0.85rem;
  border-left: 3px solid var(--color-primary);
  background: rgba(201, 169, 89, 0.08);
  border-radius: 0 4px 4px 0;
  font-style: italic;
  color: var(--color-text);
}

.description-body :deep(blockquote p) {
  margin: 0;
}

.description-body :deep(em) {
  color: #f3e6c8;
}

/* High-contrast Read More & History controls */
.read-more-link {
  display: inline-block;
  margin-top: 0.55rem;
  color: var(--color-link);
  background: transparent;
  border: none;
  padding: 0;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
}

.read-more-link:hover {
  background: transparent;
  color: var(--color-link-hover);
  text-decoration: underline;
}

/* Actions section */
.entity-actions {
  margin-top: 0.75rem;
  margin-bottom: 0.5rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: flex-start;
}

.entity-actions :deep(.button-link) {
  margin-top: 0;
}

/* Badges */
.badge-new,
.badge-updated,
.badge-stale {
  display: inline-block;
  padding: 0.12rem 0.45rem;
  font-size: 0.72rem;
  font-weight: 700;
  color: #111;
  border-radius: 3px;
}

.badge-new {
  background: #ffd54f;
}

.badge-updated {
  background: #90caf9;
}

.badge-stale {
  background: #cfd6e0;
}

.entity-badge-row {
  margin-top: 0.4rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.history-btn {
  margin-left: auto;
  font-size: 0.84rem;
  line-height: 1.1;
  color: var(--color-link);
  background: transparent;
  border: none;
  cursor: pointer;
  font-weight: 600;
  padding: 0.1rem 0;
}

.history-btn:hover {
  background: transparent;
  color: var(--color-link-hover);
  text-decoration: underline;
}

/* Item properties */
.property {
  margin-bottom: 0.5rem;
}

.property-label {
  font-weight: bold;
  color: var(--color-primary);
  margin-right: 0.5rem;
}

.entity-rarity {
  font-family: var(--font-accent);
  font-size: 0.9em;
  font-weight: bold;
  padding: 0.3em 0.6em;
  border-radius: 4px;
  text-transform: uppercase;
}
</style>

<template>
  <div class="content-section">
    <h1>Notable NPCs</h1>

    <FilterBar
      v-model="searchQuery"
      v-model:activeFilter="activeFilter"
      :filters="filterPills"
      :totalCount="npcs.length"
      :filteredCount="filteredNpcs.length"
      itemLabel="NPCs"
      placeholder="Search NPCs by name, role, location, or description..."
    />

    <!-- Major NPCs (Key Figures) -->
    <div v-if="majorNpcs.length" class="location-section">
      <h2>Key Figures</h2>
      <div class="entity-grid">
        <EntityCard
          v-for="npc in majorNpcs"
          :key="npc.id"
          :entity="npc"
          entityType="npc"
          :showAvatar="Boolean(npc.avatarUrl)"
          @show-full-text="handleShowFullText"
          @show-portrait="handleShowPortrait"
        />
      </div>
    </div>

    <!-- Minor NPCs (Others) — now also supports Read More & Connections when present -->
    <div v-if="minorNpcs.length" class="location-section">
      <h2>Others</h2>
      <div class="npc-list">
        <div class="npc-list-item" v-for="npc in minorNpcs" :key="npc.id" :id="npc.id">
          <div class="npc-list-header">
            <strong class="npc-name">{{ npc.name }}</strong>
            <span class="npc-role">{{ npc.role }}</span>
            <button
              v-if="hasHistory(npc)"
              type="button"
              class="history-btn"
              @click="showMinorHistory(npc)"
              aria-label="View change history"
              title="View change history"
            >
              History
            </button>
          </div>
          <div class="npc-list-body">
            <div class="npc-meta-row">
              <span v-if="npc.location" class="npc-meta">📍 {{ npc.location }}</span>
              <span
                v-if="badgeLabel(npc)"
                :class="badgeLabel(npc) === 'Updated' ? 'badge-updated' : 'badge-new'"
              >
                {{ badgeLabel(npc) }}
              </span>
              <span v-else-if="fallbackBadgeLabel(npc)" class="badge-stale">
                {{ fallbackBadgeLabel(npc) }}
              </span>
            </div>
            <p class="npc-desc">{{ npc.description }}</p>
            <button
              v-if="npc.fullText"
              type="button"
              class="read-more-link"
              @click="handleShowFullText({ title: npc.name, text: npc.fullText })"
            >
              Read More →
            </button>
          </div>
          <EntityConnections
            :entity="npc"
            entityType="npc"
            :entityId="npc.id"
          />
        </div>
      </div>
    </div>

    <p v-if="!filteredNpcs.length" class="empty-message">
      {{ npcs.length ? 'No NPCs match your current filter.' : 'No NPCs recorded yet.' }}
    </p>

    <FullTextModal
      :visible="isOpen"
      :title="modalTitle"
      :text="modalContent"
      :imageUrl="modalMeta.imageUrl || null"
      @close="closeModal"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import EntityCard from '@/components/EntityCard.vue';
import EntityConnections from '@/components/EntityConnections.vue';
import FullTextModal from '@/components/FullTextModal.vue';
import FilterBar from '@/components/FilterBar.vue';
import { npcs } from '@/store/npcs.js';
import { currentSession, isEntityNew } from '@/store/config.js';
import { sortEntitiesByLastSession } from '@/utils/entitySorting.js';
import {
  badgeLabel,
  fallbackBadgeLabel,
  hasHistory,
  formatHistoryMarkdown,
} from '@/utils/entityHelpers.js';
import { useModal } from '@/composables/useModal.js';

const { isOpen, modalTitle, modalContent, modalMeta, openModal, closeModal } = useModal();

const searchQuery = ref('');
const activeFilter = ref('all');

function isMajorNpc(npc) {
  if (!npc) return false;
  if (npc.prominence === 'major') return true;
  if (npc.prominence === 'minor') return false;
  return Boolean(npc.fullText) || ['ally', 'enemy'].includes((npc.status || '').toLowerCase());
}

const filterPills = computed(() => [
  { value: 'all', label: 'All', count: npcs.length },
  {
    value: 'updated',
    label: `Updated in Session ${currentSession}`,
    count: npcs.filter((n) => isEntityNew(n, currentSession)).length,
  },
  {
    value: 'major',
    label: 'Key Figures',
    count: npcs.filter((n) => isMajorNpc(n)).length,
  },
  {
    value: 'minor',
    label: 'Others',
    count: npcs.filter((n) => !isMajorNpc(n)).length,
  },
]);

const filteredNpcs = computed(() => {
  const q = searchQuery.value.trim().toLowerCase();
  return npcs.filter((npc) => {
    if (activeFilter.value === 'updated' && !isEntityNew(npc, currentSession)) return false;
    if (activeFilter.value === 'major' && !isMajorNpc(npc)) return false;
    if (activeFilter.value === 'minor' && isMajorNpc(npc)) return false;

    if (!q) return true;
    const haystack = [npc.name, npc.role, npc.location, npc.description, npc.fullText]
      .filter(Boolean)
      .join(' ')
      .toLowerCase();
    return haystack.includes(q);
  });
});

const majorNpcs = computed(() =>
  sortEntitiesByLastSession(filteredNpcs.value.filter((n) => isMajorNpc(n)))
);

const minorNpcs = computed(() =>
  sortEntitiesByLastSession(filteredNpcs.value.filter((n) => !isMajorNpc(n)))
);

function showMinorHistory(entity) {
  const text = formatHistoryMarkdown(entity);
  if (!text) return;
  openModal(`History: ${entity.name}`, text, { imageUrl: null });
}

function handleShowFullText(payload) {
  openModal(payload.title, payload.text, { imageUrl: null });
}

function handleShowPortrait(payload) {
  openModal(payload.title, '', { imageUrl: payload.imageUrl });
}
</script>

<style scoped>
.npc-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.15rem;
  align-items: start;
}

.npc-list-item {
  background: rgba(0, 0, 0, 0.22);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1rem 1.15rem;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.npc-list-header {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.npc-name {
  color: var(--color-primary);
  font-family: var(--font-display);
  font-size: 1.05rem;
}

.npc-role {
  color: var(--color-text-muted);
  font-style: italic;
  font-size: 0.9rem;
}

.npc-meta-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin-bottom: 0.35rem;
}

.npc-meta {
  color: var(--color-text-muted);
  font-size: 0.85rem;
}

.badge-new,
.badge-updated,
.badge-stale {
  padding: 0.08rem 0.42rem;
  font-size: 0.7rem;
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

.history-btn {
  margin-left: auto;
  font-size: 0.84rem;
  line-height: 1.1;
  color: var(--color-link);
  background: transparent;
  border: none;
  cursor: pointer;
  font-weight: 600;
  padding: 0;
}

.history-btn:hover {
  background: transparent;
  color: var(--color-link-hover);
  text-decoration: underline;
}

.read-more-link {
  display: inline-block;
  margin-top: 0.45rem;
  color: var(--color-link);
  background: transparent;
  border: none;
  padding: 0;
  font-size: 0.88rem;
  font-weight: 700;
  cursor: pointer;
}

.read-more-link:hover {
  background: transparent;
  color: var(--color-link-hover);
  text-decoration: underline;
}

.npc-desc {
  margin: 0;
  line-height: 1.58;
}

.location-section {
  margin: 1.5rem 0;
}

.empty-message {
  text-align: center;
  margin-top: 2rem;
  color: var(--text-muted);
}
</style>

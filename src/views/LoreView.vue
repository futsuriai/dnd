<template>
  <div class="content-section">
    <h1>World Lore</h1>

    <FilterBar
      v-model="searchQuery"
      v-model:activeFilter="activeFilter"
      :filters="filterPills"
      :totalCount="lore.length"
      :filteredCount="filteredLoreEntries.length"
      itemLabel="lore entries"
      placeholder="Search lore by term, description, or full entry..."
    />

    <div v-if="filteredLoreEntries.length" class="lore-list">
      <EntityCard
        v-for="item in filteredLoreEntries"
        :key="item.id"
        :entity="item"
        entityType="lore"
        @show-full-text="handleShowFullText"
      />
    </div>

    <p v-else class="empty-message">No lore entries match your current filter.</p>

    <FullTextModal
      :visible="isOpen"
      :title="modalTitle"
      :text="modalContent"
      @close="closeModal"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import EntityCard from '@/components/EntityCard.vue';
import FullTextModal from '@/components/FullTextModal.vue';
import FilterBar from '@/components/FilterBar.vue';
import { lore } from '@/store/lore.js';
import { currentSession, isEntityNew } from '@/store/config.js';
import { sortEntitiesByLastSession } from '@/utils/entitySorting.js';
import { useModal } from '@/composables/useModal.js';

const { isOpen, modalTitle, modalContent, openModal, closeModal } = useModal();

const searchQuery = ref('');
const activeFilter = ref('all');

const sortedLore = computed(() => sortEntitiesByLastSession(lore));

const filterPills = computed(() => [
  { value: 'all', label: 'All', count: lore.length },
  {
    value: 'updated',
    label: `Updated in Session ${currentSession}`,
    count: lore.filter((entry) => isEntityNew(entry, currentSession)).length,
  },
  {
    value: 'detailed',
    label: 'Full Entries',
    count: lore.filter((entry) => Boolean(entry.fullText)).length,
  },
]);

const filteredLoreEntries = computed(() => {
  const q = searchQuery.value.trim().toLowerCase();
  return sortedLore.value.filter((entry) => {
    if (activeFilter.value === 'updated' && !isEntityNew(entry, currentSession)) return false;
    if (activeFilter.value === 'detailed' && !entry.fullText) return false;

    if (!q) return true;
    const haystack = [entry.term, entry.description, entry.fullText]
      .filter(Boolean)
      .join(' ')
      .toLowerCase();
    return haystack.includes(q);
  });
});

function handleShowFullText(payload) {
  openModal(payload.title, payload.text);
}
</script>

<style scoped>
.lore-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  align-items: stretch;
}

.empty-message {
  text-align: center;
  margin-top: 2rem;
  color: var(--text-muted);
}
</style>

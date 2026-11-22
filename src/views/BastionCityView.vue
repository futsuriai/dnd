<template>
  <div class="content-section">
    <div class="bastion-header">
      <h1>Bastion City</h1>
    </div>

    <FilterBar
      v-model="searchQuery"
      v-model:activeFilter="activeFilter"
      :filters="filterPills"
      :totalCount="allBastionLocations.length"
      :filteredCount="filteredBastionLocations.length"
      itemLabel="Bastion locations"
      placeholder="Search Bastion districts, inns, prisons, or Lighthouse floors..."
    />

    <div v-if="filteredBastionLocations.length" class="locations-container">
      <!-- City Landmarks, Districts, Taverns, Inns & Prisons -->
      <div v-if="cityLocations.length" class="location-section">
        <h2>City Landmarks &amp; Establishments</h2>
        <div class="entity-grid">
          <EntityCard
            v-for="location in cityLocations"
            :key="location.id"
            :entity="location"
            entityType="location"
            filter-out-connection-id="bastion-city"
            @show-full-text="handleShowFullText"
          />
        </div>
      </div>

      <!-- Duskbreaker Lighthouse Facilities (surfaces all 4 facilities + Medical Bay) -->
      <div v-if="lighthouseFacilities.length" class="location-section lighthouse-section">
        <h2>Duskbreaker Lighthouse Facilities</h2>
        <div class="entity-grid">
          <EntityCard
            v-for="facility in lighthouseFacilities"
            :key="facility.id"
            :entity="facility"
            entityType="location"
            @show-full-text="handleShowFullText"
          />
        </div>
      </div>
    </div>

    <p v-else class="empty-message">No Bastion City locations match your current filter.</p>

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
import { locations } from '@/store/locations.js';
import { currentSession, isEntityNew } from '@/store/config.js';
import { sortEntitiesByLastSession } from '@/utils/entitySorting.js';
import { useModal } from '@/composables/useModal.js';

const { isOpen, modalTitle, modalContent, openModal, closeModal } = useModal();

const searchQuery = ref('');
const activeFilter = ref('all');

function isLighthouseFacility(loc) {
  if (!loc) return false;
  if (loc.type === 'facility') return true;
  return Boolean(
    Array.isArray(loc.connections) &&
      loc.connections.some((conn) => conn && conn.type === 'location' && conn.id === 'duskbreaker-lighthouse') &&
      Array.isArray(loc.tags) &&
      loc.tags.includes('lighthouse')
  );
}

const allBastionLocations = computed(() => {
  const list = locations.filter((loc) => {
    if (!loc || loc.id === 'bastion-city') return false;
    if (Array.isArray(loc.tags) && loc.tags.includes('bastion city')) return true;
    return Boolean(
      Array.isArray(loc.connections) &&
        loc.connections.some(
          (conn) =>
            conn &&
            conn.type === 'location' &&
            (conn.id === 'bastion-city' || conn.id === 'duskbreaker-lighthouse')
        )
    );
  });
  return sortEntitiesByLastSession(list);
});

const filterPills = computed(() => [
  { value: 'all', label: 'All', count: allBastionLocations.value.length },
  {
    value: 'updated',
    label: `Updated in Session ${currentSession}`,
    count: allBastionLocations.value.filter((loc) => isEntityNew(loc, currentSession)).length,
  },
  {
    value: 'facilities',
    label: 'Lighthouse Facilities',
    count: allBastionLocations.value.filter((loc) => isLighthouseFacility(loc)).length,
  },
  {
    value: 'taverns',
    label: 'Taverns & Inns',
    count: allBastionLocations.value.filter((loc) => ['tavern', 'inn'].includes(loc.type)).length,
  },
  {
    value: 'prisons',
    label: 'Prisons',
    count: allBastionLocations.value.filter((loc) => loc.type === 'prison').length,
  },
]);

const filteredBastionLocations = computed(() => {
  const q = searchQuery.value.trim().toLowerCase();
  return allBastionLocations.value.filter((loc) => {
    if (activeFilter.value === 'updated' && !isEntityNew(loc, currentSession)) return false;
    if (activeFilter.value === 'facilities' && !isLighthouseFacility(loc)) return false;
    if (activeFilter.value === 'taverns' && !['tavern', 'inn'].includes(loc.type)) return false;
    if (activeFilter.value === 'prisons' && loc.type !== 'prison') return false;

    if (!q) return true;
    const haystack = [
      loc.name,
      loc.type,
      loc.description,
      loc.fullText,
      ...(Array.isArray(loc.tags) ? loc.tags : []),
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase();
    return haystack.includes(q);
  });
});

const lighthouseFacilities = computed(() =>
  filteredBastionLocations.value.filter((loc) => isLighthouseFacility(loc))
);

const cityLocations = computed(() =>
  filteredBastionLocations.value.filter((loc) => !isLighthouseFacility(loc))
);

function handleShowFullText(payload) {
  openModal(payload.title, payload.text);
}
</script>

<style scoped>
.bastion-header {
  margin-bottom: 1rem;
}

.lighthouse-section {
  border-color: rgba(201, 169, 89, 0.4);
}

.empty-message {
  text-align: center;
  margin-top: 1.5rem;
  color: var(--text-muted);
  font-style: italic;
}
</style>

<template>
  <div class="content-section">
    <div class="locations-header">
      <h1>World Locations</h1>
      <p class="section-intro">
        Provinces, capitals, towns, and notable places across The Hariolar Empire.
        Looking for city districts, prisons, or Duskbreaker Lighthouse interiors?
        <router-link to="/bastion-city" class="inline-bastion-link">Explore Bastion City →</router-link>
      </p>
    </div>

    <FilterBar
      v-model="searchQuery"
      v-model:activeFilter="activeFilter"
      :filters="filterPills"
      :totalCount="worldLocations.length"
      :filteredCount="filteredWorldLocations.length"
      itemLabel="locations"
      placeholder="Search locations by name, region, tag, or description..."
    />

    <div v-if="filteredWorldLocations.length" class="locations-container">
      <!-- Imperial Overview (Empire-level entities) -->
      <div v-if="filteredEmpires.length" class="location-section empire-section">
        <h2>The Empire</h2>
        <div class="empire-cards">
          <EntityCard
            v-for="empire in filteredEmpires"
            :key="empire.id"
            :entity="empire"
            entityType="location"
            :class="['location-card', `location-type-${empire.type}`]"
            @show-full-text="handleShowFullText"
          />
        </div>
      </div>

      <!-- Provinces & Nested Locations -->
      <div
        v-for="group in visibleProvinceGroups"
        :key="group.province.id"
        class="location-section province-section"
      >
        <EntityCard
          v-if="group.showProvinceCard"
          :entity="group.province"
          entityType="location"
          :class="['location-card', `location-type-${group.province.type}`]"
          @show-full-text="handleShowFullText"
        />
        <h2 v-else class="province-fallback-heading">{{ group.province.name }}</h2>

        <div v-if="group.children.length" class="nested-locations entity-grid">
          <EntityCard
            v-for="location in group.children"
            :key="location.id"
            :entity="location"
            entityType="location"
            :filter-out-connection-id="group.province.id"
            :class="['location-card', `location-type-${location.type}`]"
            @show-full-text="handleShowFullText"
          >
            <template v-if="location.id === 'bastion-city'" #actions>
              <router-link :to="{ name: 'Bastion City' }" class="button-link">
                Explore Bastion City →
              </router-link>
            </template>
          </EntityCard>
        </div>
        <p v-else-if="!isFiltering" class="empty-message nested-empty">
          No known locations recorded within {{ group.province.name }}.
        </p>
      </div>

      <!-- Standalone Towns, Villages & Other Regions (e.g., Arcos) -->
      <div v-if="filteredOtherSettlements.length" class="location-section">
        <h2>Towns &amp; Distant Regions</h2>
        <div class="entity-grid">
          <EntityCard
            v-for="location in filteredOtherSettlements"
            :key="location.id"
            :entity="location"
            entityType="location"
            :class="['location-card', `location-type-${location.type}`]"
            @show-full-text="handleShowFullText"
          />
        </div>
      </div>

      <!-- Dungeons & Ruins -->
      <div v-if="filteredDungeons.length" class="location-section">
        <h2>Dungeons &amp; Ruins</h2>
        <div class="entity-grid">
          <EntityCard
            v-for="location in filteredDungeons"
            :key="location.id"
            :entity="location"
            entityType="location"
            :class="['location-card', `location-type-${location.type}`]"
            @show-full-text="handleShowFullText"
          />
        </div>
      </div>

      <!-- Points of Interest (deduplicated against province-nested locations like Torchlight College) -->
      <div v-if="filteredPointsOfInterest.length" class="location-section">
        <h2>Points of Interest</h2>
        <div class="entity-grid">
          <EntityCard
            v-for="location in filteredPointsOfInterest"
            :key="location.id"
            :entity="location"
            entityType="location"
            :class="['location-card', `location-type-${location.type}`]"
            @show-full-text="handleShowFullText"
          />
        </div>
      </div>
    </div>

    <p v-else class="empty-message">No locations match your current filter.</p>

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
import { locations } from '@/store/locations.js';
import { currentSession, isEntityNew } from '@/store/config.js';
import EntityCard from '@/components/EntityCard.vue';
import FullTextModal from '@/components/FullTextModal.vue';
import FilterBar from '@/components/FilterBar.vue';
import { sortEntitiesByLastSession } from '@/utils/entitySorting.js';
import { BASTION_ONLY_LOCATION_IDS } from '@/utils/entityHelpers.js';
import { useModal } from '@/composables/useModal.js';

const { isOpen, modalTitle, modalContent, openModal, closeModal } = useModal();

const searchQuery = ref('');
const activeFilter = ref('all');

const POI_TYPES = new Set(['poi', 'landmark', 'tavern']);

// Exclude Bastion-only locations (inns, prisons, Lighthouse facilities rendered on /bastion-city)
const worldLocations = computed(() =>
  locations.filter((loc) => loc && !BASTION_ONLY_LOCATION_IDS.has(loc.id))
);

function prioritizeEntities(entities, priorityIds = []) {
  if (!priorityIds.length) return entities;
  const remaining = [...entities];
  const prioritized = [];
  for (const id of priorityIds) {
    const idx = remaining.findIndex((entity) => entity.id === id);
    if (idx !== -1) {
      prioritized.push(remaining.splice(idx, 1)[0]);
    }
  }
  return prioritized.concat(remaining);
}

const allProvinces = computed(() =>
  prioritizeEntities(
    sortEntitiesByLastSession(worldLocations.value.filter((loc) => loc.type === 'province')),
    ['hieroterra']
  )
);

// Assign each non-empire/non-province world location to at most one parent province
const provinceAssignment = computed(() => {
  const provinceIds = new Set(allProvinces.value.map((p) => p.id));
  const byProvince = new Map();
  for (const p of allProvinces.value) {
    byProvince.set(p.id, []);
  }
  const assignedIds = new Set();

  for (const loc of worldLocations.value) {
    if (loc.type === 'province' || loc.type === 'empire') continue;
    const parentConn = (loc.connections || []).find(
      (conn) => conn && conn.type === 'location' && provinceIds.has(conn.id)
    );
    if (parentConn) {
      byProvince.get(parentConn.id).push(loc);
      assignedIds.add(loc.id);
    }
  }

  for (const [provId, list] of byProvince.entries()) {
    byProvince.set(provId, sortEntitiesByLastSession(list));
  }

  return { byProvince, assignedIds };
});

function matchesSearch(loc, q) {
  if (!q) return true;
  const haystack = [
    loc.name,
    loc.type,
    loc.region,
    loc.description,
    loc.fullText,
    ...(Array.isArray(loc.tags) ? loc.tags : []),
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase();
  return haystack.includes(q);
}

function matchesCategory(loc, filterValue) {
  if (filterValue === 'all') return true;
  if (filterValue === 'updated') return isEntityNew(loc, currentSession);
  if (filterValue === 'regions') {
    return (
      ['empire', 'province', 'capital', 'city', 'town', 'village'].includes(loc.type) ||
      provinceAssignment.value.assignedIds.has(loc.id)
    );
  }
  if (filterValue === 'poi') {
    return POI_TYPES.has(loc.type) && !provinceAssignment.value.assignedIds.has(loc.id);
  }
  if (filterValue === 'dungeon') return loc.type === 'dungeon';
  return true;
}

const isFiltering = computed(
  () => Boolean(searchQuery.value.trim()) || activeFilter.value !== 'all'
);

const filteredWorldLocations = computed(() => {
  const q = searchQuery.value.trim().toLowerCase();
  return worldLocations.value.filter(
    (loc) => matchesCategory(loc, activeFilter.value) && matchesSearch(loc, q)
  );
});

const filteredIdSet = computed(() => new Set(filteredWorldLocations.value.map((loc) => loc.id)));

const filterPills = computed(() => {
  const pills = [
    { value: 'all', label: 'All', count: worldLocations.value.length },
    {
      value: 'updated',
      label: `Updated in Session ${currentSession}`,
      count: worldLocations.value.filter((loc) => isEntityNew(loc, currentSession)).length,
    },
    {
      value: 'regions',
      label: 'Provinces & Settlements',
      count: worldLocations.value.filter(
        (loc) =>
          ['empire', 'province', 'capital', 'city', 'town', 'village'].includes(loc.type) ||
          provinceAssignment.value.assignedIds.has(loc.id)
      ).length,
    },
    {
      value: 'poi',
      label: 'Points of Interest',
      count: worldLocations.value.filter(
        (loc) => POI_TYPES.has(loc.type) && !provinceAssignment.value.assignedIds.has(loc.id)
      ).length,
    },
  ];
  const dungeonCount = worldLocations.value.filter((loc) => loc.type === 'dungeon').length;
  if (dungeonCount > 0) {
    pills.push({ value: 'dungeon', label: 'Dungeons & Ruins', count: dungeonCount });
  }
  return pills;
});

const filteredEmpires = computed(() =>
  sortEntitiesByLastSession(
    filteredWorldLocations.value.filter((loc) => loc.type === 'empire')
  )
);

const visibleProvinceGroups = computed(() => {
  const groups = [];
  for (const province of allProvinces.value) {
    const showProvinceCard = filteredIdSet.value.has(province.id);
    const children = (provinceAssignment.value.byProvince.get(province.id) || []).filter((child) =>
      filteredIdSet.value.has(child.id)
    );
    if (showProvinceCard || children.length) {
      groups.push({
        province,
        showProvinceCard,
        children,
      });
    }
  }
  return groups;
});

const filteredDungeons = computed(() =>
  sortEntitiesByLastSession(
    filteredWorldLocations.value.filter(
      (loc) => loc.type === 'dungeon' && !provinceAssignment.value.assignedIds.has(loc.id)
    )
  )
);

const filteredPointsOfInterest = computed(() =>
  sortEntitiesByLastSession(
    filteredWorldLocations.value.filter(
      (loc) => POI_TYPES.has(loc.type) && !provinceAssignment.value.assignedIds.has(loc.id)
    )
  )
);

// Catch-all for unattached towns/villages/cities (such as Arcos) so zero locations are ever hidden
const filteredOtherSettlements = computed(() => {
  const excludedIds = new Set([
    ...provinceAssignment.value.assignedIds,
    ...filteredEmpires.value.map((l) => l.id),
    ...allProvinces.value.map((l) => l.id),
    ...filteredDungeons.value.map((l) => l.id),
    ...filteredPointsOfInterest.value.map((l) => l.id),
  ]);
  return sortEntitiesByLastSession(
    filteredWorldLocations.value.filter((loc) => !excludedIds.has(loc.id))
  );
});

function handleShowFullText(payload) {
  openModal(payload.title, payload.text);
}
</script>

<style scoped>
.locations-header {
  margin-bottom: 1rem;
}

.inline-bastion-link {
  font-weight: 700;
  color: var(--color-link);
}

.empty-message {
  text-align: center;
  margin-top: 1rem;
  color: var(--text-muted);
}

.province-section {
  margin-bottom: 0.5rem;
}

.province-fallback-heading {
  margin-top: 0;
}

.nested-locations {
  margin-top: 1.25rem;
}

.nested-empty {
  padding-left: 0.5rem;
  font-style: italic;
}

.empire-cards {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

:deep(.location-card.location-type-province) {
  border-left: 3px solid var(--color-link);
  background: rgba(var(--background-secondary-rgb), 0.35);
}

:deep(.location-card.location-type-capital) {
  border-left: 3px solid var(--color-primary);
}

:deep(.location-card.location-type-empire) {
  border-left: 3px solid var(--color-highlight);
}
</style>

<template>
  <div class="filter-bar">
    <div class="filter-controls-row">
      <div class="filter-search-wrapper">
        <span class="filter-search-icon" aria-hidden="true">⌕</span>
        <input
          type="text"
          class="filter-search-input"
          :value="modelValue"
          :placeholder="placeholder"
          :aria-label="placeholder"
          @input="emit('update:modelValue', $event.target.value)"
        />
        <button
          v-if="modelValue"
          type="button"
          class="filter-clear-btn"
          aria-label="Clear filter search"
          @click="emit('update:modelValue', '')"
        >
          &times;
        </button>
      </div>

      <div class="filter-count" aria-live="polite">
        <span>Showing <strong>{{ filteredCount }}</strong> of {{ totalCount }} {{ itemLabel }}</span>
        <button
          v-if="isFiltered"
          type="button"
          class="filter-reset-btn"
          @click="resetAll"
        >
          Reset
        </button>
      </div>
    </div>

    <div v-if="filters.length" class="filter-pills" role="group" aria-label="Category filters">
      <button
        v-for="pill in filters"
        :key="pill.value"
        type="button"
        class="filter-pill"
        :class="{ active: activeFilter === pill.value }"
        :aria-pressed="activeFilter === pill.value"
        @click="emit('update:activeFilter', pill.value)"
      >
        <span>{{ pill.label }}</span>
        <span v-if="typeof pill.count === 'number'" class="pill-count">{{ pill.count }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  activeFilter: {
    type: String,
    default: 'all',
  },
  filters: {
    type: Array,
    default: () => [],
  },
  placeholder: {
    type: String,
    default: 'Filter...',
  },
  totalCount: {
    type: Number,
    default: 0,
  },
  filteredCount: {
    type: Number,
    default: 0,
  },
  itemLabel: {
    type: String,
    default: 'entries',
  },
});

const emit = defineEmits(['update:modelValue', 'update:activeFilter']);

const isFiltered = computed(
  () => Boolean(props.modelValue.trim()) || props.activeFilter !== 'all'
);

function resetAll() {
  emit('update:modelValue', '');
  emit('update:activeFilter', 'all');
}
</script>

<style scoped>
.filter-bar {
  background: var(--color-background-soft);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 0.9rem 1rem;
  margin-bottom: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.filter-controls-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.filter-search-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  flex: 1 1 260px;
  background: var(--color-background);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 0 0.65rem;
  transition: border-color 0.2s ease;
}

.filter-search-wrapper:focus-within {
  border-color: var(--color-primary);
}

.filter-search-icon {
  color: var(--color-primary);
  font-size: 1.05rem;
  margin-right: 0.45rem;
  line-height: 1;
}

.filter-search-input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--color-text);
  font-size: 0.92rem;
  font-family: var(--font-main);
  padding: 0.5rem 0;
  outline: none;
  min-width: 0;
}

.filter-search-input::placeholder {
  color: var(--color-text-muted);
}

.filter-clear-btn {
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  font-size: 1.15rem;
  padding: 0 0.25rem;
  line-height: 1;
}

.filter-clear-btn:hover {
  background: transparent;
  color: var(--color-text);
}

.filter-count {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.filter-count strong {
  color: var(--color-text);
}

.filter-reset-btn {
  background: transparent;
  border: none;
  color: var(--color-link);
  font-size: 0.84rem;
  font-weight: 600;
  padding: 0;
  cursor: pointer;
}

.filter-reset-btn:hover {
  background: transparent;
  color: var(--color-link-hover);
  text-decoration: underline;
}

.filter-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.filter-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.32rem 0.72rem;
  font-size: 0.82rem;
  font-weight: 600;
  border-radius: 999px;
  border: 1px solid var(--border-color);
  background: var(--color-background);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all 0.18s ease;
}

.filter-pill:hover {
  border-color: var(--color-primary);
  color: var(--color-text);
  background: var(--bg-hover);
}

.filter-pill.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-background);
}

.pill-count {
  font-size: 0.72rem;
  opacity: 0.85;
  padding: 0.02rem 0.35rem;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.22);
}

.filter-pill.active .pill-count {
  background: rgba(18, 20, 24, 0.2);
  color: var(--color-background);
}
</style>

<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="search-overlay"
      role="dialog"
      aria-modal="true"
      aria-label="Global campaign search"
      @click.self="close"
    >
      <div class="search-dialog">
        <div class="search-input-row">
          <span class="search-input-icon" aria-hidden="true">⌕</span>
          <input
            ref="inputRef"
            v-model="query"
            type="text"
            class="search-input"
            placeholder="Search sessions, characters, NPCs, locations, lore..."
            aria-label="Search campaign entities"
            @keydown="handleInputKeydown"
          />
          <button
            v-if="query"
            type="button"
            class="clear-query-btn"
            aria-label="Clear search"
            @click="clearQuery"
          >
            &times;
          </button>
          <kbd class="esc-hint">Esc</kbd>
        </div>

        <div class="search-results" ref="resultsRef">
          <p v-if="!query.trim()" class="results-hint">
            Quick Jump — Updated in Session {{ currentSession }} &amp; Key Entries
          </p>

          <template v-if="groupedResults.length">
            <div
              v-for="group in groupedResults"
              :key="group.type"
              class="result-group"
            >
              <div class="group-heading">
                <span aria-hidden="true">{{ group.icon }}</span>
                <span>{{ group.label }}</span>
                <span class="group-count">{{ group.items.length }}</span>
              </div>

              <button
                v-for="item in group.items"
                :key="`${item.type}:${item.id}`"
                type="button"
                class="result-item"
                :class="{ active: item.flatIndex === activeIndex }"
                :data-flat-index="item.flatIndex"
                @mouseenter="activeIndex = item.flatIndex"
                @click="selectItem(item)"
              >
                <div class="result-main">
                  <span class="result-name">{{ item.name }}</span>
                  <span v-if="item.subtitle" class="result-subtitle">{{ item.subtitle }}</span>
                </div>
                <div class="result-badges">
                  <span v-if="item.isNew" class="result-badge badge-current">
                    Session {{ currentSession }}
                  </span>
                  <span v-else-if="item.latestSession" class="result-badge badge-session">
                    S{{ item.latestSession }}
                  </span>
                  <span class="jump-arrow" aria-hidden="true">↵</span>
                </div>
              </button>
            </div>
          </template>

          <div v-else class="no-results">
            <p>No matches found for "{{ query }}".</p>
            <span class="muted">Try searching by character name, location, session number, or lore term.</span>
          </div>
        </div>

        <div class="search-footer">
          <span><kbd>↑</kbd> <kbd>↓</kbd> Navigate</span>
          <span><kbd>↵</kbd> Open</span>
          <span><kbd>Esc</kbd> Close</span>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';
import { getAllSearchableEntities } from '@/store/worldData.js';
import { currentSession } from '@/store/config.js';

const props = defineProps({
  visible: {
    type: Boolean,
    required: true,
  },
});

const emit = defineEmits(['close']);
const router = useRouter();

const inputRef = ref(null);
const resultsRef = ref(null);
const query = ref('');
const activeIndex = ref(0);

const CATEGORY_META = [
  { type: 'session', label: 'Sessions', icon: '🗓️' },
  { type: 'character', label: 'Player Characters', icon: '🛡️' },
  { type: 'npc', label: 'Notable NPCs', icon: '👥' },
  { type: 'location', label: 'Locations', icon: '📍' },
  { type: 'lore', label: 'World Lore', icon: '📜' },
];

const allEntities = getAllSearchableEntities();

let previousOverflow = '';
let isLocked = false;

function normalizeText(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();
}

function fuzzySubsequenceScore(needle, haystack) {
  let hi = 0;
  let consecutive = 0;
  let bestRun = 0;
  for (let ni = 0; ni < needle.length; ni += 1) {
    const ch = needle[ni];
    const found = haystack.indexOf(ch, hi);
    if (found === -1) return 0;
    if (found === hi) {
      consecutive += 1;
      if (consecutive > bestRun) bestRun = consecutive;
    } else {
      consecutive = 1;
    }
    hi = found + 1;
  }
  return 10 + bestRun * 2;
}

function scoreEntity(entity, normalizedQuery) {
  const name = normalizeText(entity.name);
  const id = normalizeText(entity.id);
  const subtitle = normalizeText(entity.subtitle);
  const description = normalizeText(entity.description);
  const type = normalizeText(entity.type);

  if (name === normalizedQuery || id === normalizedQuery) return 200;
  if (name.startsWith(normalizedQuery)) return 140;
  if (name.includes(normalizedQuery)) return 100;
  if (subtitle.includes(normalizedQuery)) return 70;
  if (id.includes(normalizedQuery) || type.includes(normalizedQuery)) return 60;
  if (description.includes(normalizedQuery)) return 40;

  // Multi-word AND match across combined fields
  const tokens = normalizedQuery.split(/\s+/).filter(Boolean);
  if (tokens.length > 1) {
    const combined = `${name} ${subtitle} ${description} ${type}`;
    if (tokens.every((token) => combined.includes(token))) {
      return 55;
    }
  }

  // Fuzzy subsequence on name for short typo-tolerant jumps
  if (normalizedQuery.length >= 2) {
    const fuzzy = fuzzySubsequenceScore(normalizedQuery.replace(/\s+/g, ''), name);
    if (fuzzy > 0) return fuzzy;
  }

  return 0;
}

const matchedItems = computed(() => {
  const trimmed = normalizeText(query.value.trim());

  if (!trimmed) {
    const featured = [];
    const seen = new Set();

    // Prioritize items updated in current session + all PCs
    for (const item of allEntities) {
      const key = `${item.type}:${item.id}`;
      if (item.isNew || item.type === 'character') {
        if (!seen.has(key)) {
          seen.add(key);
          featured.push(item);
        }
      }
    }
    return featured.slice(0, 18);
  }

  return allEntities
    .map((item) => ({ item, score: scoreEntity(item, trimmed) }))
    .filter((entry) => entry.score > 0)
    .sort((a, b) => b.score - a.score || (b.item.latestSession || 0) - (a.item.latestSession || 0))
    .slice(0, 30)
    .map((entry) => entry.item);
});

const groupedResults = computed(() => {
  const groups = [];
  let flatIdx = 0;

  for (const meta of CATEGORY_META) {
    const groupItems = matchedItems.value
      .filter((item) => item.type === meta.type)
      .map((item) => ({
        ...item,
        flatIndex: flatIdx++,
      }));

    if (groupItems.length) {
      groups.push({
        ...meta,
        items: groupItems,
      });
    }
  }

  return groups;
});

const flatResults = computed(() =>
  groupedResults.value.flatMap((group) => group.items)
);

watch(query, () => {
  activeIndex.value = 0;
});

watch(
  () => props.visible,
  async (open) => {
    if (typeof document === 'undefined') return;
    if (open) {
      if (!isLocked) {
        previousOverflow = document.body.style.overflow;
        document.body.style.overflow = 'hidden';
        isLocked = true;
      }
      query.value = '';
      activeIndex.value = 0;
      await nextTick();
      inputRef.value?.focus();
    } else if (isLocked) {
      document.body.style.overflow = previousOverflow;
      isLocked = false;
    }
  }
);

onBeforeUnmount(() => {
  if (typeof document !== 'undefined' && isLocked) {
    document.body.style.overflow = previousOverflow;
    isLocked = false;
  }
});

function close() {
  emit('close');
}

function clearQuery() {
  query.value = '';
  activeIndex.value = 0;
  inputRef.value?.focus();
}

function selectItem(item) {
  if (!item || !item.route) return;
  close();
  router.push(item.route);
}

function scrollActiveIntoView() {
  nextTick(() => {
    const el = resultsRef.value?.querySelector(`[data-flat-index="${activeIndex.value}"]`);
    if (el) {
      el.scrollIntoView({ block: 'nearest' });
    }
  });
}

function handleInputKeydown(event) {
  const total = flatResults.value.length;

  if (event.key === 'Escape') {
    event.preventDefault();
    close();
    return;
  }

  if (!total) return;

  if (event.key === 'ArrowDown') {
    event.preventDefault();
    activeIndex.value = (activeIndex.value + 1) % total;
    scrollActiveIntoView();
  } else if (event.key === 'ArrowUp') {
    event.preventDefault();
    activeIndex.value = (activeIndex.value - 1 + total) % total;
    scrollActiveIntoView();
  } else if (event.key === 'Enter') {
    event.preventDefault();
    const target = flatResults.value[activeIndex.value];
    if (target) {
      selectItem(target);
    }
  }
}
</script>

<style scoped>
.search-overlay {
  position: fixed;
  inset: 0;
  background: rgba(8, 10, 14, 0.8);
  backdrop-filter: blur(3px);
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 10vh 1rem 2rem;
  box-sizing: border-box;
  z-index: 1100;
}

.search-dialog {
  width: min(640px, 100%);
  max-height: 76vh;
  background: var(--color-surface);
  border: 1px solid var(--color-primary);
  border-radius: 10px;
  box-shadow: var(--shadow-lg), 0 0 30px rgba(201, 169, 89, 0.14);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.search-input-row {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.85rem 1rem;
  background: var(--color-background-soft);
  border-bottom: 1px solid var(--border-color);
}

.search-input-icon {
  font-size: 1.25rem;
  color: var(--color-primary);
  line-height: 1;
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--color-text);
  font-size: 1rem;
  font-family: var(--font-main);
  outline: none;
}

.search-input::placeholder {
  color: var(--color-text-muted);
}

.clear-query-btn {
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  font-size: 1.25rem;
  padding: 0.1rem 0.4rem;
  line-height: 1;
}

.clear-query-btn:hover {
  background: transparent;
  color: var(--color-text);
}

.esc-hint {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  background: var(--color-background);
  border: 1px solid var(--border-color);
  color: var(--color-text-muted);
}

.search-results {
  overflow-y: auto;
  padding: 0.65rem 0.75rem;
  flex: 1;
}

.results-hint {
  margin: 0.2rem 0.4rem 0.6rem;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
}

.result-group {
  margin-bottom: 0.85rem;
}

.result-group:last-child {
  margin-bottom: 0.25rem;
}

.group-heading {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.3rem 0.5rem;
  font-family: var(--font-display);
  font-size: 0.8rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-primary);
}

.group-count {
  margin-left: auto;
  font-family: var(--font-main);
  font-size: 0.72rem;
  color: var(--color-text-muted);
}

.result-item {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.58rem 0.7rem;
  border: 1px solid transparent;
  border-radius: 6px;
  background: transparent;
  color: var(--color-text);
  text-align: left;
  cursor: pointer;
  transition: background-color 0.12s ease, border-color 0.12s ease;
}

.result-item:hover,
.result-item.active {
  background: var(--bg-hover);
  border-color: rgba(201, 169, 89, 0.45);
  color: var(--color-text);
}

.result-main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.result-name {
  font-weight: 700;
  font-size: 0.94rem;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-item.active .result-name {
  color: var(--color-highlight);
}

.result-subtitle {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-badges {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  flex-shrink: 0;
}

.result-badge {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.12rem 0.42rem;
  border-radius: 4px;
}

.badge-current {
  background: #ffd54f;
  color: #111;
}

.badge-session {
  background: var(--color-background-mute);
  color: var(--color-text-muted);
}

.jump-arrow {
  color: var(--color-primary);
  opacity: 0;
  font-size: 0.85rem;
}

.result-item.active .jump-arrow {
  opacity: 1;
}

.no-results {
  text-align: center;
  padding: 2rem 1rem;
}

.no-results p {
  margin: 0 0 0.4rem;
  font-weight: 600;
}

.search-footer {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  padding: 0.6rem 1rem;
  background: var(--color-background-soft);
  border-top: 1px solid var(--border-color);
  font-size: 0.76rem;
  color: var(--color-text-muted);
}

.search-footer kbd {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  padding: 0.08rem 0.32rem;
  border-radius: 3px;
  background: var(--color-background);
  border: 1px solid var(--border-color);
  color: var(--color-text);
}
</style>

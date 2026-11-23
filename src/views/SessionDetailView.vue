<template>
  <div class="content-section session-detail-section">
    <!-- Top navigation bar -->
    <div class="session-top-nav">
      <router-link to="/sessions" class="back-link">← All Sessions</router-link>
      <div class="prev-next-links" v-if="session">
        <router-link
          v-if="prevSession"
          :to="`/sessions/${prevSession.id}`"
          class="nav-pill"
        >
          ← {{ prevSession.title }}
        </router-link>
        <router-link
          v-if="nextSession"
          :to="`/sessions/${nextSession.id}`"
          class="nav-pill"
        >
          {{ nextSession.title }} →
        </router-link>
      </div>
    </div>

    <template v-if="session">
      <!-- Session Hero Header -->
      <header class="session-hero">
        <div class="session-meta-row">
          <span class="session-badge" :class="{ upcoming: session.upcoming }">
            {{ session.upcoming ? 'Upcoming Session' : session.title }}
          </span>
          <span v-if="session.date" class="meta-item">📅 {{ session.date }}</span>
          <span v-if="session.time" class="meta-item">🕒 {{ session.time }}</span>
          <span v-if="session.location" class="meta-item">📍 {{ session.location }}</span>
        </div>
        <h1>{{ session.title }}<span v-if="session.subtitle">: {{ session.subtitle }}</span></h1>
        <p class="session-lead">{{ session.description }}</p>

        <!-- Summary / Transcript Toggle -->
        <div v-if="session.transcriptFile" class="view-mode-bar" role="tablist" aria-label="Session view mode">
          <button
            type="button"
            role="tab"
            :aria-selected="activeTab === 'summary'"
            class="mode-tab"
            :class="{ active: activeTab === 'summary' }"
            @click="activeTab = 'summary'"
          >
            📜 Session Summary
          </button>
          <button
            type="button"
            role="tab"
            :aria-selected="activeTab === 'transcript'"
            class="mode-tab"
            :class="{ active: activeTab === 'transcript' }"
            @click="switchToTranscript"
          >
            📝 Full Transcript
          </button>
        </div>
      </header>

      <!-- Main Reader Grid (with Sticky Section TOC when summary has headings) -->
      <div
        v-if="activeTab === 'summary'"
        class="reader-layout"
        :class="{ 'has-toc': tocHeadings.length > 0 }"
      >
        <aside v-if="tocHeadings.length" class="toc-sidebar" aria-label="Session sections">
          <div class="toc-card">
            <h2 class="toc-title">On This Page</h2>
            <nav class="toc-nav">
              <ul>
                <li v-for="heading in tocHeadings" :key="heading.id">
                  <a
                    :href="`#${heading.id}`"
                    class="toc-link"
                    :class="{ active: activeHeadingId === heading.id }"
                    :aria-current="activeHeadingId === heading.id ? 'location' : undefined"
                    @click.prevent="scrollToHeading(heading.id)"
                  >
                    {{ heading.text }}
                  </a>
                </li>
                <li v-if="updatedEntityGroups.length">
                  <a
                    href="#session-entities-updated"
                    class="toc-link toc-link-accent"
                    :class="{ active: activeHeadingId === 'session-entities-updated' }"
                    :aria-current="activeHeadingId === 'session-entities-updated' ? 'location' : undefined"
                    @click.prevent="scrollToHeading('session-entities-updated')"
                  >
                    Entities Updated ({{ totalUpdatedEntities }})
                  </a>
                </li>
              </ul>
            </nav>
          </div>
        </aside>

        <article class="reader-article">
          <div v-if="isLoadingMarkdown" class="loading-box">
            <div class="loading-spinner"></div>
            <p>Loading session chronicle...</p>
          </div>

          <div v-else-if="markdownError" class="error-box">
            <p>{{ markdownError }}</p>
          </div>

          <div
            v-else-if="renderedSummaryHtml"
            class="markdown-body"
            v-html="renderedSummaryHtml"
            @click="handleMarkdownClick"
          ></div>

          <div v-else class="fallback-summary">
            <p v-if="session.upcoming" class="upcoming-callout">
              This session has not been played yet. Check back after {{ session.date }} for the full chronicle.
            </p>
            <div v-if="session.highlights && session.highlights.length" class="highlights-box">
              <h2>Key Moments</h2>
              <ul>
                <li v-for="(item, idx) in session.highlights" :key="idx">{{ item }}</li>
              </ul>
            </div>
          </div>
        </article>
      </div>

      <!-- Transcript Tab -->
      <section v-else class="transcript-section">
        <div v-if="isLoadingTranscript" class="loading-box">
          <div class="loading-spinner"></div>
          <p>Loading corrected transcript...</p>
        </div>
        <div v-else-if="transcriptError" class="error-box">
          <p>{{ transcriptError }}</p>
        </div>
        <div v-else class="transcript-body" v-html="renderedTranscriptHtml"></div>
      </section>

      <!-- Entities Updated in Session N -->
      <section
        v-if="updatedEntityGroups.length"
        id="session-entities-updated"
        class="updated-entities-section"
      >
        <h2>Entities Updated in {{ session.title }}</h2>
        <div class="updated-groups-grid">
          <div
            v-for="group in updatedEntityGroups"
            :key="group.type"
            class="updated-group-card"
          >
            <h3>
              <span aria-hidden="true">{{ group.icon }}</span>
              {{ group.label }}
            </h3>
            <ul class="updated-entity-list">
              <li v-for="entry in group.items" :key="`${group.type}:${entry.id}`">
                <router-link :to="entry.route" class="updated-entity-link">
                  {{ entry.name }}
                </router-link>
                <p v-if="entry.note" class="updated-entity-note">{{ entry.note }}</p>
              </li>
            </ul>
          </div>
        </div>
      </section>

      <!-- Bottom Prev/Next Navigation -->
      <div class="session-bottom-nav">
        <router-link
          v-if="prevSession"
          :to="`/sessions/${prevSession.id}`"
          class="button-link"
        >
          ← {{ prevSession.title }}<span v-if="prevSession.subtitle">: {{ prevSession.subtitle }}</span>
        </router-link>
        <span v-else></span>
        <router-link
          v-if="nextSession"
          :to="`/sessions/${nextSession.id}`"
          class="button-link"
        >
          {{ nextSession.title }}<span v-if="nextSession.subtitle">: {{ nextSession.subtitle }}</span> →
        </router-link>
      </div>
    </template>

    <!-- Not Found State -->
    <div v-else class="session-not-found">
      <h1>Session Not Found</h1>
      <p class="muted">We couldn't find a chronicle entry matching "{{ activeSessionId }}".</p>
      <router-link to="/sessions" class="button-link button-primary">Return to Sessions</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { marked } from 'marked';
import {
  sessions,
  getSession,
  getEntitiesUpdatedInSession,
  resolveEntityByNameOrId,
} from '@/store/worldData.js';
import { parseSessionNumber } from '@/store/config.js';
import { getEntityRoute } from '@/utils/entityHelpers.js';
import { loadSessionMarkdown, loadSessionTranscript } from '@/utils/markdownLoader.js';
import { getCharacterAvatar } from '@/utils/avatars.js';

const props = defineProps({
  id: {
    type: String,
    default: null,
  },
});

const route = useRoute();
const router = useRouter();

const activeSessionId = computed(() => props.id || String(route.params.id || ''));
const session = computed(() => getSession(activeSessionId.value));

const sessionNumber = computed(() =>
  session.value ? parseSessionNumber(session.value.id) : null
);

function getChronologicalKey(s) {
  if (!s || !s.id) return Number.NEGATIVE_INFINITY;
  if (s.id === 'session-minus-1') return -1;
  const parsed = parseSessionNumber(s.id);
  return parsed !== null ? parsed : Number.NEGATIVE_INFINITY;
}

const chronologicalSessions = computed(() =>
  [...sessions].sort((a, b) => getChronologicalKey(a) - getChronologicalKey(b))
);

const currentIndex = computed(() =>
  chronologicalSessions.value.findIndex((s) => s.id === activeSessionId.value)
);

const prevSession = computed(() =>
  currentIndex.value > 0 ? chronologicalSessions.value[currentIndex.value - 1] : null
);

const nextSession = computed(() =>
  currentIndex.value !== -1 && currentIndex.value < chronologicalSessions.value.length - 1
    ? chronologicalSessions.value[currentIndex.value + 1]
    : null
);

const activeTab = ref('summary');
const isLoadingMarkdown = ref(false);
const markdownError = ref('');
const renderedSummaryHtml = ref('');
const tocHeadings = ref([]);
const activeHeadingId = ref('');

const isLoadingTranscript = ref(false);
const transcriptError = ref('');
const renderedTranscriptHtml = ref('');
const loadedTranscriptForId = ref('');

function escapeHtml(text) {
  return String(text || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function slugifyHeading(text) {
  return String(text || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/<[^>]+>/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'section';
}

function stripTags(html) {
  return String(html || '')
    .replace(/<[^>]+>/g, '')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .trim();
}

function extractWikiLabel(rawInner, resolved) {
  const pipeIdx = rawInner.indexOf('|');
  if (pipeIdx !== -1) {
    const alias = rawInner.slice(pipeIdx + 1).trim();
    if (alias) return alias;
  }
  const hashIdx = rawInner.indexOf('#');
  if (hashIdx !== -1) {
    const anchorText = rawInner.slice(hashIdx + 1).trim();
    if (anchorText) return anchorText;
  }
  const target = rawInner.includes('/') ? rawInner.split('/').pop().trim() : rawInner.trim();
  return target || (resolved ? resolved.name : rawInner);
}

function parseSessionMarkdown(rawMarkdown) {
  const withWikiLinks = rawMarkdown.replace(/\[\[([^\]]+)\]\]/g, (_match, rawInner) => {
    const resolved = resolveEntityByNameOrId(rawInner);
    const label = extractWikiLabel(rawInner, resolved);
    if (resolved && resolved.route) {
      const safeRoute = escapeHtml(resolved.route);
      return `<a href="#${safeRoute}" class="wikilink" data-route="${safeRoute}">${escapeHtml(label)}</a>`;
    }
    return `<span class="wikilink-unresolved">${escapeHtml(label)}</span>`;
  });

  // Strip redundant leading H1 since the hero displays the session title
  const withoutTopH1 = withWikiLinks.replace(/^\s*#\s+[^\n]+\n+/, '');
  let html = marked.parse(withoutTopH1);

  const headings = [];
  const usedIds = new Set();

  html = html.replace(/<h2>([\s\S]*?)<\/h2>/gi, (_match, inner) => {
    const plainText = stripTags(inner);
    let baseId = `sec-${slugifyHeading(plainText)}`;
    let uniqueId = baseId;
    let counter = 2;
    while (usedIds.has(uniqueId)) {
      uniqueId = `${baseId}-${counter++}`;
    }
    usedIds.add(uniqueId);
    headings.push({ id: uniqueId, text: plainText });
    return `<h2 id="${uniqueId}">${inner}</h2>`;
  });

  html = html.replace(
    /<table([\s\S]*?)<\/table>/g,
    '<div class="table-scroll-wrapper"><table$1</table></div>'
  );

  return { html, headings };
}

function getSpeakerClass(speaker) {
  const normalized = String(speaker || '')
    .trim()
    .toLowerCase()
    .replace(/['’]/g, '');
  if (normalized === 'gm') return 'speaker-gm';
  if (normalized.includes('nyx')) return 'speaker-nyx';
  if (normalized.includes('ellara')) return 'speaker-ellara';
  if (normalized.includes('berridin')) return 'speaker-berridin';
  if (normalized.includes('ysidor')) return 'speaker-ysidor';
  if (normalized.includes('tsinyra')) return 'speaker-tsinyra';
  if (normalized.includes('witty') || normalized.includes('whitaker')) return 'speaker-witty';
  return 'speaker-unknown';
}

function formatTranscript(content) {
  const lines = content.split('\n').filter((line) => line.trim());
  const out = [];
  let currentSpeaker = null;

  for (const line of lines) {
    const match = line.match(/^\[(\d{2}:\d{2}:\d{2})\]\s*([^:]+):\s*(.*)$/);
    if (match) {
      const [, timestamp, speaker, text] = match;
      const trimmedSpeaker = speaker.trim();
      const isNewSpeaker = currentSpeaker !== null && currentSpeaker !== trimmedSpeaker;
      currentSpeaker = trimmedSpeaker;

      const avatarUrl = getCharacterAvatar(trimmedSpeaker);
      const avatarHtml = avatarUrl
        ? `<img src="${avatarUrl}" alt="${escapeHtml(trimmedSpeaker)}" class="transcript-avatar" />`
        : `<span class="transcript-avatar-placeholder">${escapeHtml(trimmedSpeaker.charAt(0))}</span>`;

      const speakerClass = getSpeakerClass(trimmedSpeaker);
      out.push(
        `<div class="transcript-line${isNewSpeaker ? ' new-speaker' : ''}">` +
          `<span class="transcript-timestamp">${escapeHtml(timestamp)}</span>` +
          `${avatarHtml}` +
          `<span class="transcript-speaker ${speakerClass}">${escapeHtml(trimmedSpeaker)}:</span>` +
          `<span class="transcript-text">${escapeHtml(text)}</span>` +
          `</div>`
      );
    } else if (line.trim()) {
      out.push(`<div class="transcript-line transcript-plain">${escapeHtml(line)}</div>`);
    }
  }
  return out.join('');
}

async function loadSummaryForCurrentSession() {
  renderedSummaryHtml.value = '';
  tocHeadings.value = [];
  activeHeadingId.value = '';
  markdownError.value = '';

  const current = session.value;
  if (!current || !current.summaryFile) {
    isLoadingMarkdown.value = false;
    return;
  }

  isLoadingMarkdown.value = true;
  try {
    const raw = await loadSessionMarkdown(current.summaryFile);
    const { html, headings } = parseSessionMarkdown(raw);
    renderedSummaryHtml.value = html;
    tocHeadings.value = headings;
    if (headings.length) {
      activeHeadingId.value = headings[0].id;
    }
  } catch (err) {
    console.error('Failed to load session markdown:', err);
    markdownError.value = 'Unable to load the detailed summary for this session.';
  } finally {
    isLoadingMarkdown.value = false;
  }
}

async function switchToTranscript() {
  activeTab.value = 'transcript';
  const current = session.value;
  if (!current || !current.transcriptFile) return;
  if (loadedTranscriptForId.value === current.id && renderedTranscriptHtml.value) return;

  isLoadingTranscript.value = true;
  transcriptError.value = '';
  try {
    const raw = await loadSessionTranscript(current.transcriptFile);
    renderedTranscriptHtml.value = formatTranscript(raw);
    loadedTranscriptForId.value = current.id;
  } catch (err) {
    console.error('Failed to load session transcript:', err);
    transcriptError.value = 'Unable to load the transcript for this session.';
  } finally {
    isLoadingTranscript.value = false;
  }
}

function scrollToHeading(id) {
  activeHeadingId.value = id;
  scrollLockUntil = performance.now() + 700;
  const target = document.getElementById(id);
  if (target) {
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function handleMarkdownClick(event) {
  const link = event.target.closest('a');
  if (!link) return;
  const dataRoute = link.getAttribute('data-route');
  if (dataRoute) {
    event.preventDefault();
    router.push(dataRoute);
    return;
  }
  const href = link.getAttribute('href') || '';
  if (href.startsWith('#/')) {
    event.preventDefault();
    router.push(href.slice(1));
  }
}

function getSessionNote(entity, num) {
  if (!Array.isArray(entity.history)) return '';
  return entity.history
    .filter((entry) => entry && entry.session === num && entry.note)
    .map((entry) => entry.note)
    .join(' • ');
}

const updatedEntityGroups = computed(() => {
  const num = sessionNumber.value;
  if (!Number.isFinite(num) || num <= 0) return [];
  const digest = getEntitiesUpdatedInSession(num);

  const defs = [
    { type: 'character', key: 'characters', label: 'Characters', icon: '🛡️' },
    { type: 'npc', key: 'npcs', label: 'NPCs', icon: '👥' },
    { type: 'location', key: 'locations', label: 'Locations', icon: '📍' },
    { type: 'lore', key: 'lore', label: 'Lore', icon: '📜' },
  ];

  return defs
    .map((def) => {
      const list = Array.isArray(digest[def.key]) ? digest[def.key] : [];
      return {
        ...def,
        items: list.map((entity) => ({
          id: entity.id,
          name: def.type === 'lore' ? entity.term : entity.name,
          route: getEntityRoute(def.type, entity.id),
          note: getSessionNote(entity, num),
        })),
      };
    })
    .filter((group) => group.items.length > 0);
});

const totalUpdatedEntities = computed(() =>
  updatedEntityGroups.value.reduce((sum, group) => sum + group.items.length, 0)
);

const trackedSectionIds = computed(() => [
  ...tocHeadings.value.map((heading) => heading.id),
  ...(updatedEntityGroups.value.length ? ['session-entities-updated'] : []),
]);

let scrollSpyRaf = 0;
let scrollLockUntil = 0;

function updateActiveHeading() {
  if (activeTab.value !== 'summary' || !trackedSectionIds.value.length) return;
  const tracked = trackedSectionIds.value
    .map((id) => ({ id, el: document.getElementById(id) }))
    .filter((item) => item.el);
  if (!tracked.length) return;

  if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 24) {
    activeHeadingId.value = tracked[tracked.length - 1].id;
    return;
  }

  const offset = Math.min(140, Math.max(96, window.innerHeight * 0.18));
  let currentId = tracked[0].id;
  for (const item of tracked) {
    if (item.el.getBoundingClientRect().top <= offset) {
      currentId = item.id;
    } else {
      break;
    }
  }
  activeHeadingId.value = currentId;
}

function scheduleScrollSpy() {
  if (performance.now() < scrollLockUntil || scrollSpyRaf) return;
  scrollSpyRaf = window.requestAnimationFrame(() => {
    scrollSpyRaf = 0;
    updateActiveHeading();
  });
}

function clearScrollLock() {
  scrollLockUntil = 0;
}

watch([renderedSummaryHtml, isLoadingMarkdown, activeTab], async () => {
  if (activeTab.value === 'summary' && !isLoadingMarkdown.value) {
    await nextTick();
    updateActiveHeading();
  }
});

onMounted(() => {
  window.addEventListener('scroll', scheduleScrollSpy, { passive: true });
  window.addEventListener('resize', scheduleScrollSpy, { passive: true });
  window.addEventListener('wheel', clearScrollLock, { passive: true });
  window.addEventListener('touchstart', clearScrollLock, { passive: true });
  updateActiveHeading();
});

onBeforeUnmount(() => {
  window.removeEventListener('scroll', scheduleScrollSpy);
  window.removeEventListener('resize', scheduleScrollSpy);
  window.removeEventListener('wheel', clearScrollLock);
  window.removeEventListener('touchstart', clearScrollLock);
  if (scrollSpyRaf) {
    window.cancelAnimationFrame(scrollSpyRaf);
    scrollSpyRaf = 0;
  }
});

watch(
  () => activeSessionId.value,
  async () => {
    renderedTranscriptHtml.value = '';
    loadedTranscriptForId.value = '';
    transcriptError.value = '';
    activeTab.value = route.query.view === 'transcript' && session.value?.transcriptFile
      ? 'transcript'
      : 'summary';
    await loadSummaryForCurrentSession();
    if (activeTab.value === 'transcript') {
      await switchToTranscript();
    }
  },
  { immediate: true }
);
</script>

<style scoped>
.session-detail-section {
  overflow: clip;
}

.session-top-nav {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--border-color);
}

.back-link {
  font-weight: 700;
  color: var(--color-link);
}

.prev-next-links {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.nav-pill {
  padding: 0.3rem 0.75rem;
  border-radius: 999px;
  border: 1px solid var(--border-color);
  background: var(--color-background-soft);
  color: var(--color-link);
  font-size: 0.86rem;
  font-weight: 600;
}

.nav-pill:hover {
  border-color: var(--color-primary);
  color: var(--color-highlight);
  border-bottom-color: var(--color-primary);
}

.session-hero {
  margin-bottom: 1.75rem;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid var(--border-color);
}

.session-hero h1 {
  font-size: clamp(1.75rem, 3.6vw, 2.45rem);
  margin: 0.5rem 0 0.85rem;
}

.session-meta-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.9rem;
  color: var(--text-muted);
}

.session-badge {
  font-family: var(--font-display);
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
  background: rgba(201, 169, 89, 0.16);
  color: var(--color-primary);
  border: 1px solid rgba(201, 169, 89, 0.45);
}

.session-badge.upcoming {
  background: var(--color-primary);
  color: var(--color-background);
}

.session-lead {
  margin: 1rem 0 0;
  font-size: 1.03rem;
  color: var(--color-text);
  line-height: 1.68;
}

.view-mode-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  margin-top: 1.15rem;
}

.mode-tab {
  padding: 0.45rem 0.95rem;
  font-size: 0.9rem;
  font-weight: 600;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background: var(--color-background-soft);
  color: var(--color-text-muted);
}

.mode-tab:hover {
  border-color: var(--color-primary);
  color: var(--color-text);
  background: var(--bg-hover);
}

.mode-tab.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-background);
}

/* Reader Layout with Sticky TOC */
.reader-layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
  align-items: start;
}

.reader-layout.has-toc {
  grid-template-columns: 240px minmax(0, 1fr);
}

.toc-sidebar {
  position: sticky;
  top: 1.25rem;
}

.toc-card {
  background: var(--color-background-soft);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1rem;
  max-height: calc(100vh - 2.5rem);
  overflow-y: auto;
}

.toc-title {
  margin: 0 0 0.7rem;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-primary);
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0.45rem;
}

.toc-nav {
  background: transparent;
  box-shadow: none;
  border: none;
  padding: 0;
  margin: 0;
}

.toc-nav::before {
  display: none;
}

.toc-nav ul {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 0.25rem;
}

.toc-link {
  display: block;
  font-family: var(--font-main);
  font-size: 0.84rem;
  line-height: 1.4;
  padding: 0.35rem 0.55rem;
  border-radius: 4px;
  border-left: 2px solid transparent;
  border-bottom: none;
  color: var(--color-text-muted);
  white-space: normal;
}

.toc-link:hover,
.toc-link.active {
  color: var(--color-highlight);
  background: rgba(201, 169, 89, 0.1);
  border-left-color: var(--color-primary);
  border-bottom: none;
}

.toc-link-accent {
  margin-top: 0.35rem;
  padding-top: 0.5rem;
  border-top: 1px solid rgba(var(--border-color-rgb), 0.5);
  color: var(--color-link);
}

.reader-article {
  min-width: 0;
}

.markdown-body {
  line-height: 1.76;
  font-size: 1.02rem;
}

.markdown-body :deep(h2) {
  margin-top: 2rem;
  margin-bottom: 0.75rem;
  font-size: 1.45rem;
  padding-bottom: 0.35rem;
  border-bottom: 1px solid rgba(var(--border-color-rgb), 0.7);
  scroll-margin-top: 1.5rem;
}

.markdown-body :deep(h2:first-child) {
  margin-top: 0;
}

.markdown-body :deep(h3) {
  margin-top: 1.5rem;
  margin-bottom: 0.5rem;
  font-size: 1.18rem;
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid rgba(var(--border-color-rgb), 0.55);
  margin: 1.75rem 0;
}

.markdown-body :deep(blockquote) {
  margin: 1rem 0;
  padding: 0.75rem 1rem;
  border-left: 3px solid var(--color-primary);
  background: var(--color-background-soft);
  border-radius: 0 6px 6px 0;
  font-style: italic;
}

.markdown-body :deep(.table-scroll-wrapper) {
  width: 100%;
  overflow-x: auto;
  margin: 1.25rem 0;
}

.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.92rem;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid var(--border-color);
  padding: 0.5rem 0.85rem;
  text-align: left;
}

.markdown-body :deep(th) {
  background: var(--color-background-soft);
  color: var(--color-heading);
}

.markdown-body :deep(tr:nth-child(even)) {
  background: var(--color-background-mute);
}

.markdown-body :deep(a) {
  color: var(--color-link);
  font-weight: 600;
}

.markdown-body :deep(a:hover) {
  color: var(--color-link-hover);
}

.upcoming-callout {
  padding: 1rem 1.25rem;
  border-left: 3px solid var(--color-primary);
  background: var(--color-background-soft);
  border-radius: 0 6px 6px 0;
  font-style: italic;
}

.highlights-box ul {
  padding-left: 1.4rem;
}

.highlights-box li {
  margin-bottom: 0.5rem;
}

/* Transcript Panel */
.transcript-body {
  background: var(--color-background-soft);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1rem;
  font-size: 0.92rem;
  line-height: 1.55;
}

.transcript-body :deep(.transcript-line) {
  display: flex;
  align-items: flex-start;
  padding: 0.35em 0.5em;
  border-radius: 4px;
  gap: 0.55em;
}

.transcript-body :deep(.transcript-line:hover) {
  background: var(--bg-hover);
}

.transcript-body :deep(.transcript-line.new-speaker) {
  margin-top: 0.6em;
  border-top: 1px solid var(--border-color);
  padding-top: 0.6em;
}

.transcript-body :deep(.transcript-avatar),
.transcript-body :deep(.transcript-avatar-placeholder) {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  flex-shrink: 0;
  border: 1px solid var(--border-color);
}

.transcript-body :deep(.transcript-avatar) {
  object-fit: cover;
}

.transcript-body :deep(.transcript-avatar-placeholder) {
  background: var(--color-background-mute);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72em;
  font-weight: 700;
  color: var(--text-muted);
}

.transcript-body :deep(.transcript-timestamp) {
  font-family: var(--font-mono);
  font-size: 0.76em;
  color: var(--text-muted);
  min-width: 56px;
  flex-shrink: 0;
}

.transcript-body :deep(.transcript-speaker) {
  font-weight: 700;
  min-width: 82px;
  flex-shrink: 0;
}

.transcript-body :deep(.speaker-gm) { color: #e6a23c; }
.transcript-body :deep(.speaker-nyx) { color: #9a8fbd; }
.transcript-body :deep(.speaker-ellara) { color: #d4a855; }
.transcript-body :deep(.speaker-berridin) { color: #c49a6c; }
.transcript-body :deep(.speaker-ysidor) { color: #7ba3c4; }
.transcript-body :deep(.speaker-tsinyra) { color: #7cb587; }
.transcript-body :deep(.speaker-witty) { color: #b08dc9; }
.transcript-body :deep(.speaker-unknown) { color: var(--text-muted); }

/* Updated Entities Section */
.updated-entities-section {
  margin-top: 2.5rem;
  padding-top: 1.75rem;
  border-top: 1px solid var(--border-color);
  scroll-margin-top: 1.5rem;
}

.updated-entities-section h2 {
  margin-top: 0;
  font-size: 1.55rem;
}

.updated-groups-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.updated-group-card {
  background: var(--color-background-soft);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1rem 1.15rem;
}

.updated-group-card h3 {
  margin: 0 0 0.75rem;
  font-size: 1.05rem;
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.updated-entity-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

.updated-entity-link {
  font-weight: 700;
  color: var(--color-link);
}

.updated-entity-note {
  margin: 0.2rem 0 0;
  font-size: 0.85rem;
  color: var(--text-muted);
  line-height: 1.45;
}

/* Bottom Navigation */
.session-bottom-nav {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 2.25rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--border-color);
}

.session-bottom-nav .button-link {
  margin-top: 0;
}

/* Loading & Error States */
.loading-box,
.error-box,
.session-not-found {
  text-align: center;
  padding: 2.5rem 1rem;
}

.loading-spinner {
  width: 44px;
  height: 44px;
  margin: 0 auto 1rem;
  border: 4px solid rgba(255, 255, 255, 0.12);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 860px) {
  .reader-layout.has-toc {
    grid-template-columns: 1fr;
  }

  .toc-sidebar {
    position: static;
  }
}
</style>

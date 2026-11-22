<template>
  <div class="content-section">
    <h1>Campaign Sessions</h1>
    <p class="story-link-row">
      <router-link to="/sessions/story-so-far" class="story-link">
        Read The Story So Far →
      </router-link>
    </p>

    <FilterBar
      v-model="searchQuery"
      v-model:activeFilter="activeFilter"
      :filters="filterPills"
      :totalCount="sessions.length"
      :filteredCount="filteredSessions.length"
      itemLabel="sessions"
      placeholder="Search sessions by title, location, summary, or key moment..."
    />

    <div v-if="filteredSessions.length" class="sessions-container">
      <article
        v-for="session in filteredSessions"
        :key="session.id"
        class="session-card"
        :class="{ 'is-upcoming': session.upcoming }"
        :id="session.id"
      >
        <div class="session-header" :class="{ upcoming: session.upcoming }">
          <div class="header-top-line">
            <h3 class="session-title">
              <router-link :to="`/sessions/${session.id}`" class="session-title-link">
                {{ session.title }}
              </router-link>
              <span v-if="session.upcoming" class="upcoming-badge">Upcoming</span>
            </h3>
            <span class="session-date">{{ session.date }}</span>
          </div>
          <p class="session-subtitle">{{ session.subtitle }}</p>
          <p v-if="session.location" class="session-location">📍 {{ session.location }}</p>
        </div>

        <div class="session-content">
          <div v-if="session.upcoming" class="upcoming-message">
            <p>{{ session.description }}</p>
            <div class="session-links">
              <router-link :to="`/sessions/${session.id}`" class="read-more-link">
                View Session Details →
              </router-link>
            </div>
          </div>

          <div v-else class="session-summary">
            <p>{{ session.description }}</p>

            <div class="session-links">
              <router-link :to="`/sessions/${session.id}`" class="read-more-link">
                📜 {{ session.summaryFile ? 'Read Full Session' : 'View Session Details' }} →
              </router-link>

              <button
                v-if="session.transcriptFile"
                type="button"
                class="transcript-link"
                @click="showTranscript(session)"
              >
                📝 Quick View Transcript
              </button>
            </div>

            <div v-if="session.highlights && session.highlights.length" class="highlights">
              <h4>Key Moments:</h4>
              <ul>
                <li v-for="(highlight, i) in session.highlights" :key="`${session.id}-hl-${i}`">
                  {{ highlight }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </article>
    </div>

    <p v-else class="empty-message">No sessions match your current filter.</p>

    <FullTextModal
      :visible="isOpen"
      :title="modalTitle"
      :text="modalContent"
      :loading="Boolean(modalMeta.loading)"
      :contentClass="modalMeta.contentClass || ''"
      @close="closeModal"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { sessions } from '@/store/worldData.js';
import FullTextModal from '@/components/FullTextModal.vue';
import FilterBar from '@/components/FilterBar.vue';
import { loadSessionTranscript } from '@/utils/markdownLoader.js';
import { getCharacterAvatar } from '@/utils/avatars.js';
import { useModal } from '@/composables/useModal.js';

const { isOpen, modalTitle, modalContent, modalMeta, openModal, closeModal } = useModal();

const searchQuery = ref('');
const activeFilter = ref('all');

const filterPills = computed(() => [
  { value: 'all', label: 'All', count: sessions.length },
  {
    value: 'completed',
    label: 'Completed',
    count: sessions.filter((s) => !s.upcoming).length,
  },
  {
    value: 'upcoming',
    label: 'Upcoming',
    count: sessions.filter((s) => s.upcoming).length,
  },
  {
    value: 'transcript',
    label: 'With Transcript',
    count: sessions.filter((s) => Boolean(s.transcriptFile)).length,
  },
]);

const filteredSessions = computed(() => {
  const q = searchQuery.value.trim().toLowerCase();

  return sessions.filter((session) => {
    if (activeFilter.value === 'completed' && session.upcoming) return false;
    if (activeFilter.value === 'upcoming' && !session.upcoming) return false;
    if (activeFilter.value === 'transcript' && !session.transcriptFile) return false;

    if (!q) return true;
    const haystack = [
      session.title,
      session.subtitle,
      session.location,
      session.date,
      session.description,
      ...(Array.isArray(session.highlights) ? session.highlights : []),
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase();
    return haystack.includes(q);
  });
});

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

function escapeHtml(text) {
  return String(text || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function formatTranscript(content) {
  const lines = content.split('\n').filter((line) => line.trim());
  const formattedLines = [];
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
      formattedLines.push(
        `<div class="transcript-line${isNewSpeaker ? ' new-speaker' : ''}">` +
          `<span class="transcript-timestamp">${escapeHtml(timestamp)}</span>` +
          `${avatarHtml}` +
          `<span class="transcript-speaker ${speakerClass}">${escapeHtml(trimmedSpeaker)}:</span>` +
          `<span class="transcript-text">${escapeHtml(text)}</span>` +
          `</div>`
      );
    } else if (line.trim()) {
      formattedLines.push(
        `<div class="transcript-line transcript-plain">${escapeHtml(line)}</div>`
      );
    }
  }

  return formattedLines.join('');
}

async function showTranscript(session) {
  const title = `${session.title}: ${session.subtitle} — Transcript`;
  openModal(title, '', { loading: true, contentClass: 'transcript-content' });

  try {
    const transcriptContent = await loadSessionTranscript(session.transcriptFile);
    openModal(title, formatTranscript(transcriptContent), {
      loading: false,
      contentClass: 'transcript-content',
    });
  } catch (error) {
    console.error('Error loading transcript:', error);
    openModal(title, '<p>Unable to load the session transcript file.</p>', {
      loading: false,
      contentClass: 'transcript-content',
    });
  }
}
</script>

<style scoped>
.story-link-row {
  text-align: center;
  margin: 0 auto 1.5rem;
}

.story-link {
  font-weight: 700;
  text-decoration: none;
  color: var(--color-highlight);
}

.story-link:hover {
  color: var(--color-link-hover);
  text-decoration: underline;
}

.sessions-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.session-card {
  background: var(--gradient-primary);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.session-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border-accent);
}

/* Fixed selector: .upcoming is applied directly on .session-header */
.session-header.upcoming {
  background: linear-gradient(90deg, rgba(201, 169, 89, 0.16) 0%, rgba(91, 176, 207, 0.12) 100%);
  border-bottom-color: rgba(201, 169, 89, 0.45);
}

.header-top-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
}

.session-title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.4rem;
  line-height: 1.2;
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.session-title-link {
  color: var(--color-primary);
  border-bottom: none;
}

.session-title-link:hover {
  color: var(--color-highlight);
  text-decoration: underline;
}

.upcoming-badge {
  font-family: var(--font-main);
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  background: var(--color-primary);
  color: var(--color-background);
}

.session-subtitle {
  margin: 0.3rem 0 0;
  font-size: 0.98rem;
  color: var(--color-text);
  font-style: italic;
}

.session-location {
  margin: 0.25rem 0 0;
  font-size: 0.85rem;
  color: var(--text-muted);
}

.session-date {
  font-family: var(--font-accent);
  font-size: 0.9em;
  font-weight: bold;
  padding: 0.3em 0.65em;
  border-radius: 4px;
  background-color: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(var(--border-color-rgb), 0.6);
  white-space: nowrap;
}

.session-content {
  padding: 1.35rem 1.5rem;
}

.upcoming-message {
  font-style: italic;
  border-left: 3px solid var(--color-primary);
  padding-left: 1rem;
}

.highlights {
  margin-top: 1.25rem;
}

.highlights h4 {
  margin-bottom: 0.5rem;
  color: var(--color-primary);
}

.highlights ul {
  padding-left: 1.4rem;
  margin: 0;
}

.highlights li {
  margin-bottom: 0.45rem;
}

.empty-message {
  text-align: center;
  margin-top: 2rem;
  color: var(--text-muted);
}

.session-links {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1.15rem;
  margin-top: 0.85rem;
}

.read-more-link {
  color: var(--color-highlight);
  cursor: pointer;
  text-decoration: none;
  font-weight: 700;
  font-size: 1rem;
  display: inline-block;
  border-bottom: none;
}

.read-more-link:hover {
  color: var(--color-link-hover);
  text-decoration: underline;
}

.transcript-link {
  color: var(--color-link);
  background: transparent;
  border: none;
  padding: 0;
  cursor: pointer;
  font-weight: 700;
  font-size: 0.95rem;
}

.transcript-link:hover {
  background: transparent;
  color: var(--color-link-hover);
  text-decoration: underline;
}

@media (max-width: 600px) {
  .header-top-line {
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .session-header,
  .session-content {
    padding: 1rem 1.1rem;
  }
}
</style>

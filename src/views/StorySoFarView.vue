<template>
  <div class="content-section story-page">
    <div class="story-header">
      <h1>The Story So Far</h1>
      <p class="coverage-text">
        An unlikely party, a darkness in the heart of the duchy, a light in the hearts of our heroes.
      </p>
      <p v-if="latestCompletedSession" class="coverage-meta">
        Chronicle through {{ latestCompletedSession.title }} ({{ latestCompletedSession.date }})
      </p>
    </div>

    <article v-if="preambleParagraphs.length || chronicleBeats.length" class="story-manuscript">
      <div v-if="preambleParagraphs.length" class="story-preamble">
        <p v-for="(paragraph, index) in preambleParagraphs" :key="`preamble-${index}`">
          {{ paragraph }}
        </p>
      </div>

      <section
        v-for="beat in chronicleBeats"
        :key="beat.sessionId"
        class="story-beat"
      >
        <div class="beat-meta">
          <router-link :to="`/sessions/${beat.sessionId}`" class="beat-session-link">
            {{ beat.title }}<span v-if="beat.subtitle"> · {{ beat.subtitle }}</span>
          </router-link>
        </div>
        <p class="beat-text">{{ beat.text }}</p>
      </section>
    </article>

    <p v-else class="empty-message">
      No session records were found to build the chronicle.
    </p>

    <div class="story-footer-actions">
      <router-link to="/sessions" class="button-link">
        Browse All Sessions
      </router-link>
      <router-link
        v-if="latestCompletedSession"
        :to="`/sessions/${latestCompletedSession.id}`"
        class="button-link button-primary"
      >
        Read {{ latestCompletedSession.title }} →
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { sessions, storyPreamble } from '@/store/sessions.js';
import { parseSessionNumber } from '@/store/config.js';

const preambleParagraphs = computed(() =>
  typeof storyPreamble === 'string'
    ? storyPreamble
        .split(/\n\s*\n/)
        .map((part) => part.trim())
        .filter(Boolean)
    : []
);

const completedNumberedSessions = computed(() =>
  sessions
    .filter((session) => session && session.upcoming === false)
    .map((session) => ({
      ...session,
      sessionNumber: parseSessionNumber(session.id),
    }))
    .filter((session) => Number.isFinite(session.sessionNumber) && session.sessionNumber >= 1)
    .sort((a, b) => a.sessionNumber - b.sessionNumber)
);

const latestCompletedSession = computed(() => {
  const list = completedNumberedSessions.value;
  return list.length ? list[list.length - 1] : null;
});

const chronicleBeats = computed(() => {
  const list = completedNumberedSessions.value;
  if (!list.length) return [];

  const authoredBeats = list.filter(
    (session) => typeof session.storyBeat === 'string' && session.storyBeat.trim().length > 0
  );
  const lastAuthoredNumber = authoredBeats.length
    ? authoredBeats[authoredBeats.length - 1].sessionNumber
    : 0;

  const beats = [];
  for (const session of list) {
    const hasBeat = typeof session.storyBeat === 'string' && session.storyBeat.trim().length > 0;
    if (hasBeat) {
      beats.push({
        sessionId: session.id,
        title: session.title,
        subtitle: session.subtitle,
        text: session.storyBeat.trim(),
      });
    } else if (session.sessionNumber > lastAuthoredNumber && session.description) {
      beats.push({
        sessionId: session.id,
        title: session.title,
        subtitle: session.subtitle,
        text: session.description.trim(),
      });
    }
  }
  return beats;
});
</script>

<style scoped>
.story-page {
  max-width: 980px;
  margin: 0 auto;
}

.story-header {
  text-align: center;
  margin-bottom: 1.5rem;
}

.story-header h1::after {
  left: 50%;
  transform: translateX(-50%);
}

.coverage-text {
  text-align: center;
  margin: 1rem auto 0.35rem;
  color: var(--color-text);
  font-style: italic;
  max-width: 700px;
}

.coverage-meta {
  text-align: center;
  margin: 0 auto;
  font-size: 0.88rem;
  color: var(--text-muted);
}

.story-manuscript {
  background: var(--gradient-primary);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 1.5rem 1.75rem;
}

.story-preamble {
  padding-bottom: 1.25rem;
  margin-bottom: 1.25rem;
  border-bottom: 1px solid rgba(var(--border-color-rgb), 0.7);
}

.story-preamble p {
  margin: 0 0 1rem;
  line-height: 1.75;
  text-wrap: pretty;
  font-size: 1.03rem;
}

.story-preamble p:last-child {
  margin-bottom: 0;
}

.story-beat {
  margin-bottom: 1.25rem;
  padding-left: 1rem;
  border-left: 2px solid rgba(201, 169, 89, 0.38);
}

.story-beat:last-child {
  margin-bottom: 0;
}

.beat-meta {
  margin-bottom: 0.3rem;
}

.beat-session-link {
  font-family: var(--font-display);
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--color-link);
  letter-spacing: 0.03em;
}

.beat-session-link:hover {
  color: var(--color-link-hover);
}

.beat-text {
  margin: 0;
  line-height: 1.74;
  text-wrap: pretty;
}

.story-footer-actions {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 1.75rem;
}

.story-footer-actions .button-link {
  margin-top: 0;
}

.empty-message {
  text-align: center;
  color: var(--text-muted);
  font-style: italic;
}

@media (max-width: 600px) {
  .story-manuscript {
    padding: 1.15rem 1.1rem;
  }
}
</style>

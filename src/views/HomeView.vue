<template>
  <div class="content-section home-view">
    <!-- Atmospheric Gaslamp Hero -->
    <section class="hero-banner">
      <img src="../assets/gaslamp.jpg" alt="Bastion City gaslamp streets" class="hero-image" />
      <div class="hero-overlay">
        <p class="hero-eyebrow">{{ worldName }} · 651 AE</p>
        <h1 class="hero-title">{{ campaignName }}</h1>
        <p class="hero-tagline">
          Crystal lamps burn bright in Bastion City, casting deep shadows over the truth beneath.
        </p>
        <div class="hero-actions">
          <router-link
            v-if="latestCompletedSession"
            :to="`/sessions/${latestCompletedSession.id}`"
            class="button-link button-primary"
          >
            Read {{ latestCompletedSession.title }}
          </router-link>
          <router-link to="/sessions/story-so-far" class="button-link hero-secondary-btn">
            The Story So Far
          </router-link>
        </div>
      </div>
    </section>

    <!-- Campaign Quick Info -->
    <section class="campaign-quick-info" aria-label="Campaign status">
      <div class="info-card">
        <h3 class="fancy-title">Current Location</h3>
        <p>{{ currentLocation }}</p>
      </div>

      <div class="info-card">
        <h3 class="fancy-title">Current Quest</h3>
        <p>{{ currentQuest }}</p>
      </div>

      <div class="info-card">
        <h3 class="fancy-title">Next Session</h3>
        <p>{{ nextSessionLabel }}</p>
      </div>
    </section>

    <!-- Where We Left Off & What Comes Next -->
    <section class="session-bridge" v-if="latestRecap || nextStepsList.length || nextSessionFallback">
      <div class="bridge-card" v-if="latestRecap">
        <div class="bridge-card-header">
          <h3 class="fancy-title">Where We Left Off</h3>
          <router-link
            v-if="latestCompletedSession"
            :to="`/sessions/${latestCompletedSession.id}`"
            class="bridge-link"
          >
            {{ latestCompletedSession.title }} →
          </router-link>
        </div>
        <p>{{ latestRecap }}</p>
      </div>

      <div class="bridge-card" v-if="nextStepsList.length || nextSessionFallback">
        <div class="bridge-card-header">
          <h3 class="fancy-title">What Comes Next</h3>
          <router-link
            v-if="upcomingSession"
            :to="`/sessions/${upcomingSession.id}`"
            class="bridge-link"
          >
            {{ upcomingSession.title }} →
          </router-link>
        </div>
        <ul v-if="nextStepsList.length" class="next-steps-list">
          <li v-for="(step, idx) in nextStepsList" :key="idx">{{ step }}</li>
        </ul>
        <p v-else>{{ nextSessionFallback }}</p>
      </div>
    </section>

    <!-- Party Quick-Cards -->
    <section class="home-section">
      <div class="section-heading-row">
        <h2>The Party</h2>
        <router-link to="/characters" class="section-all-link">All Characters →</router-link>
      </div>
      <div class="party-grid">
        <router-link
          v-for="pc in characters"
          :key="pc.id"
          :to="`/characters/${pc.id}`"
          class="party-card"
        >
          <div class="party-avatar-wrap">
            <img
              v-if="pc.avatarUrl"
              :src="pc.avatarUrl"
              :alt="pc.name"
              class="party-avatar"
            />
            <span v-else class="party-initials">{{ pc.name.charAt(0) }}</span>
          </div>
          <div class="party-meta">
            <span class="party-name">{{ pc.name }}</span>
            <span class="party-sub">{{ pc.race }} {{ pc.class }}</span>
            <span class="party-level">Level {{ pc.level }}</span>
          </div>
        </router-link>
      </div>
    </section>

    <!-- Automatic New & Updated in Session N Feed -->
    <section v-if="updatedFeedGroups.length" class="home-section">
      <div class="section-heading-row">
        <h2>New &amp; Updated in Session {{ activeSessionNum }}</h2>
        <router-link
          v-if="latestCompletedSession"
          :to="`/sessions/${latestCompletedSession.id}`"
          class="section-all-link"
        >
          Full Session Notes →
        </router-link>
      </div>

      <div class="updated-groups">
        <div v-for="group in updatedFeedGroups" :key="group.type" class="updated-group">
          <h3 class="updated-group-title">
            <span aria-hidden="true">{{ group.icon }}</span>
            {{ group.label }}
          </h3>
          <div class="updated-items">
            <router-link
              v-for="entry in group.items"
              :key="`${group.type}:${entry.id}`"
              :to="entry.route"
              class="updated-item-card"
            >
              <div class="updated-item-top">
                <span class="updated-item-name">{{ entry.name }}</span>
                <span
                  v-if="entry.badge"
                  :class="entry.badge === 'New' ? 'badge-new' : 'badge-updated'"
                >
                  {{ entry.badge }}
                </span>
              </div>
              <p v-if="entry.note" class="updated-item-note">{{ entry.note }}</p>
            </router-link>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { sessions } from '@/store/sessions.js';
import { characters } from '@/store/characters.js';
import { currentSession, parseSessionNumber } from '@/store/config.js';
import { getEntitiesUpdatedInSession } from '@/store/worldData.js';
import { badgeLabel, getEntityRoute } from '@/utils/entityHelpers.js';

const campaignName = 'A Blinding Light';
const worldName = 'The Hariolar Empire';

const upcomingSession = computed(
  () => sessions.find((session) => session && session.upcoming === true) || null
);

const latestCompletedSession = computed(() => {
  const completed = sessions
    .filter((session) => session && session.upcoming === false)
    .map((session) => ({
      ...session,
      sessionNumber: parseSessionNumber(session.id),
    }))
    .filter((session) => Number.isFinite(session.sessionNumber))
    .sort((a, b) => b.sessionNumber - a.sessionNumber);
  return completed[0] || null;
});

const activeSessionNum = computed(
  () => latestCompletedSession.value?.sessionNumber ?? currentSession
);

const currentLocation = computed(
  () => upcomingSession.value?.location || latestCompletedSession.value?.location || 'Bastion City'
);

const currentQuest = computed(
  () => upcomingSession.value?.subtitle || latestCompletedSession.value?.subtitle || 'Unfolding'
);

const nextSessionLabel = computed(() => {
  const up = upcomingSession.value;
  if (!up) return 'No upcoming session scheduled';
  return up.time ? `${up.date} at ${up.time}` : up.date;
});

const latestRecap = computed(() => {
  const latest = latestCompletedSession.value;
  if (!latest) return '';
  return latest.homeRecap || latest.description || '';
});

const nextStepsList = computed(() => {
  const steps = latestCompletedSession.value?.nextSteps;
  return Array.isArray(steps) && steps.length ? steps : [];
});

const nextSessionFallback = computed(() => {
  if (upcomingSession.value?.description) {
    return upcomingSession.value.description;
  }
  return latestCompletedSession.value
    ? `The aftermath of ${latestCompletedSession.value.title} continues to unfold.`
    : '';
});

function getSessionNote(entity, sessionNum) {
  if (!Array.isArray(entity.history)) return '';
  const notes = entity.history
    .filter((h) => h && h.session === sessionNum && h.note)
    .map((h) => h.note);
  return notes.join(' • ');
}

const updatedFeedGroups = computed(() => {
  const num = activeSessionNum.value;
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
          badge: badgeLabel(entity, num),
          note: getSessionNote(entity, num),
        })),
      };
    })
    .filter((group) => group.items.length > 0);
});
</script>

<style scoped>
.home-view {
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
}

/* Atmospheric Hero */
.hero-banner {
  position: relative;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--border-color);
  min-height: 320px;
  display: flex;
  align-items: flex-end;
  box-shadow: var(--shadow-md);
}

.hero-image {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center 35%;
  filter: brightness(0.55) saturate(1.05);
}

.hero-overlay {
  position: relative;
  z-index: 1;
  width: 100%;
  padding: 2.5rem 2rem 2rem;
  background: linear-gradient(
    to top,
    rgba(18, 20, 24, 0.96) 0%,
    rgba(18, 20, 24, 0.72) 55%,
    rgba(18, 20, 24, 0.18) 100%
  );
  text-align: center;
}

.hero-eyebrow {
  margin: 0 0 0.4rem;
  font-family: var(--font-accent);
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-size: 0.9rem;
  color: var(--color-highlight);
}

.hero-title {
  margin: 0 0 0.75rem;
  font-size: clamp(2.1rem, 5vw, 3.2rem);
  color: var(--color-primary);
  text-shadow: 0 2px 14px rgba(0, 0, 0, 0.8);
}

.hero-title::after {
  left: 50%;
  transform: translateX(-50%);
  width: 45%;
}

.hero-tagline {
  max-width: 620px;
  margin: 1rem auto 1.25rem;
  color: var(--color-text);
  font-size: 1.05rem;
  opacity: 0.92;
}

.hero-actions {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 0.85rem;
}

.hero-actions .button-link {
  margin-top: 0;
}

.hero-secondary-btn {
  background-color: rgba(18, 20, 24, 0.65);
}

/* Quick Info */
.campaign-quick-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 1.15rem;
}

.info-card {
  background: var(--gradient-primary);
  padding: 1.25rem;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  text-align: center;
}

.info-card h3 {
  margin: 0 0 0.55rem;
  font-size: 1.05rem;
}

.info-card p {
  margin: 0;
  color: var(--color-text);
}

/* Session Bridge */
.session-bridge {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
  gap: 1.15rem;
}

.bridge-card {
  background: var(--gradient-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1.2rem 1.35rem;
}

.bridge-card-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.65rem;
}

.bridge-card h3 {
  margin: 0;
  font-size: 1.1rem;
}

.bridge-link {
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--color-link);
  white-space: nowrap;
}

.bridge-card p {
  margin: 0;
  line-height: 1.68;
}

.next-steps-list {
  margin: 0;
  padding-left: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  line-height: 1.55;
}

/* Party Quick-Cards */
.home-section {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.section-heading-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.5rem;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0.45rem;
}

.section-heading-row h2 {
  margin: 0;
  font-size: 1.55rem;
}

.section-all-link {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--color-link);
}

.party-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.9rem;
}

.party-card {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 0.85rem;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.22);
  border: 1px solid var(--border-color);
  color: var(--color-text);
  transition: transform 0.2s ease, border-color 0.2s ease, background-color 0.2s ease;
}

.party-card:hover {
  transform: translateY(-2px);
  border-color: var(--color-primary);
  background: var(--bg-hover);
  border-bottom-color: var(--color-primary);
}

.party-avatar-wrap {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid var(--color-primary);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-background-soft);
}

.party-avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.party-initials {
  font-family: var(--font-display);
  font-weight: 700;
  color: var(--color-primary);
  font-size: 1.2rem;
}

.party-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.party-name {
  font-family: var(--font-display);
  font-weight: 700;
  color: var(--color-primary);
  font-size: 0.98rem;
  line-height: 1.2;
}

.party-sub {
  font-size: 0.78rem;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.party-level {
  margin-top: 0.2rem;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--color-link-hover);
}

/* Updated in Session N Feed */
.updated-groups {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}

.updated-group-title {
  margin: 0 0 0.55rem;
  font-size: 1.05rem;
  color: var(--color-primary);
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.updated-items {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 0.75rem;
}

.updated-item-card {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding: 0.8rem 0.95rem;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.22);
  border: 1px solid var(--border-color);
  color: var(--color-text);
  transition: border-color 0.2s ease, background-color 0.2s ease;
}

.updated-item-card:hover {
  border-color: var(--color-link);
  background: var(--bg-hover);
  border-bottom-color: var(--color-link);
}

.updated-item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.updated-item-name {
  font-weight: 700;
  color: var(--color-link);
}

.updated-item-card:hover .updated-item-name {
  color: var(--color-link-hover);
}

.updated-item-note {
  margin: 0;
  font-size: 0.85rem;
  line-height: 1.5;
  color: var(--color-text-muted);
}

.badge-new,
.badge-updated {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.1rem 0.42rem;
  border-radius: 3px;
  color: #111;
  flex-shrink: 0;
}

.badge-new {
  background: #ffd54f;
}

.badge-updated {
  background: #90caf9;
}

@media (max-width: 600px) {
  .hero-banner {
    min-height: 270px;
  }

  .hero-overlay {
    padding: 1.75rem 1.25rem 1.5rem;
  }
}
</style>

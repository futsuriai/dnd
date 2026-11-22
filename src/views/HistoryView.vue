<template>
  <div class="content-section">
    <h1>World History &amp; Lore</h1>
    <p class="section-intro">
      The current year is <strong>{{ worldHistory.currentYear }} AE</strong> (After Eulogia).
      The official calendar of The Hariolar Empire and the Eulogia of the Eternal Light.
    </p>

    <div v-if="reversedEras.length" class="timeline">
      <section
        class="era"
        v-for="era in reversedEras"
        :key="era.name"
        :id="slugifyEra(era.name)"
      >
        <div class="era-header">
          <h2>{{ era.name }}</h2>
          <span class="era-year">{{ era.period }}</span>
        </div>

        <div class="era-content">
          <p v-for="(paragraph, pIndex) in era.description" :key="`${era.name}-p-${pIndex}`">
            {{ paragraph }}
          </p>

          <div class="key-events" v-if="era.events && era.events.length">
            <h3>Key Events</h3>
            <ul>
              <li v-for="(event, eIndex) in era.events" :key="`${era.name}-e-${eIndex}`">
                <span class="event-year">{{ event.year }}:</span>
                {{ event.description }}
              </li>
            </ul>
          </div>
        </div>
      </section>
    </div>
    <p v-else class="empty-message">No history recorded yet.</p>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { worldHistory } from '@/store/worldHistory.js';

const reversedEras = computed(() => [...(worldHistory.eras || [])].reverse());

function slugifyEra(name) {
  return String(name || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/['’"]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}
</script>

<style scoped>
.section-intro {
  text-align: center;
  max-width: 800px;
  margin: 0 auto 2em;
}

.timeline {
  position: relative;
  margin: 2rem 0;
  padding-left: 3rem;
}

.timeline::before {
  content: "";
  position: absolute;
  left: 16px;
  top: 0;
  bottom: 0;
  width: 3px;
  background: linear-gradient(
    to bottom,
    var(--color-primary) 0%,
    var(--color-secondary) 50%,
    var(--color-primary) 100%
  );
}

.era {
  position: relative;
  margin-bottom: 3rem;
  border-radius: 6px;
}

.era:last-child {
  margin-bottom: 0;
}

/* Mathematically centered over .timeline::before (16px + 1.5px = 17.5px from .timeline left edge) */
.era::before {
  content: "";
  position: absolute;
  box-sizing: border-box;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--color-surface);
  border: 3px solid var(--color-primary);
  left: calc(-3rem + 17.5px);
  transform: translateX(-50%);
  top: 0.45rem;
}

.era-header {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 0.4rem 1rem;
  margin-bottom: 1rem;
}

.era-header h2 {
  margin: 0;
  font-family: var(--font-display);
}

.era-year {
  color: var(--color-text-muted);
  font-style: italic;
}

.era-content {
  padding-left: 1rem;
  border-left: 1px solid var(--border-color);
}

.key-events {
  margin-top: 1.5rem;
  background: rgba(0, 0, 0, 0.2);
  padding: 1rem;
  border-radius: 6px;
  border: 1px solid rgba(var(--border-color-rgb), 0.5);
}

.key-events h3 {
  margin-top: 0;
  font-family: var(--font-accent);
  color: var(--color-primary);
  font-size: 1.2rem;
}

.key-events ul {
  margin: 0;
  padding-left: 1.5rem;
}

.key-events li {
  margin-bottom: 0.5rem;
}

.key-events li:last-child {
  margin-bottom: 0;
}

.event-year {
  font-weight: bold;
  color: var(--color-primary);
}

.empty-message {
  text-align: center;
  margin-top: 2rem;
  color: var(--text-muted);
}

@media (max-width: 768px) {
  .timeline {
    padding-left: 2.25rem;
  }

  .timeline::before {
    left: 12px;
  }

  .era::before {
    width: 18px;
    height: 18px;
    left: calc(-2.25rem + 13.5px);
  }
}

@media (max-width: 480px) {
  .timeline {
    padding-left: 1.75rem;
  }

  .timeline::before {
    left: 9px;
  }

  .era::before {
    width: 15px;
    height: 15px;
    left: calc(-1.75rem + 10.5px);
    top: 0.5rem;
  }

  .era-header {
    flex-direction: column;
  }
}
</style>

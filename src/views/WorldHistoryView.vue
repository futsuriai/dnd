<template>
  <div class="content-section">
    <h1>World History & Lore</h1>
    <p class="section-intro">The forgotten past and present of the world.</p>

    <div class="timeline">
      <div class="era" v-for="(era, index) in eras" :key="index">
        <div class="era-header">
          <h2>{{ era.name }}</h2>
          <span class="era-year">{{ era.period }}</span>
        </div>
        
        <div class="era-content">
          <p v-for="(paragraph, pIndex) in era.description" :key="pIndex">
            {{ paragraph }}
          </p>
          
          <div class="key-events" v-if="era.events && era.events.length">
            <h3>Key Events</h3>
            <ul>
              <li v-for="(event, eIndex) in era.events" :key="eIndex">
                <span class="event-year">{{ event.year }}:</span> 
                {{ event.description }}
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { worldHistory } from '../store/worldHistory';

export default {
  name: 'WorldHistoryView',
  data() {
    return {
      eras: worldHistory.eras
    }
  }
}
</script>

<style scoped>
.timeline {
  position: relative;
  margin: 3rem 0;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 2rem;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(to bottom, 
    rgba(var(--color-primary-rgb), 0.2), 
    rgba(var(--color-primary-rgb), 0.8),
    rgba(var(--color-primary-rgb), 0.2)
  );
  border-radius: 2px;
  transform: translateX(-50%);
}

.era {
  position: relative;
  margin-bottom: 3rem;
  padding-left: 4rem;
}

.era::before {
  content: '';
  position: absolute;
  left: 2rem;
  top: 1.5rem;
  width: 1.5rem;
  height: 1.5rem;
  background-color: var(--color-background);
  border: 4px solid var(--color-primary);
  border-radius: 50%;
  transform: translateX(-50%);
  z-index: 1;
}

.era-header {
  margin-bottom: 1rem;
}

.era-header h2 {
  margin: 0;
  color: var(--color-primary);
  font-family: var(--font-display);
  font-size: 1.8rem;
}

.era-year {
  display: block;
  font-style: italic;
  color: var(--color-text-muted);
  margin-top: 0.25rem;
}

.era-content {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: var(--shadow-sm);
}

.era-content p {
  margin-bottom: 1rem;
  line-height: 1.6;
}

.key-events {
  margin-top: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: 1rem;
}

.key-events h3 {
  font-size: 1.2rem;
  margin-bottom: 1rem;
  color: var(--color-accent);
}

.key-events ul {
  list-style: none;
  padding: 0;
}

.key-events li {
  margin-bottom: 0.5rem;
  padding-left: 1.5rem;
  position: relative;
}

.key-events li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: var(--color-accent);
}

.event-year {
  font-weight: bold;
  color: var(--color-accent);
}

@media (max-width: 768px) {
  .era {
    padding-left: 3rem;
  }
  
  .timeline::before {
    left: 1.5rem;
  }
  
  .era::before {
    left: 1.5rem;
    width: 1.2rem;
    height: 1.2rem;
  }
}
</style>

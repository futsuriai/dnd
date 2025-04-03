<template>
  <div class="content-section">
    <h1>Campaign Sessions</h1>
    <p class="section-intro">Chronicles of our adventures and key events from each session.</p>

    <div class="sessions-container">
      <div v-for="(session, index) in sessions" :key="index" class="session-card">
        <div class="session-header" :class="{ 'upcoming': session.upcoming }">
          <div class="header-top-line">
            <h3 class="session-title">{{ session.title }}:</h3>
            <span class="session-date">{{ session.date }}</span>
          </div>
          <p class="session-subtitle">{{ session.subtitle }}</p>
        </div>
        
        <div class="session-content">
          <div v-if="session.upcoming" class="upcoming-message">
            <p>{{ session.description }}</p>
          </div>
          <div v-else class="session-summary">
            <p>{{ session.description }}</p>
            
            <div v-if="session.highlights" class="highlights">
              <h4>Key Moments:</h4>
              <ul>
                <li v-for="(highlight, i) in session.highlights" :key="i">
                  {{ highlight }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SessionsView',
  data() {
    return {
      sessions: [
        {
          title: 'Session 0',
          subtitle: 'Character Creation',
          date: 'April 6, 2025',
          upcoming: true,
          description: 'Character creation and world introduction. Come prepared with character concepts and backstory ideas!'
        },
        {
          title: 'Session -1',
          subtitle: 'Setting up the website',
          date: 'April 2, 2025',
          description: 'Playing around with Vue and Github Pages to set this up.',
          highlights: [
            'Set up the page and made it publishable on github'
          ]
        }
      ]
    };
  }
};
</script>

<style scoped>
.section-intro {
  text-align: center;
  max-width: 800px;
  margin: 0 auto 2em;
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

.header-top-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.session-title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.4rem;
  line-height: 1.2;
  display: inline-block;
}

.session-subtitle {
  margin: 0.25rem 0 0;
  font-size: 0.95rem;
  color: var(--text-muted, #aaa);
  font-style: italic;
  width: 100%;
}

.session-date {
  font-family: var(--font-accent);
  font-size: 0.9em;
  font-weight: bold;
  padding: 0.3em 0.6em;
  border-radius: 4px;
  background-color: rgba(100, 100, 100, 0.2);
  white-space: nowrap;
}

.session-content {
  padding: 1.5rem;
}

.upcoming-message {
  font-style: italic;
  border-left: 3px solid var(--color-primary);
  padding-left: 1rem;
}

.upcoming .session-header {
  background-color: rgba(65, 105, 225, 0.1);
}

.highlights {
  margin-top: 1.5rem;
}

.highlights h4 {
  margin-bottom: 0.5rem;
  color: var(--color-primary);
}

.highlights ul {
  padding-left: 1.5rem;
}

.highlights li {
  margin-bottom: 0.5rem;
}

@media (max-width: 600px) {
  .header-top-line {
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  
  .session-date {
    align-self: flex-start;
  }
  
  .session-subtitle {
    margin-top: 0.5rem;
  }
}
</style>

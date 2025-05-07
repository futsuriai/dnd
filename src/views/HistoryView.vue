<template>
    <div class="content-section">
      <h1>World History & Lore</h1>
      <p class="section-intro">The current year is <strong>651 AE</strong> (After Eulogia). The official calendar of The Hariolar Empire and the Eulogia of the Eternal Light.</p>
  
      <div v-if="reversedEras && reversedEras.length" class="timeline">
        <div class="era" v-for="(era, index) in reversedEras" :key="index">
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
      <p v-else class="empty-message">No history recorded yet.</p>
    </div>
  </template>
  
  <script>
  import { worldHistory } from '../store/worldHistory';
  
  export default {
    name: 'HistoryView',
    data() {
      return {
        eras: worldHistory.eras || []
      };
    },
    computed: {
      reversedEras() {
        // Return a reversed copy of the eras array to show newest first
        return [...this.eras].reverse();
      }
    },
    methods: {
      sortedEvents(events) {
        // For events within an era, sort them in reverse chronological order
        // We're making a shallow copy to avoid modifying the original data
        if (!events || !events.length) return [];
        return [...events].sort((a, b) => {
          // Strip out any non-numeric prefix (like "c. ") and convert to number
          const yearA = parseInt(a.year.replace(/[^\d-]/g, ''));
          const yearB = parseInt(b.year.replace(/[^\d-]/g, ''));
          // Reverse sort (newest first)
          return yearB - yearA;
        });
      }
    }
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
    left: 15px;
    top: 0;
    bottom: 0;
    width: 3px;
    background: linear-gradient(to bottom, 
      var(--color-primary) 0%, 
      var(--color-secondary) 50%, 
      var(--color-primary) 100%);
  }
  
  .era {
    position: relative;
    margin-bottom: 3rem;
  }
  
  .era:last-child {
    margin-bottom: 0;
  }
  
  .era::before {
    content: "";
    position: absolute;
    width: 25px;
    height: 25px;
    border-radius: 50%;
    background: var(--color-surface);
    border: 3px solid var(--color-primary);
    left: -4.5rem;
    top: 0.5rem;
  }
  
  .era-header {
    display: flex;
    align-items: baseline;
    margin-bottom: 1rem;
  }
  
  .era-header h2 {
    margin: 0;
    margin-right: 1rem;
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
    border-radius: 4px;
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
  
  @media (max-width: 768px) {
    .timeline {
      padding-left: 2rem;
    }
    
    .era::before {
      left: -4.5rem;
      width: 20px;
      height: 20px;
    }
  }
  
  @media (max-width: 480px) {
    .timeline {
      padding-left: 1.5rem;
    }
    
    .era::before {
      left: -2.2rem;
      width: 16px;
      height: 16px;
    }
    
    .era-header {
      flex-direction: column;
    }
    
    .era-year {
      margin-bottom: 0.5rem;
    }
  }

  .empty-message {
    text-align: center;
    margin-top: 2rem;
    color: var(--text-muted);
  }
  </style>
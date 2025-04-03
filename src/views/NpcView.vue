<template>
  <div class="content-section">
    <h1>Notable NPCs</h1>
    <p class="section-intro">Key figures encountered throughout the realm of the Seven Spires Confederation.</p>
    
    <div class="card-grid">
      <div v-for="npc in npcs" :key="npc.id" class="card npc-card" :id="npc.id">
        <div class="npc-content">
          <h3 class="card-title">{{ npc.name }}</h3>
          
          <div class="npc-details">
            <div class="detail-row">
              <span class="detail-icon">📍</span>
              <span>{{ npc.location }}</span>
            </div>
            
            <div class="detail-row">
              <span class="detail-icon">👑</span>
              <span>{{ npc.role }}</span>
            </div>
            
            <div class="npc-description">
              <p>{{ npc.description }}</p>
            </div>
            
            <div class="npc-status" :class="npc.status.toLowerCase()">
              <span class="status-indicator"></span>
              <span>{{ npc.status }}</span>
            </div>
          </div>
        </div>
        
        <EntityConnections :entityType="'npc'" :entityId="npc.id" />
      </div>
    </div>
  </div>
</template>

<script>
import { npcs } from '../store/worldData';
import EntityConnections from '../components/EntityConnections.vue';

export default {
  name: 'NpcView',
  components: {
    EntityConnections
  },
  data() {
    return {
      npcs
    };
  }
}
</script>

<style scoped>
.section-intro {
  text-align: center;
  max-width: 800px;
  margin: 0 auto 2em;
}

/* Fix for card grid layout */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 2rem;
  align-items: stretch;
}

.npc-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  margin: 0; /* Remove any margin that might cause overflow */
}

.npc-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.npc-details {
  display: flex;
  flex-direction: column;
  height: 100%;
  flex: 1;
}

.detail-row {
  display: flex;
  align-items: center;
  margin-bottom: 0.5rem;
}

.detail-icon {
  margin-right: 0.5rem;
  font-size: 1.2rem;
}

.npc-description {
  margin-top: 1rem;
  flex-grow: 1;
}

.npc-status {
  margin-top: 1rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  font-weight: bold;
  padding: 0.3rem 0.5rem;
  border-radius: 4px;
  align-self: flex-start;
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 0.5rem;
}

.ally .status-indicator {
  background-color: #4caf50;
}

.neutral .status-indicator {
  background-color: #ffeb3b;
}

.enemy .status-indicator {
  background-color: #f44336;
}

.unknown .status-indicator {
  background-color: #9e9e9e;
}

.ally {
  color: #4caf50;
  background-color: rgba(76, 175, 80, 0.1);
}

.neutral {
  color: #ffeb3b;
  background-color: rgba(255, 235, 59, 0.1);
}

.enemy {
  color: #f44336;
  background-color: rgba(244, 67, 54, 0.1);
}

.unknown {
  color: #9e9e9e;
  background-color: rgba(158, 158, 158, 0.1);
}
</style>
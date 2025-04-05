<template>
  <div class="content-section">
    <h1>Magical Items & Artifacts</h1>
    <p class="section-intro">Ancient relics and magical items from the Age of Wonders, recovered from forgotten ruins.</p>

    <!-- Add filter options for viewing historical changes -->
    <div class="view-controls">
      <div class="filter-container">
        <label for="session-filter">Filter by Session:</label>
        <select id="session-filter" v-model="selectedSession" @change="filterBySession">
          <option value="current">Current State</option>
          <option value="all">All Sessions</option>
          <option v-for="session in sessions" :key="session.id" :value="session.id">
            {{ session.title }}
          </option>
        </select>
      </div>
      <div class="toggle-container">
        <label class="toggle-label">
          <input type="checkbox" v-model="showHistoryTimeline">
          Show History Timeline
        </label>
      </div>
    </div>

    <div class="entity-grid">
      <EntityCard 
        v-for="item in filteredItems" 
        :key="item.id" 
        :entity="item" 
        entityType="item"
      />
    </div>
    
    <!-- Historical changes timeline -->
    <div v-if="showHistoryTimeline && itemsWithHistory.length > 0" class="history-timeline">
      <h2>Item History Timeline</h2>
      <p class="section-intro">See how items have changed throughout your campaign.</p>
      
      <div class="timeline">
        <div v-for="(sessionGroup, index) in groupedChanges" :key="index" class="timeline-session">
          <div class="timeline-header">
            <h3>{{ getSessionTitle(sessionGroup.sessionId) }}</h3>
            <span class="timeline-date">{{ getSessionDate(sessionGroup.sessionId) }}</span>
          </div>
          
          <div class="timeline-events">
            <div v-for="(change, changeIndex) in sessionGroup.changes" :key="changeIndex" class="timeline-event">
              <div class="event-icon" :class="change.type">
                <span v-if="change.type === 'added'">+</span>
                <span v-else-if="change.type === 'modified'">↻</span>
                <span v-else-if="change.type === 'removed'">-</span>
              </div>
              
              <div class="event-content">
                <div class="event-title">
                  <span class="event-item-name">{{ change.itemName }}</span>
                  <span class="event-type">{{ getChangeTypeLabel(change.type) }}</span>
                </div>
                
                <div v-if="change.details" class="event-details">
                  <p v-for="(detail, detailIndex) in change.details" :key="detailIndex">
                    {{ detail }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-else-if="showHistoryTimeline && itemsWithHistory.length === 0" class="empty-history">
      <p>No historical changes recorded yet. Changes will appear here as items are discovered or modified during sessions.</p>
    </div>
  </div>
</template>

<script>
import EntityCard from '../components/EntityCard.vue';
import { items, sessions, getSession } from '../store/worldData';

export default {
  name: 'ItemsView',
  components: {
    EntityCard
  },
  data() {
    return {
      items,
      sessions,
      selectedSession: 'current',
      showHistoryTimeline: false,
      // This would come from your session tracking
      currentSessionId: 'session-0'
    };
  },
  computed: {
    filteredItems() {
      if (this.selectedSession === 'current') {
        return this.items;
      } else if (this.selectedSession === 'all') {
        return this.items;
      } else {
        // Return items as they were at the selected session
        // This would require storing historical item states
        return this.items.filter(item => {
          if (!item.history) return false;
          
          // Find the first session where this item appeared
          const firstAppearance = item.history.find(h => 
            h.type === 'added' || h.type === 'modified'
          );
          
          if (!firstAppearance) return false;
          
          // Check if item existed before or during the selected session
          const sessionIndex = this.sessions.findIndex(s => s.id === this.selectedSession);
          const firstAppearanceIndex = this.sessions.findIndex(s => s.id === firstAppearance.sessionId);
          
          return firstAppearanceIndex <= sessionIndex;
        });
      }
    },
    itemsWithHistory() {
      return this.items.filter(item => item.history && item.history.length > 0);
    },
    groupedChanges() {
      // Group all changes by session
      const allChanges = [];
      
      this.itemsWithHistory.forEach(item => {
        item.history.forEach(historyEntry => {
          allChanges.push({
            sessionId: historyEntry.sessionId,
            type: historyEntry.type,
            itemId: item.id,
            itemName: item.name,
            details: historyEntry.details
          });
        });
      });
      
      // Group by session
      const grouped = [];
      const sessionMap = new Map();
      
      allChanges.forEach(change => {
        if (!sessionMap.has(change.sessionId)) {
          const sessionGroup = {
            sessionId: change.sessionId,
            changes: []
          };
          grouped.push(sessionGroup);
          sessionMap.set(change.sessionId, sessionGroup);
        }
        
        sessionMap.get(change.sessionId).changes.push(change);
      });
      
      // Sort by session date (newest first)
      return grouped.sort((a, b) => {
        const sessionA = this.sessions.find(s => s.id === a.sessionId);
        const sessionB = this.sessions.find(s => s.id === b.sessionId);
        
        if (!sessionA || !sessionB) return 0;
        
        // Convert dates to comparable format (assuming date format is consistent)
        return new Date(sessionB.date) - new Date(sessionA.date);
      });
    }
  },
  methods: {
    filterBySession() {
      // Filter method can be expanded later for more complex filtering
    },
    getSessionTitle(sessionId) {
      const session = this.sessions.find(s => s.id === sessionId);
      return session ? session.title : 'Unknown Session';
    },
    getSessionDate(sessionId) {
      const session = this.sessions.find(s => s.id === sessionId);
      return session ? session.date : '';
    },
    getChangeTypeLabel(type) {
      switch (type) {
        case 'added': return 'Discovered';
        case 'modified': return 'Updated';
        case 'removed': return 'Removed';
        default: return type;
      }
    }
  }
};
</script>

<style scoped>
/* View controls and filters */
.view-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.filter-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.toggle-container {
  display: flex;
  align-items: center;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

select {
  background-color: var(--color-surface);
  color: var(--color-text);
  border: 1px solid var(--border-color);
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  font-family: var(--font-main);
}

/* Timeline styles */
.history-timeline {
  margin-top: 3rem;
  border-top: 1px solid var(--border-color);
  padding-top: 2rem;
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

.timeline-session {
  position: relative;
  margin-bottom: 3rem;
}

.timeline-session:last-child {
  margin-bottom: 0;
}

.timeline-session::before {
  content: "";
  position: absolute;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--color-surface);
  border: 3px solid var(--color-primary);
  left: -4.2rem;
  top: 0.5rem;
}

.timeline-header {
  display: flex;
  align-items: baseline;
<template>
  <div :class="['entity-card', entityType + '-card']" :id="entity.id">
    <div class="entity-content">
      <!-- Header Section -->
      <div class="entity-header" :class="getSpecialClasses">
        <!-- Avatar/Icon Section (for characters or with custom icon) -->
        <div v-if="showAvatar" class="avatar-container">
          <div class="avatar-placeholder">
            <span>{{ getInitials(entity.name) }}</span>
          </div>
        </div>
        
        <div class="entity-title-container">
          <h3 class="entity-title">{{ entity.name }}</h3>
          
          <!-- Subtitle section -->
          <div v-if="getSubtitle" class="entity-subtitle">
            {{ getSubtitle }}
          </div>
          
          <!-- Status badge (for NPCs) -->
          <div v-if="entityType === 'npc' && entity.status" 
               class="entity-status" 
               :class="entity.status.toLowerCase()">
            <span class="status-indicator"></span>
            <span>{{ entity.status }}</span>
          </div>
        </div>
        
        <!-- Rarity badge (for items) -->
        <span v-if="entityType === 'item' && entity.rarity" class="entity-rarity">
          {{ entity.rarity }}
        </span>
      </div>
      
      <!-- Metadata Section -->
      <div v-if="hasMetadata" class="entity-meta">
        <!-- Location entities -->
        <template v-if="entityType === 'location'">
          <span class="meta-icon" v-html="getEntityIcon()"></span>
          <span class="meta-value" v-if="entity.region">{{ entity.region }}</span>
        </template>
        
        <!-- Character entities -->
        <template v-else-if="entityType === 'character'">
          <div class="detail-row">
            <span class="detail-label">Player:</span>
            <span class="detail-value">{{ entity.player }}</span>
          </div>
          
          <div class="detail-row">
            <span class="detail-label">Level:</span>
            <span class="detail-value">{{ entity.level }}</span>
          </div>
          
          <div class="detail-row">
            <span class="detail-label">Background:</span>
            <span class="detail-value">{{ entity.background }}</span>
          </div>
          
          <!-- Optional quote section for characters -->
          <div v-if="entity.quote" class="character-quote">
            <blockquote>{{ entity.quote }}</blockquote>
          </div>
        </template>
        
        <!-- NPC entities -->
        <template v-else-if="entityType === 'npc'">
          <div class="detail-row">
            <span class="detail-icon">📍</span>
            <span>{{ entity.location }}</span>
          </div>
          
          <div class="detail-row">
            <span class="detail-icon">👑</span>
            <span>{{ entity.role }}</span>
          </div>
          
          <!-- Optional quote section for NPCs -->
          <div v-if="entity.quote" class="npc-quote">
            <blockquote>{{ entity.quote }}</blockquote>
          </div>
        </template>
        
        <!-- Item entities -->
        <template v-else-if="entityType === 'item'">
          <div class="property">
            <span class="property-label">Type:</span>
            <span>{{ entity.type }}</span>
          </div>
          
          <div class="property">
            <span class="property-label">Attunement:</span>
            <span>{{ entity.attunement }}</span>
          </div>
          
          <div v-if="entity.found" class="property">
            <span class="property-label">Found:</span>
            <span>{{ entity.found }}</span>
          </div>
          
          <div v-if="entity.owner" class="property">
            <span class="property-label">Current Owner:</span>
            <span>{{ entity.owner }}</span>
          </div>
        </template>
      </div>
      
      <!-- Description Section -->
      <div class="entity-description">
        <p>{{ entity.description || entity.bio }}</p>
      </div>
      
      <!-- Character-specific traits -->
      <div v-if="entityType === 'character' && entity.specialAbility" class="character-traits">
        <div class="ability">
          <span class="ability-label">Special Ability:</span>
          <span>{{ entity.specialAbility }}</span>
        </div>
      </div>
      
      <!-- NPC-specific traits -->
      <div v-if="entityType === 'npc' && entity.inventory" class="npc-traits">
        <div class="inventory">
          <span class="inventory-label">Inventory:</span>
          <span>{{ entity.inventory }}</span>
        </div>
      </div>
      
      <!-- Character inventory if available -->
      <div v-if="entityType === 'character' && entity.inventory" class="character-inventory">
        <div class="inventory">
          <span class="inventory-label">Inventory:</span>
          <span>{{ entity.inventory }}</span>
        </div>
      </div>
      
      <!-- Action Buttons Section -->
      <div v-if="hasActions" class="entity-actions">
        <a v-if="entityType === 'character' && entity.dndBeyondLink" 
           :href="entity.dndBeyondLink" 
           target="_blank" 
           rel="noopener noreferrer" 
           class="button-link">
          View on D&D Beyond
        </a>
      </div>
    </div>
    
    <!-- EntityConnections Component -->
    <EntityConnections :entityType="entityType" :entityId="entity.id" v-if="entity.id" />
    
    <!-- Entity History Section -->
    <div class="entity-history" v-if="entity.history && entity.history.length">
      <div class="history-header" @click="toggleHistory">
        <h4>History</h4>
        <span class="toggle-icon">{{ showHistory ? '▼' : '▶' }}</span>
      </div>
      
      <div v-if="showHistory" class="history-content">
        <div v-for="(sessionHistory, index) in entity.history" 
             :key="'history-' + index"
             class="history-session-group">
          
          <div class="history-session-header">
            <span class="session-indicator"></span>
            <span class="session-name">{{ getSessionName(sessionHistory.sessionId) }}</span>
          </div>
          
          <ul class="history-events">
            <li v-for="(event, eventIndex) in sessionHistory.events" 
                :key="'event-' + eventIndex"
                :class="['history-event', event.type]">
              {{ event.description }}
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import EntityConnections from './EntityConnections.vue';
import { getSession } from '../store/worldData';

export default {
  name: 'EntityCard',
  components: {
    EntityConnections
  },
  props: {
    entity: {
      type: Object,
      required: true
    },
    entityType: {
      type: String,
      required: true,
      validator: value => ['character', 'npc', 'location', 'item'].includes(value)
    },
    showAvatar: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      showHistory: false
    };
  },
  computed: {
    hasMetadata() {
      if (this.entityType === 'location' && this.entity.region) return true;
      if (this.entityType === 'character') return true;
      if (this.entityType === 'npc') return true;
      if (this.entityType === 'item') return true;
      return false;
    },
    hasActions() {
      if (this.entityType === 'character' && this.entity.dndBeyondLink) return true;
      return false;
    },
    getSubtitle() {
      if (this.entityType === 'character') {
        return `${this.entity.race} ${this.entity.class}`;
      }
      return null;
    },
    getSpecialClasses() {
      const classes = {};
      
      // Add item rarity class
      if (this.entityType === 'item' && this.entity.rarity) {
        classes[this.entity.rarity.toLowerCase().replace(' ', '-')] = true;
      }
      
      return classes;
    }
  },
  methods: {
    getInitials(name) {
      return name.split(' ').map(word => word[0]).join('');
    },
    getEntityIcon() {
      if (this.entityType === 'location') {
        const cityIcons = {
          capital: '🏛️',
          port: '⚓',
          trading: '🛒',
          magic: '✨',
          default: '🏙️'
        };
        
        const dungeonIcons = {
          ruin: '🏚️',
          cave: '🕳️',
          temple: '🏯',
          fortress: '🏰',
          default: '💀'
        };
        
        const poiIcons = {
          natural: '🌳',
          magic: '✨',
          shrine: '🔮',
          monument: '🗿',
          tavern: '🍺',
          default: '⭐'
        };
        
        if (this.entity.type === 'city') {
          return cityIcons[this.entity.subtype] || cityIcons.default;
        } else if (this.entity.type === 'dungeon') {
          return dungeonIcons[this.entity.subtype] || dungeonIcons.default;
        } else {
          return poiIcons[this.entity.subtype] || poiIcons.default;
        }
      }
      
      return '';
    },
    toggleHistory() {
      this.showHistory = !this.showHistory;
    },
    getSessionName(sessionId) {
      // Session -1 is special, treat as website setup
      if (sessionId === 'session-minus-1') {
        return 'Initial Setup';
      }
      
      const session = getSession(sessionId);
      if (session) {
        return `${session.title}: ${session.subtitle}`;
      }
      return sessionId;
    }
  }
}
</script>

<style scoped>
/* Base card styling */
.entity-card {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  padding: 1.25rem;
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}

.entity-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}

.entity-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  padding: 1.25rem;
}

/* Header section */
.entity-header {
  display: flex;
  align-items: center;
  margin-bottom: 1rem;
}

.entity-title-container {
  flex-grow: 1;
}

.entity-title {
  margin: 0;
  font-family: var(--font-display);
  color: var(--color-primary);
  font-size: 1.3rem;
  line-height: 1.2;
}

.entity-subtitle {
  color: var(--color-text-muted);
  margin: 0.2rem 0 0;
  font-size: 0.9rem;
  font-style: italic;
}

/* Avatar styling */
.avatar-container {
  margin-right: 1rem;
}

.avatar-placeholder {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: var(--color-primary);
  color: var(--color-background);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: bold;
  font-family: var(--font-display);
  border: 2px solid var(--color-text);
}

/* Metadata section */
.entity-meta {
  margin-bottom: 1rem;
}

.meta-icon {
  margin-right: 0.5rem;
  font-size: 1.1rem;
}

.meta-value {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  font-style: italic;
}

/* Detail rows for character and NPC */
.detail-row {
  display: flex;
  margin-bottom: 0.5rem;
}

.detail-label {
  font-weight: bold;
  color: var(--color-primary);
  width: 100px;
}

.detail-value {
  flex-grow: 1;
}

.detail-icon {
  margin-right: 0.5rem;
  font-size: 1.2rem;
}

/* Description section */
.entity-description {
  flex-grow: 1;
  margin-bottom: 1rem;
}

.entity-description p {
  margin: 0;
  line-height: 1.6;
}

/* Quote styling */
.character-quote blockquote,
.npc-quote blockquote {
  font-style: italic;
  border-left: 3px solid var(--color-primary);
  padding-left: 10px;
  margin: 12px 0;
  font-size: 0.95rem;
}

/* Character traits */
.character-traits, 
.npc-traits,
.character-inventory {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dotted var(--border-color);
}

.ability-label, 
.inventory-label {
  font-weight: bold;
  color: var(--color-primary);
  margin-right: 0.5rem;
}

/* Actions section */
.entity-actions {
  margin-top: 1rem;
  display: flex;
  justify-content: center;
}

/* NPC status styles */
.entity-status {
  margin-top: 0.5rem;
  display: inline-flex;
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

/* Item properties */
.property {
  margin-bottom: 0.8rem;
}

.property-label {
  font-weight: bold;
  color: var(--color-primary);
  margin-right: 0.5rem;
}

/* Item rarity */
.entity-rarity {
  font-family: var(--font-accent);
  font-size: 0.9em;
  font-weight: bold;
  padding: 0.3em 0.6em;
  border-radius: 4px;
  text-transform: uppercase;
}

/* Item rarity backgrounds */
.common {
  background-color: rgba(169, 169, 169, 0.1);
}
.common .entity-rarity {
  color: #a9a9a9;
  background-color: rgba(169, 169, 169, 0.2);
}

.uncommon {
  background-color: rgba(75, 175, 80, 0.1);
}
.uncommon .entity-rarity {
  color: #4baf50;
  background-color: rgba(75, 175, 80, 0.2);
}

.rare {
  background-color: rgba(33, 150, 243, 0.1);
}
.rare .entity-rarity {
  color: #2196f3;
  background-color: rgba(33, 150, 243, 0.2);
}

.very-rare {
  background-color: rgba(156, 39, 176, 0.1);
}
.very-rare .entity-rarity {
  color: #9c27b0;
  background-color: rgba(156, 39, 176, 0.2);
}

.legendary {
  background-color: rgba(255, 152, 0, 0.1);
}
.legendary .entity-rarity {
  color: #ff9800;
  background-color: rgba(255, 152, 0, 0.2);
}

.artifact {
  background-color: rgba(244, 67, 54, 0.1);
}
.artifact .entity-rarity {
  color: #f44336;
  background-color: rgba(244, 67, 54, 0.2);
}

/* Specific entity type customizations */
.location-card {
  background: rgba(0, 0, 0, 0.2);
}

/* Entity History Section */
.entity-history {
  border-top: 1px solid var(--border-color);
  margin-top: 1.5rem;
  padding-top: 1rem;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  margin-bottom: 0.5rem;
}

.history-header h4 {
  margin: 0;
  font-size: 1rem;
  color: var(--color-primary);
}

.toggle-icon {
  color: var(--color-text-muted);
  font-size: 0.8rem;
  transition: transform 0.3s ease;
}

.history-content {
  padding-top: 0.5rem;
}

.history-session-group {
  margin-bottom: 1rem;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  padding: 0.8rem;
}

.history-session-header {
  display: flex;
  align-items: center;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  font-weight: bold;
}

.session-indicator {
  display: inline-block;
  width: 8px;
  height: 8px;
  background-color: var(--color-primary);
  border-radius: 50%;
  margin-right: 0.5rem;
}

.history-events {
  list-style: none;
  padding-left: 1rem;
  margin: 0.5rem 0 0;
}

.history-event {
  position: relative;
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
  padding-left: 1.2rem;
}

.history-event:before {
  content: "";
  position: absolute;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #666;
  left: 0;
  top: 7px;
}

.history-event.create:before {
  background-color: #4caf50; /* green */
}

.history-event.update:before {
  background-color: #2196f3; /* blue */
}

.history-event.connect:before {
  background-color: #ff9800; /* orange */
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .entity-meta {
    flex-direction: column;
  }
}
</style>

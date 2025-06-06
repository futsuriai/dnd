<template>
  <div :class="['entity-card', entityType + '-card']" :id="entity.id">
    <div class="entity-content">
      <!-- Header Section -->
      <div class="entity-header" :class="getSpecialClasses">
        <!-- Avatar/Icon Section (for characters or with custom icon) -->
        <div v-if="showAvatar" class="avatar-container" @click="handleAvatarClick" :style="{ cursor: entity.portraitUrl ? 'pointer' : 'default' }">
          <div class="avatar-placeholder">
            <!-- Conditionally render image or initials -->
            <img v-if="entity.avatarUrl" :src="entity.avatarUrl" :alt="entity.name + ' avatar'" class="avatar-image"/>
            <span v-else>{{ getInitials(entity.name) }}</span>
          </div>
        </div>
        
        <div class="entity-title-container">
          <!-- Make character names clickable -->
          <h3 class="entity-title">
            <router-link v-if="entityType === 'character'" :to="'/characters/' + entity.id">
              {{ entity.name }}
            </router-link>
            <span v-else>{{ entityType === 'lore' ? entity.term : entity.name }}</span>
          </h3>
          
          <!-- Subtitle section - Use v-html for line break -->
          <div v-if="getSubtitle" class="entity-subtitle" v-html="getSubtitle"></div>
          
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
            <span class="detail-label">Level:</span>
            <span class="detail-value">{{ entity.level }}</span>
          </div>
          
          <div class="detail-row">
            <span class="detail-label">Background:</span>
            <span class="detail-value">{{ entity.background }}</span>
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
        <!-- Use v-html for potential markdown/links in bio, ensure safety if needed -->
        <p v-html="entity.description || entity.bio"></p> 
        <!-- Add Read More hint -->
        <a v-if="entity.fullText" @click.prevent="showFullText" href="#" class="read-more-link">
          Read More...
        </a>
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
    <EntityConnections 
      :entityType="entityType" 
      :entityId="entity.id" 
      :filter-out-connection-id="filterOutConnectionId"
      v-if="entity.id" 
    />
  </div>
</template>

<script>
import EntityConnections from './EntityConnections.vue';

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
      validator: value => ['character', 'npc', 'location', 'item', 'lore'].includes(value) // Add 'lore'
    },
    showAvatar: {
      type: Boolean,
      default: false
    },
    avatarUrl: { // Add avatarUrl prop
      type: String,
      default: null
    },
    portraitUrl: { // Add portraitUrl prop
      type: String,
      default: null
    },
    filterOutConnectionId: { // Add the new prop
      type: String,
      default: null
    }
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
        // Create a more styled display with distinct lines for race and class
        return `<div class="char-race">${this.entity.race}</div>
                <div class="char-class">${this.entity.class}</div>`;
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
    showFullText() {
      // Emit an object containing both title and text
      this.$emit('show-full-text', { 
        title: this.entityType === 'lore' ? this.entity.term : this.entity.name, // Use term for lore title
        text: this.entity.fullText 
      });
    },
    handleAvatarClick() {
      if (this.entity.portraitUrl) {
        this.$emit('show-portrait', { 
          title: this.entity.name,
          imageUrl: this.entity.portraitUrl 
        });
      }
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

.entity-title a {
  color: var(--accent-color, #d4af37);
  text-decoration: none;
  transition: color 0.2s ease;
}

.entity-title a:hover {
  color: var(--color-primary, #375a7f);
  text-decoration: underline;
}

.entity-subtitle {
  color: var(--color-text-muted);
  margin: 0.3rem 0 0.5rem;
  font-size: 0.9rem;
  font-style: italic;
  line-height: 1.6; /* Increased line height for better spacing */
}

/* Avatar styling */
.avatar-container {
  margin-right: 1rem;
  flex-shrink: 0; /* Prevent shrinking */
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
  overflow: hidden; /* Hide parts of image that overflow */
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover; /* Cover the area, cropping if needed */
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
  margin-bottom: 0.7rem;
  flex-wrap: wrap; /* Allow wrapping for long backgrounds */
}

.detail-label {
  font-weight: bold;
  color: var(--color-primary);
  min-width: 100px;
  margin-right: 0.5rem;
}

.detail-value {
  flex: 1;
  word-wrap: break-word; /* Handle long text */
  max-width: 100%; /* Prevent overflow */
  padding: 0 0.25rem; /* Add some padding */
}

.detail-icon {
  margin-right: 0.5rem;
  font-size: 1.2rem;
}

/* Character race and class styling */
.char-race, .char-class {
  margin: 0.15rem 0;
  line-height: 1.3;
}

.char-race {
  color: var(--color-text-muted);
}

.char-class {
  color: var(--color-text-muted);
  font-weight: 500;
}

/* Description section */
.entity-description {
  flex-grow: 1;
  margin-bottom: 1rem;
}

.entity-description p {
  margin: 0 0 0.5rem 0; /* Add bottom margin */
  line-height: 1.6;
  /* Consider adding max-height and overflow for very long text */
  /* max-height: 100px; */
  /* overflow: hidden; */
  /* text-overflow: ellipsis; */
  /* display: -webkit-box; */
  /* -webkit-line-clamp: 4; */ /* Limit to 4 lines */
  /* -webkit-box-orient: vertical; */
}

/* Read More link styling */
.read-more-link {
  display: inline-block;
  margin-top: 0.5rem;
  color: var(--color-accent);
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: bold;
}

.read-more-link:hover {
  text-decoration: underline;
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

/* Responsive adjustments */
@media (max-width: 768px) {
  .entity-meta {
    flex-direction: column;
  }
}
</style>

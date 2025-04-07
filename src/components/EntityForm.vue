<template>
  <div class="entity-form">
    <form @submit.prevent="saveEntity">
      <!-- Common fields for all entity types -->
      <div class="form-group">
        <label for="id">Entity ID</label>
        <input 
          type="text" 
          id="id" 
          v-model="formData.id" 
          :disabled="readOnly || !isNewEntity"
          placeholder="Leave empty for auto-generated ID"
        />
      </div>
      
      <div class="form-group">
        <label for="name">Name*</label>
        <input 
          type="text" 
          id="name" 
          v-model="formData.name" 
          required 
          :disabled="readOnly"
        />
      </div>
      
      <div class="form-group">
        <label for="description">Description</label>
        <textarea 
          id="description" 
          v-model="formData.description" 
          rows="4"
          :disabled="readOnly"
        ></textarea>
      </div>
      
      <!-- Session selector for history tracking (shown for all entity types) -->
      <div class="form-group" v-if="!readOnly">
        <label for="sessionId">Associate with Session</label>
        <select 
          id="sessionId" 
          v-model="formData.sessionId"
          class="session-selector"
        >
          <option value="session-admin">Admin (No specific session)</option>
          <option v-for="session in sessions" :key="session.id" :value="session.id">
            {{ session.title }} ({{ formatDate(session.date) }})
          </option>
        </select>
        <div class="helper-text">Select which game session this change is associated with for history tracking</div>
      </div>
      
      <!-- Character specific fields -->
      <template v-if="entityType === 'character'">
        <div class="form-group">
          <label for="player">Player Name</label>
          <input 
            type="text" 
            id="player" 
            v-model="formData.player" 
            :disabled="readOnly"
          />
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label for="race">Race</label>
            <input 
              type="text" 
              id="race" 
              v-model="formData.race" 
              :disabled="readOnly"
            />
          </div>
          
          <div class="form-group">
            <label for="class">Class</label>
            <input 
              type="text" 
              id="class" 
              v-model="formData.class" 
              :disabled="readOnly"
            />
          </div>
          
          <div class="form-group">
            <label for="level">Level</label>
            <input 
              type="number" 
              id="level" 
              v-model.number="formData.level" 
              :disabled="readOnly"
              min="1"
            />
          </div>
        </div>
        
        <div class="form-group">
          <label for="background">Background</label>
          <input 
            type="text" 
            id="background" 
            v-model="formData.background" 
            :disabled="readOnly"
          />
        </div>
        
        <div class="form-group">
          <label for="bio">Biography/Backstory</label>
          <textarea 
            id="bio" 
            v-model="formData.bio" 
            rows="6"
            :disabled="readOnly"
          ></textarea>
        </div>
        
        <div class="form-group">
          <label for="quote">Character Quote</label>
          <input 
            type="text" 
            id="quote" 
            v-model="formData.quote" 
            :disabled="readOnly"
          />
        </div>
      </template>
      
      <!-- NPC specific fields -->
      <template v-if="entityType === 'npc'">
        <div class="form-group">
          <label for="role">Role</label>
          <input 
            type="text" 
            id="role" 
            v-model="formData.role" 
            :disabled="readOnly"
          />
        </div>
        
        <div class="form-group">
          <label for="location">Location</label>
          <input 
            type="text" 
            id="location" 
            v-model="formData.location" 
            :disabled="readOnly"
          />
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label for="status">Status</label>
            <select 
              id="status" 
              v-model="formData.status"
              :disabled="readOnly"
            >
              <option value="Ally">Ally</option>
              <option value="Neutral">Neutral</option>
              <option value="Enemy">Enemy</option>
              <option value="Unknown">Unknown</option>
            </select>
          </div>
        </div>
        
        <div class="form-group">
          <label for="quote">NPC Quote</label>
          <input 
            type="text" 
            id="quote" 
            v-model="formData.quote" 
            :disabled="readOnly"
          />
        </div>
      </template>
      
      <!-- Location specific fields -->
      <template v-if="entityType === 'location'">
        <div class="form-row">
          <div class="form-group">
            <label for="type">Type</label>
            <input 
              type="text" 
              id="type" 
              v-model="formData.type" 
              placeholder="City, Dungeon, Landmark, etc."
              :disabled="readOnly"
            />
          </div>
          
          <div class="form-group">
            <label for="subtype">Subtype</label>
            <input 
              type="text" 
              id="subtype" 
              v-model="formData.subtype" 
              placeholder="Magical, Settlement, Ruin, etc."
              :disabled="readOnly"
            />
          </div>
        </div>
        
        <div class="form-group">
          <label for="region">Region</label>
          <input 
            type="text" 
            id="region" 
            v-model="formData.region" 
            :disabled="readOnly"
          />
        </div>
        
        <div class="form-group">
          <label for="status">Status</label>
          <input 
            type="text" 
            id="status" 
            v-model="formData.status" 
            placeholder="Accessible, Ruins, Active Node, etc."
            :disabled="readOnly"
          />
        </div>
      </template>
      
      <!-- Item specific fields -->
      <template v-if="entityType === 'item'">
        <div class="form-row">
          <div class="form-group">
            <label for="type">Type</label>
            <input 
              type="text" 
              id="type" 
              v-model="formData.type" 
              placeholder="Weapon, Armor, Magical item, etc."
              :disabled="readOnly"
            />
          </div>
          
          <div class="form-group">
            <label for="rarity">Rarity</label>
            <select 
              id="rarity" 
              v-model="formData.rarity"
              :disabled="readOnly"
            >
              <option value="Common">Common</option>
              <option value="Uncommon">Uncommon</option>
              <option value="Rare">Rare</option>
              <option value="Very Rare">Very Rare</option>
              <option value="Legendary">Legendary</option>
              <option value="Artifact">Artifact</option>
            </select>
          </div>
        </div>
        
        <div class="form-group">
          <label for="attunement">Attunement</label>
          <input 
            type="text" 
            id="attunement" 
            v-model="formData.attunement" 
            placeholder="Required (Class), Not Required, etc."
            :disabled="readOnly"
          />
        </div>
        
        <div class="form-group">
          <label for="found">Where Found</label>
          <input 
            type="text" 
            id="found" 
            v-model="formData.found" 
            :disabled="readOnly"
          />
        </div>
        
        <div class="form-group">
          <label for="owner">Current Owner</label>
          <input 
            type="text" 
            id="owner" 
            v-model="formData.owner" 
            :disabled="readOnly"
          />
        </div>
      </template>
      
      <!-- Session specific fields -->
      <template v-if="entityType === 'session'">
        <div class="form-group">
          <label for="title">Session Title*</label>
          <input 
            type="text" 
            id="title" 
            v-model="formData.title" 
            required
            :disabled="readOnly"
          />
        </div>
        
        <div class="form-group">
          <label for="subtitle">Subtitle</label>
          <input 
            type="text" 
            id="subtitle" 
            v-model="formData.subtitle"
            :disabled="readOnly"
          />
        </div>
        
        <div class="form-group">
          <label for="date">Date</label>
          <input 
            type="date" 
            id="date" 
            v-model="formData.date"
            :disabled="readOnly"
          />
        </div>
        
        <div class="form-group">
          <label for="upcoming">Upcoming Session</label>
          <input 
            type="checkbox" 
            id="upcoming" 
            v-model="formData.upcoming"
            :disabled="readOnly"
          />
        </div>
        
        <div class="form-group">
          <label for="summary">Summary</label>
          <textarea 
            id="summary" 
            v-model="formData.summary" 
            rows="6"
            :disabled="readOnly"
          ></textarea>
        </div>
        
        <div class="form-group">
          <label for="highlights">Highlights</label>
          <div v-if="!readOnly" class="repeatable-fields">
            <div v-for="(highlight, index) in formData.highlights" :key="index" class="repeatable-field">
              <input 
                type="text" 
                v-model="formData.highlights[index]"
                placeholder="Session highlight"
              />
              <button type="button" @click="removeHighlight(index)" class="remove-button">×</button>
            </div>
            <button type="button" @click="addHighlight" class="add-button">Add Highlight</button>
          </div>
          <div v-else>
            <div v-for="(highlight, index) in formData.highlights" :key="index" class="highlight-item">
              {{ highlight }}
            </div>
          </div>
        </div>
      </template>
      
      <div class="form-actions" v-if="!readOnly">
        <button type="button" class="btn btn-cancel" @click="$emit('cancel')">Cancel</button>
        <button type="submit" class="btn btn-primary">Save</button>
      </div>
    </form>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue';
import worldData from '../store/worldData';

export default {
  name: 'EntityForm',
  props: {
    entityType: {
      type: String,
      required: true,
      validator: value => ['character', 'npc', 'location', 'item', 'session'].includes(value)
    },
    entity: {
      type: Object,
      default: () => ({})
    },
    readOnly: {
      type: Boolean,
      default: false
    }
  },
  setup(props, { emit }) {
    const formData = ref({});
    const isNewEntity = computed(() => !props.entity.id);
    const sessions = ref([]);
    
    // Load sessions for the dropdown
    onMounted(async () => {
      try {
        // Initialize worldData to determine data source
        await worldData.initWorldData();
        // Get all sessions
        sessions.value = await worldData.getAllSessions();
      } catch (error) {
        console.error('Error loading sessions for form:', error);
      }
    });
    
    // Format date for display
    const formatDate = (dateString) => {
      if (!dateString) return '';
      return new Date(dateString).toLocaleDateString();
    };
    
    // Initialize form data from entity prop
    const initFormData = () => {
      // Deep clone the entity to avoid modifying the original
      formData.value = JSON.parse(JSON.stringify(props.entity || {}));
      
      // Set default values for new entities
      if (Object.keys(formData.value).length === 0) {
        setDefaultValues();
      }
      
      // Ensure highlights is an array for sessions
      if (props.entityType === 'session' && !Array.isArray(formData.value.highlights)) {
        formData.value.highlights = formData.value.highlights 
          ? formData.value.highlights.split('\n').filter(h => h.trim())
          : [];
      }
      
      // Set default session ID if not provided (try to use most recent non-upcoming session)
      if (!formData.value.sessionId) {
        const recentSession = sessions.value.find(s => !s.upcoming);
        formData.value.sessionId = recentSession ? recentSession.id : 'session-admin';
      }
    };
    
    // Set default values based on entity type
    const setDefaultValues = () => {
      const defaults = {
        // Common defaults
        id: '',
        name: '',
        description: '',
        
        // Entity-specific defaults
        character: {
          player: '',
          race: '',
          class: '',
          level: 1,
          background: '',
          bio: '',
          quote: ''
        },
        npc: {
          role: '',
          location: '',
          status: 'Neutral',
          quote: ''
        },
        location: {
          type: '',
          subtype: '',
          region: '',
          status: ''
        },
        item: {
          type: '',
          rarity: 'Common',
          attunement: 'Not required',
          found: '',
          owner: ''
        },
        session: {
          title: '',
          subtitle: '',
          date: new Date().toISOString().split('T')[0],
          upcoming: false,
          summary: '',
          highlights: []
        }
      };
      
      // Apply common defaults
      formData.value = {
        ...formData.value,
        id: '',
        name: '',
        description: '',
        sessionId: 'session-admin' // Default to admin session
      };
      
      // Apply entity-specific defaults
      if (defaults[props.entityType]) {
        formData.value = {
          ...formData.value,
          ...defaults[props.entityType]
        };
      }
    };
    
    // Initialize form data on component creation
    initFormData();
    
    // Watch for changes to the entity prop
    watch(() => props.entity, () => {
      initFormData();
    }, { deep: true });
    
    // Methods for session highlights
    const addHighlight = () => {
      if (!formData.value.highlights) {
        formData.value.highlights = [];
      }
      formData.value.highlights.push('');
    };
    
    const removeHighlight = (index) => {
      formData.value.highlights.splice(index, 1);
    };
    
    // Handle form submission
    const saveEntity = () => {
      // Clone the data to avoid reactive issues
      const dataToSave = JSON.parse(JSON.stringify(formData.value));
      
      // Clean up any empty fields
      Object.keys(dataToSave).forEach(key => {
        if (dataToSave[key] === '' || dataToSave[key] === null) {
          delete dataToSave[key];
        }
      });
      
      // For sessions, handle specific conversions
      if (props.entityType === 'session') {
        // Filter out empty highlights
        if (Array.isArray(dataToSave.highlights)) {
          dataToSave.highlights = dataToSave.highlights.filter(h => h.trim());
        }
        
        // If no ID provided for session, create ID from title
        if (!dataToSave.id && dataToSave.title) {
          const sessionNum = extractSessionNumber(dataToSave.title);
          if (sessionNum !== null) {
            dataToSave.id = `session-${sessionNum}`;
          }
        }
      }
      
      emit('save', dataToSave);
    };
    
    // Extract session number from title, e.g., "Session 1" -> 1
    const extractSessionNumber = (title) => {
      const match = title.match(/session\s+(-?\d+)/i);
      if (match && match[1]) {
        return match[1];
      }
      return null;
    };
    
    return {
      formData,
      isNewEntity,
      sessions,
      formatDate,
      addHighlight,
      removeHighlight,
      saveEntity
    };
  }
};
</script>

<style scoped>
.entity-form {
  padding: 1rem 0;
}

.form-group {
  margin-bottom: 1rem;
  width: 100%;
}

.form-row {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.form-row .form-group {
  flex: 1;
  margin-bottom: 0;
}

label {
  display: block;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

input, textarea, select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid var(--border-color, #555);
  background-color: rgba(0, 0, 0, 0.2);
  color: var(--color-text, #ddd);
  border-radius: 4px;
  font-family: inherit;
}

input[type="checkbox"] {
  width: auto;
  margin-right: 0.5rem;
}

input:focus, textarea:focus, select:focus {
  outline: none;
  border-color: var(--color-primary, #4CAF50);
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 2rem;
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  border: none;
}

.btn-primary {
  background-color: var(--color-primary, #4CAF50);
  color: var(--color-background, #fff);
}

.btn-cancel {
  background-color: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--border-color, #555);
  color: var(--color-text, #ddd);
}

/* Repeatable fields for highlights */
.repeatable-fields {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.repeatable-field {
  display: flex;
  gap: 0.5rem;
}

.remove-button {
  width: 30px;
  height: 30px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1.2rem;
}

.add-button {
  margin-top: 0.5rem;
  padding: 0.3rem 0.8rem;
  background-color: #2196F3;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  align-self: flex-start;
}

.highlight-item {
  padding: 0.5rem;
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  margin-bottom: 0.5rem;
}

@media (max-width: 768px) {
  .form-row {
    flex-direction: column;
    gap: 1rem;
  }
  
  .form-row .form-group {
    margin-bottom: 0;
  }
}

/* Session selector styling */
.session-selector {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid var(--border-color, #555);
  background-color: rgba(0, 0, 0, 0.2);
  color: var(--color-text, #ddd);
  border-radius: 4px;
  font-family: inherit;
}

.helper-text {
  font-size: 0.8rem;
  color: var(--color-text-muted, #999);
  margin-top: 0.3rem;
}
</style>
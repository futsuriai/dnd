<template>
  <div class="entity-form">
    <form @submit.prevent="saveEntity">
      <!-- Common fields for all entity types -->
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
      
      <!-- Character specific fields -->
      <template v-if="entityType === 'character'">
        <div class="form-group">
          <label for="playerName">Player Name</label>
          <input 
            type="text" 
            id="playerName" 
            v-model="formData.playerName" 
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
        </div>
        
        <div class="form-group">
          <label for="backstory">Backstory</label>
          <textarea 
            id="backstory" 
            v-model="formData.backstory" 
            rows="6"
            :disabled="readOnly"
          ></textarea>
        </div>
      </template>
      
      <!-- NPC specific fields -->
      <template v-if="entityType === 'npc'">
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
            <label for="occupation">Occupation</label>
            <input 
              type="text" 
              id="occupation" 
              v-model="formData.occupation" 
              :disabled="readOnly"
            />
          </div>
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
        
        <div class="form-group">
          <label for="relationships">Relationships</label>
          <textarea 
            id="relationships" 
            v-model="formData.relationships" 
            rows="4"
            :disabled="readOnly"
          ></textarea>
        </div>
      </template>
      
      <!-- Location specific fields -->
      <template v-if="entityType === 'location'">
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
          <label for="type">Type</label>
          <input 
            type="text" 
            id="type" 
            v-model="formData.type" 
            placeholder="City, Dungeon, Forest, etc."
            :disabled="readOnly"
          />
        </div>
        
        <div class="form-group">
          <label for="notableFeatures">Notable Features</label>
          <textarea 
            id="notableFeatures" 
            v-model="formData.notableFeatures" 
            rows="4"
            :disabled="readOnly"
          ></textarea>
        </div>
        
        <div class="form-group">
          <label for="inhabitants">Inhabitants</label>
          <textarea 
            id="inhabitants" 
            v-model="formData.inhabitants" 
            rows="4"
            :disabled="readOnly"
          ></textarea>
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
              placeholder="Weapon, Armor, Magical, etc."
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
          <label for="properties">Properties</label>
          <textarea 
            id="properties" 
            v-model="formData.properties" 
            rows="4"
            :disabled="readOnly"
          ></textarea>
        </div>
        
        <div class="form-group">
          <label for="history">History</label>
          <textarea 
            id="history" 
            v-model="formData.history" 
            rows="4"
            :disabled="readOnly"
          ></textarea>
        </div>
      </template>
      
      <!-- Session specific fields -->
      <template v-if="entityType === 'session'">
        <div class="form-row">
          <div class="form-group">
            <label for="sessionNumber">Session Number*</label>
            <input 
              type="number" 
              id="sessionNumber" 
              v-model.number="formData.sessionNumber" 
              required
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
        </div>
        
        <div class="form-group">
          <label for="title">Title*</label>
          <input 
            type="text" 
            id="title" 
            v-model="formData.title" 
            required
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
          <label for="locations">Locations Visited</label>
          <textarea 
            id="locations" 
            v-model="formData.locations" 
            rows="3"
            placeholder="Comma-separated list of locations"
            :disabled="readOnly"
          ></textarea>
        </div>
        
        <div class="form-group">
          <label for="characters">Characters Present</label>
          <textarea 
            id="characters" 
            v-model="formData.characters" 
            rows="3"
            placeholder="Comma-separated list of characters"
            :disabled="readOnly"
          ></textarea>
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
  data() {
    return {
      formData: {}
    };
  },
  watch: {
    entity: {
      immediate: true,
      handler(newValue) {
        // Deep clone the entity to avoid modifying the original
        this.formData = JSON.parse(JSON.stringify(newValue || {}));
        
        // Set default values for new entities
        if (Object.keys(this.formData).length === 0) {
          this.setDefaultValues();
        }
      }
    }
  },
  methods: {
    setDefaultValues() {
      // Set default values based on entity type
      const defaults = {
        // Common defaults
        name: '',
        description: '',
        
        // Entity-specific defaults
        character: {
          playerName: '',
          race: '',
          class: '',
          backstory: ''
        },
        npc: {
          race: '',
          occupation: '',
          location: '',
          relationships: ''
        },
        location: {
          region: '',
          type: '',
          notableFeatures: '',
          inhabitants: ''
        },
        item: {
          type: '',
          rarity: 'Common',
          properties: '',
          history: ''
        },
        session: {
          sessionNumber: this.getNextSessionNumber(),
          date: new Date().toISOString().split('T')[0],
          title: '',
          summary: '',
          locations: '',
          characters: ''
        }
      };
      
      // Apply common defaults
      this.formData = {
        ...this.formData,
        name: '',
        description: ''
      };
      
      // Apply entity-specific defaults
      if (defaults[this.entityType]) {
        this.formData = {
          ...this.formData,
          ...defaults[this.entityType]
        };
      }
    },
    
    getNextSessionNumber() {
      // This would ideally check existing sessions to determine the next number
      // For now, we'll just return a placeholder
      return 1;
    },
    
    saveEntity() {
      // Process data before emitting
      let processedData = { ...this.formData };
      
      // Special processing for sessions
      if (this.entityType === 'session') {
        // Generate an ID for new sessions if not present
        if (!processedData.id) {
          processedData.id = `session-${processedData.sessionNumber}`;
        }
        
        // Process locations and characters into arrays if they're strings
        if (typeof processedData.locations === 'string') {
          processedData.locations = processedData.locations
            .split(',')
            .map(item => item.trim())
            .filter(item => item);
        }
        
        if (typeof processedData.characters === 'string') {
          processedData.characters = processedData.characters
            .split(',')
            .map(item => item.trim())
            .filter(item => item);
        }
      }
      
      this.$emit('save', processedData);
    }
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
  border: 1px solid var(--border-color);
  background-color: rgba(0, 0, 0, 0.2);
  color: var(--color-text);
  border-radius: 4px;
  font-family: inherit;
}

input:focus, textarea:focus, select:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(var(--color-primary-rgb), 0.2);
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
  background-color: var(--color-primary);
  color: var(--color-background);
}

.btn-cancel {
  background-color: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--border-color);
  color: var(--color-text);
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
</style>
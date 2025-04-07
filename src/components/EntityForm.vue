<template>
  <div class="entity-form">
    <form @submit.prevent="submitForm">
      <div class="form-group">
        <label for="name">Name</label>
        <input 
          type="text" 
          id="name" 
          v-model="formData.name" 
          required
          class="form-control"
        />
      </div>

      <div v-if="entityType === 'character'" class="character-fields">
        <div class="form-group">
          <label for="player">Player Name</label>
          <input 
            type="text" 
            id="player" 
            v-model="formData.player" 
            class="form-control"
          />
        </div>

        <div class="form-group">
          <label for="race">Race</label>
          <input 
            type="text" 
            id="race" 
            v-model="formData.race" 
            class="form-control"
          />
        </div>

        <div class="form-group">
          <label for="class">Class</label>
          <input 
            type="text" 
            id="class" 
            v-model="formData.class" 
            class="form-control"
          />
        </div>

        <div class="form-group">
          <label for="level">Level</label>
          <input 
            type="number" 
            id="level" 
            v-model.number="formData.level" 
            class="form-control"
            min="1"
          />
        </div>

        <div class="form-group">
          <label for="background">Background</label>
          <input 
            type="text" 
            id="background" 
            v-model="formData.background" 
            class="form-control"
          />
        </div>

        <div class="form-group">
          <label for="bio">Biography</label>
          <textarea 
            id="bio" 
            v-model="formData.bio" 
            class="form-control"
            rows="5"
          ></textarea>
        </div>
      </div>

      <div class="form-group session-selection">
        <label for="sessionId">Associated Session</label>
        <select id="sessionId" v-model="formData.sessionId" class="form-control" required>
          <option value="session-admin">Admin Session (Default)</option>
          <option v-for="session in sessions" :key="session.id" :value="session.id">
            {{ session.title }}
          </option>
        </select>
        <small class="help-text">Select the session in which this entity was created or modified</small>
      </div>

      <div class="form-group">
        <label for="action-note">Action Description (Optional)</label>
        <input 
          type="text" 
          id="action-note" 
          v-model="formData.last_action" 
          class="form-control"
          placeholder="e.g., 'Added character backstory' or 'Updated character level'"
        />
        <small class="help-text">This will be displayed in the entity's history</small>
      </div>

      <div class="form-actions">
        <button type="button" @click="$emit('cancel')" class="cancel-button">Cancel</button>
        <button type="submit" class="save-button">Save {{ capitalizeFirst(entityType) }}</button>
      </div>
    </form>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue';
import worldData from '../store/worldData';

export default {
  name: 'EntityForm',
  props: {
    entityType: {
      type: String,
      required: true
    },
    entity: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['save', 'cancel'],
  setup(props, { emit }) {
    // Form data with defaults based on entity type
    const formData = ref({
      id: '',
      name: '',
      sessionId: 'session-admin',
      entityType: props.entityType,
      // Character-specific defaults
      player: '',
      race: '',
      class: '',
      level: 1,
      background: '',
      bio: '',
      // Optional action description
      last_action: ''
    });
    
    // Available sessions
    const sessions = ref([]);
    
    // Initialize form with entity data if provided
    watch(() => props.entity, (newEntity) => {
      if (newEntity && Object.keys(newEntity).length > 0) {
        // Merge entity data with formData, preserving defaults for missing fields
        formData.value = {
          ...formData.value,
          ...newEntity,
          entityType: props.entityType
        };
      }
    }, { immediate: true });
    
    // Load sessions for dropdown
    const loadSessions = async () => {
      try {
        sessions.value = await worldData.getAllSessions();
      } catch (error) {
        console.error('Failed to load sessions:', error);
      }
    };
    
    onMounted(loadSessions);
    
    // Capitalize first letter of a string
    const capitalizeFirst = (str) => {
      return str.charAt(0).toUpperCase() + str.slice(1);
    };
    
    // Submit the form
    const submitForm = () => {
      // If no ID, generate one based on entity type and timestamp
      if (!formData.value.id) {
        formData.value.id = `${props.entityType}-${Date.now()}`;
      }
      
      // Ensure entityType is set correctly
      formData.value.entityType = props.entityType;
      
      // Add a timestamp for the history entry
      formData.value.timestamp = new Date().toISOString();
      
      // Emit save event with form data
      emit('save', formData.value);
    };
    
    return {
      formData,
      sessions,
      capitalizeFirst,
      submitForm
    };
  }
};
</script>

<style scoped>
.entity-form {
  width: 100%;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.form-control {
  width: 100%;
  padding: 10px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background-color: rgba(0, 0, 0, 0.2);
  color: white;
  font-size: 1rem;
}

textarea.form-control {
  resize: vertical;
  min-height: 100px;
}

.help-text {
  display: block;
  margin-top: 5px;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.7);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 30px;
}

.save-button, .cancel-button {
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  margin-left: 10px;
}

.save-button {
  background-color: #4CAF50;
  color: white;
  border: none;
}

.cancel-button {
  background-color: transparent;
  border: 1px solid #aaa;
  color: #aaa;
}

.cancel-button:hover {
  border-color: white;
  color: white;
}

.character-fields {
  margin-top: 20px;
  padding: 20px;
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
}

@media (max-width: 768px) {
  .form-control {
    font-size: 16px; /* Prevent zoom on mobile */
  }
}
</style>
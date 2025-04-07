<template>
  <div class="admin-tools">
    <h2>Admin Tools</h2>
    
    <div class="tool-section">
      <h3>Entity Management</h3>
      <div class="entity-tabs">
        <button 
          @click="activeEntityType = 'character'" 
          :class="['tab-button', activeEntityType === 'character' ? 'active' : '']"
        >
          Characters
        </button>
        <button 
          @click="activeEntityType = 'npc'" 
          :class="['tab-button', activeEntityType === 'npc' ? 'active' : '']"
        >
          NPCs
        </button>
        <button 
          @click="activeEntityType = 'location'" 
          :class="['tab-button', activeEntityType === 'location' ? 'active' : '']"
        >
          Locations
        </button>
        <button 
          @click="activeEntityType = 'item'" 
          :class="['tab-button', activeEntityType === 'item' ? 'active' : '']"
        >
          Items
        </button>
        <button 
          @click="activeEntityType = 'session'" 
          :class="['tab-button', activeEntityType === 'session' ? 'active' : '']"
        >
          Sessions
        </button>
      </div>
      
      <div class="entity-list-container">
        <div class="entity-controls">
          <button @click="createNewEntity" class="primary-button">
            Create New {{ capitalizeFirst(activeEntityType) }}
          </button>
          <input 
            v-model="entitySearchQuery" 
            placeholder="Search..."
            class="search-input"
          />
        </div>
        
        <div v-if="isLoadingEntities" class="loading">Loading entities...</div>
        
        <div v-else class="entity-list">
          <div v-for="entity in filteredEntities" :key="entity.id" class="entity-item">
            <div class="entity-name">{{ entity.name }}</div>
            <div class="entity-actions">
              <button @click="editEntity(entity)" class="edit-button">Edit</button>
              <button @click="confirmDeleteEntity(entity)" class="delete-button">Delete</button>
            </div>
          </div>
          
          <div v-if="filteredEntities.length === 0" class="no-entities">
            No {{ activeEntityType }}s found.
          </div>
        </div>
      </div>
      
      <!-- Entity Edit Modal -->
      <div v-if="showEntityModal" class="modal">
        <div class="modal-content">
          <div class="modal-header">
            <h3>{{ isNewEntity ? 'Create' : 'Edit' }} {{ capitalizeFirst(activeEntityType) }}</h3>
            <button @click="closeEntityModal" class="close-button">&times;</button>
          </div>
          
          <div class="modal-body">
            <EntityForm 
              :entityType="activeEntityType"
              :entity="currentEntity"
              @save="saveEntity"
              @cancel="closeEntityModal"
            />
          </div>
        </div>
      </div>
      
      <!-- Delete Confirmation Modal -->
      <div v-if="showDeleteConfirmation" class="modal">
        <div class="modal-content">
          <div class="modal-header">
            <h3>Confirm Delete</h3>
            <button @click="showDeleteConfirmation = false" class="close-button">&times;</button>
          </div>
          
          <div class="modal-body">
            <p>Are you sure you want to delete {{ currentEntity.name }}?</p>
            <p class="warning">This action cannot be undone.</p>
            
            <div class="modal-actions">
              <button @click="showDeleteConfirmation = false" class="cancel-button">Cancel</button>
              <button @click="deleteEntity" class="delete-button">Delete</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="tool-section">
      <h3>Database Management</h3>
      <div class="event-counts" v-if="eventCounts">
        <p><strong>Total Events:</strong> {{ eventCounts.total }}</p>
        <ul>
          <li>History Entries: {{ eventCounts.historyEntries }}</li>
          <li>World History Events: {{ eventCounts.worldHistoryEvents }}</li>
          <li>Sessions: {{ eventCounts.sessions }}</li>
        </ul>
      </div>
      
      <div class="actions">
        <button 
          @click="seedDatabase" 
          :disabled="isLoading"
          class="primary-button"
        >
          {{ isLoading ? 'Seeding Database...' : 'Seed Firestore Database' }}
        </button>
        
        <div v-if="message" :class="['message', messageType]">
          {{ message }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import authService from '../services/AuthService';
import EntityForm from './EntityForm.vue';
import worldData from '../store/worldData';
import firestoreService from '../services/FirestoreService';

export default {
  name: 'AdminTools',
  components: {
    EntityForm
  },
  setup() {
    const isLoading = ref(false);
    const message = ref('');
    const messageType = ref('');
    const eventCounts = ref(null);
    
    // Entity management
    const activeEntityType = ref('character');
    const entities = ref({
      character: [],
      npc: [],
      location: [],
      item: [],
      session: []
    });
    const entitySearchQuery = ref('');
    const isLoadingEntities = ref(false);
    const showEntityModal = ref(false);
    const currentEntity = ref({});
    const isNewEntity = ref(false);
    const showDeleteConfirmation = ref(false);
    
    // Only authorized editors can see this component
    const isAuthorized = ref(authService.isAuthorizedEditor());
    
    // Computed property for filtered entities
    const filteredEntities = computed(() => {
      if (!entitySearchQuery.value) {
        return entities.value[activeEntityType.value];
      }
      
      const query = entitySearchQuery.value.toLowerCase();
      return entities.value[activeEntityType.value].filter(entity => 
        entity.name && entity.name.toLowerCase().includes(query)
      );
    });
    
    onMounted(async () => {
      // Get event counts
      eventCounts.value = getEventCounts();
      
      // Set up auth listener
      authService.addAuthListener((user, isEditor) => {
        isAuthorized.value = isEditor;
      });
      
      // Load entities
      await loadEntities('character');
    });
    
    // Watch for changes to activeEntityType and load entities if needed
    watch(activeEntityType, async (newType) => {
      if (entities.value[newType].length === 0) {
        await loadEntities(newType);
      }
    });
    
    async function loadEntities(type) {
      isLoadingEntities.value = true;
      
      try {
        let loadedEntities = [];
        
        // Use appropriate loading method based on entity type
        switch (type) {
          case 'character':
            loadedEntities = await worldData.getAllCharacters();
            break;
          case 'npc':
            loadedEntities = await worldData.getAllNpcs();
            break;
          case 'location':
            loadedEntities = await worldData.getLocations();
            break;
          case 'item':
            loadedEntities = await worldData.getAllItems();
            break;
          case 'session':
            loadedEntities = await worldData.getAllSessions();
            break;
        }
        
        entities.value[type] = loadedEntities;
      } catch (error) {
        console.error(`Error loading ${type}s:`, error);
        message.value = `Error loading ${type}s: ${error.message}`;
        messageType.value = 'error';
      } finally {
        isLoadingEntities.value = false;
      }
    }
    
    function createNewEntity() {
      currentEntity.value = {
        id: '', // Will be generated by Firebase or assigned when saved
        entityType: activeEntityType.value
      };
      isNewEntity.value = true;
      showEntityModal.value = true;
    }
    
    function editEntity(entity) {
      currentEntity.value = { ...entity };
      isNewEntity.value = false;
      showEntityModal.value = true;
    }
    
    function confirmDeleteEntity(entity) {
      currentEntity.value = entity;
      showDeleteConfirmation.value = true;
    }
    
    async function deleteEntity() {
      if (!isAuthorized.value) {
        message.value = 'You must be an authorized editor to perform this action.';
        messageType.value = 'error';
        showDeleteConfirmation.value = false;
        return;
      }
      
      try {
        isLoading.value = true;
        
        // Delete from Firestore
        await firestoreService.delete(
          `${activeEntityType.value}s`, // Collection name (e.g., "characters")
          currentEntity.value.id
        );
        
        // Remove from local array
        entities.value[activeEntityType.value] = entities.value[activeEntityType.value]
          .filter(e => e.id !== currentEntity.value.id);
        
        message.value = `${capitalizeFirst(activeEntityType.value)} deleted successfully.`;
        messageType.value = 'success';
      } catch (error) {
        console.error(`Error deleting ${activeEntityType.value}:`, error);
        message.value = `Error deleting ${activeEntityType.value}: ${error.message}`;
        messageType.value = 'error';
      } finally {
        isLoading.value = false;
        showDeleteConfirmation.value = false;
      }
    }
    
    async function saveEntity(entityData) {
      if (!isAuthorized.value) {
        message.value = 'You must be an authorized editor to perform this action.';
        messageType.value = 'error';
        closeEntityModal();
        return;
      }
      
      try {
        isLoading.value = true;
        
        // Use worldData for history-based entity creation/updates
        if (isNewEntity.value) {
          // Create new entity via history entry
          await worldData.createEntity(
            activeEntityType.value,
            entityData
          );
        } else {
          // Update existing entity via history entry
          await worldData.updateEntity(
            activeEntityType.value,
            entityData.id,
            entityData
          );
        }
        
        // Reload entities to reflect changes
        await loadEntities(activeEntityType.value);
        
        message.value = `${capitalizeFirst(activeEntityType.value)} ${isNewEntity.value ? 'created' : 'updated'} successfully.`;
        messageType.value = 'success';
      } catch (error) {
        console.error(`Error saving ${activeEntityType.value}:`, error);
        message.value = `Error saving ${activeEntityType.value}: ${error.message}`;
        messageType.value = 'error';
      } finally {
        isLoading.value = false;
        closeEntityModal();
      }
    }
    
    function closeEntityModal() {
      showEntityModal.value = false;
      currentEntity.value = {};
    }
    
    function capitalizeFirst(str) {
      return str.charAt(0).toUpperCase() + str.slice(1);
    }
    
    return {
      isLoading,
      message,
      messageType,
      seedDatabase,
      eventCounts,
      isAuthorized,
      activeEntityType,
      entities,
      entitySearchQuery,
      isLoadingEntities,
      filteredEntities,
      createNewEntity,
      editEntity,
      confirmDeleteEntity,
      deleteEntity,
      saveEntity,
      showEntityModal,
      currentEntity,
      isNewEntity,
      closeEntityModal,
      showDeleteConfirmation,
      capitalizeFirst
    };
  }
};
</script>

<style scoped>
.admin-tools {
  padding: 20px;
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  margin-bottom: 20px;
}

.tool-section {
  margin-bottom: 30px;
  padding: 20px;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
}

.actions {
  margin-top: 20px;
}

.primary-button, .edit-button, .delete-button, .cancel-button {
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  border: none;
  margin-right: 8px;
}

.primary-button {
  background-color: #4CAF50;
  color: white;
}

.edit-button {
  background-color: #2196F3;
  color: white;
}

.delete-button {
  background-color: #F44336;
  color: white;
}

.cancel-button {
  background-color: #9E9E9E;
  color: white;
}

.primary-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.message {
  margin-top: 10px;
  padding: 10px;
  border-radius: 4px;
}

.success {
  background-color: #d4edda;
  color: #155724;
}

.error {
  background-color: #f8d7da;
  color: #721c24;
}

.info {
  background-color: #d1ecf1;
  color: #0c5460;
}

.event-counts {
  background-color: rgba(0, 0, 0, 0.1);
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 15px;
}

/* Entity management styles */
.entity-tabs {
  display: flex;
  margin-bottom: 20px;
  overflow-x: auto;
}

.tab-button {
  padding: 10px 20px;
  background-color: rgba(0, 0, 0, 0.1);
  border: none;
  cursor: pointer;
  font-weight: 500;
}

.tab-button.active {
  background-color: rgba(0, 0, 0, 0.3);
  color: white;
}

.entity-list-container {
  margin-top: 20px;
}

.entity-controls {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
}

.search-input {
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #ccc;
  width: 250px;
  background-color: rgba(255, 255, 255, 0.9);
}

.entity-list {
  max-height: 400px;
  overflow-y: auto;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
}

.entity-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.entity-item:last-child {
  border-bottom: none;
}

.entity-name {
  font-weight: 500;
}

.entity-actions {
  display: flex;
}

.loading, .no-entities {
  padding: 20px;
  text-align: center;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
}

/* Modal styles */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: #242424;
  border-radius: 8px;
  width: 80%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-body {
  padding: 20px;
}

.close-button {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #aaa;
}

.close-button:hover {
  color: white;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.warning {
  color: #F44336;
  font-weight: 500;
}

@media (max-width: 768px) {
  .entity-controls {
    flex-direction: column;
    gap: 10px;
  }
  
  .search-input {
    width: 100%;
  }
  
  .modal-content {
    width: 95%;
  }
}
</style>

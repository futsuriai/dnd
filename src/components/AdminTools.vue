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
              <button @click="viewEntityHistory(entity)" class="history-button">History</button>
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
      
      <!-- Entity History Modal -->
      <div v-if="showHistoryModal" class="modal">
        <div class="modal-content">
          <div class="modal-header">
            <h3>{{ currentEntity.name }} - History</h3>
            <button @click="showHistoryModal = false" class="close-button">&times;</button>
          </div>
          
          <div class="modal-body">
            <EntityHistoryViewer 
              v-if="currentEntity.id" 
              :entityType="activeEntityType"
              :entityId="currentEntity.id"
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
      <div class="data-source-info">
        <p><strong>Current Data Source:</strong> {{ dataSource.source || 'loading...' }}</p>
      </div>

      <div class="event-counts" v-if="eventCounts">
        <p><strong>Total Events:</strong> {{ eventCounts.total }}</p>
        <ul>
          <li>History Entries: {{ eventCounts.historyEntries }}</li>
          <li>Sessions: {{ eventCounts.sessions }}</li>
        </ul>
      </div>
      
      <div class="import-export-controls">
        <h4>Import/Export Data</h4>
        <div class="button-group">
          <button @click="showImportDialog = true" class="action-button">Import Data</button>
          <button @click="exportData" class="action-button">Export Data</button>
        </div>
      </div>
      
      <!-- Import Dialog -->
      <div v-if="showImportDialog" class="modal">
        <div class="modal-content">
          <div class="modal-header">
            <h3>Import Data</h3>
            <button @click="showImportDialog = false" class="close-button">&times;</button>
          </div>
          
          <div class="modal-body">
            <div class="form-group">
              <label for="importText">Paste JSON data:</label>
              <textarea 
                id="importText" 
                v-model="importText" 
                class="form-control" 
                rows="10"
                placeholder="Paste your exported data here..."
              ></textarea>
            </div>
            
            <div class="form-group checkbox-group">
              <label>
                <input type="checkbox" v-model="clearBeforeImport">
                Clear existing data before import (WARNING: This will delete all existing data)
              </label>
            </div>
            
            <div class="modal-actions">
              <button @click="showImportDialog = false" class="cancel-button">Cancel</button>
              <button @click="importData" class="primary-button" :disabled="!importText">
                Import Data
              </button>
            </div>
          </div>
        </div>
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

<script lang="ts">
import { defineComponent, ref, computed, onMounted, watch } from 'vue';
import EntityForm from './EntityForm.vue';
import EntityHistoryViewer from './EntityHistoryViewer.vue';
import worldData, { Entity, Session, DataSource } from '../store/worldData';
import firestoreService from '../services/FirestoreService';
import { historyBasedDataExpanded } from '../store/consolidatedData';

interface EventCounts {
  historyEntries: number;
  sessions: number;
  total: number;
}

interface EntityCollection {
  character: Entity[];
  npc: Entity[];
  location: Entity[];
  item: Entity[];
}

export default defineComponent({
  name: 'AdminTools',
  components: {
    EntityForm,
    EntityHistoryViewer
  },
  setup() {
    const isLoading = ref<boolean>(false);
    const message = ref<string>('');
    const messageType = ref<string>('');
    const eventCounts = ref<EventCounts | null>(null);
    const dataSource = ref<DataSource>({ source: 'loading...', initialized: false });
    
    // Entity management
    const activeEntityType = ref<keyof EntityCollection>('character');
    const entities = ref<EntityCollection>({
      character: [],
      npc: [],
      location: [],
      item: []
    });
    const entitySearchQuery = ref<string>('');
    const isLoadingEntities = ref<boolean>(false);
    const showEntityModal = ref<boolean>(false);
    const showHistoryModal = ref<boolean>(false);
    const currentEntity = ref<Entity>({
      id: '',
      entityType: 'character'
    });
    const isNewEntity = ref<boolean>(false);
    const showDeleteConfirmation = ref<boolean>(false);
    
    // Import/Export
    const showImportDialog = ref<boolean>(false);
    const importText = ref<string>('');
    const clearBeforeImport = ref<boolean>(false);
    
    // Computed property for filtered entities
    const filteredEntities = computed(() => {
      if (!entitySearchQuery.value) {
        return entities.value[activeEntityType.value as keyof EntityCollection];
      }
      
      const query = entitySearchQuery.value.toLowerCase();
      return entities.value[activeEntityType.value as keyof EntityCollection].filter(entity => 
        entity.name && entity.name.toLowerCase().includes(query)
      );
    });
    
    onMounted(async () => {
      // Initialize world data and determine data source
      dataSource.value = await worldData.getDataSource();
      await worldData.initWorldData();
      
      // Update event counts
      await updateEventCounts();
      
      // Load entities
      await loadEntities('character');
    });
    
    // Watch for changes to activeEntityType and load entities if needed
    watch(activeEntityType, async (newType) => {
      if (entities.value[newType as keyof EntityCollection].length === 0) {
        await loadEntities(newType);
      }
    });
    
    async function loadEntities(type: string): Promise<void> {
      isLoadingEntities.value = true;
      
      try {
        let loadedEntities: Entity[] = [];
        
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
        }
        
        entities.value[type as keyof EntityCollection] = loadedEntities;
      } catch (error: any) {
        console.error(`Error loading ${type}s:`, error);
        message.value = `Error loading ${type}s: ${error.message}`;
        messageType.value = 'error';
      } finally {
        isLoadingEntities.value = false;
      }
    }
    
    // Get event counts from the database
    async function updateEventCounts(): Promise<void> {
      try {
        const historyEntries = await firestoreService.getAllHistoryEvents();
        const sessions = await firestoreService.getAllSessions();
        
        eventCounts.value = {
          historyEntries: historyEntries.length,
          sessions: sessions.length,
          total: historyEntries.length + sessions.length
        };
      } catch (error) {
        console.error('Error getting event counts:', error);
        eventCounts.value = { historyEntries: 0, sessions: 0, total: 0 };
      }
    }
    
    // Seed the database with initial data
    async function seedDatabase(): Promise<void> {
      try {
        isLoading.value = true;
        message.value = 'Seeding database...';
        messageType.value = 'info';
        
        // Use the consolidated data from the store
        await firestoreService.seedDatabase(historyBasedDataExpanded);
        
        // Reinitialize world data to use Firestore
        await worldData.initWorldData({ forceInit: true });
        dataSource.value = await worldData.getDataSource();
        
        // Reload entities and update counts
        await loadEntities(activeEntityType.value);
        await updateEventCounts();
        
        message.value = 'Database seeded successfully!';
        messageType.value = 'success';
      } catch (error: any) {
        console.error('Error seeding database:', error);
        message.value = `Error seeding database: ${error.message}`;
        messageType.value = 'error';
      } finally {
        isLoading.value = false;
      }
    }
    
    function createNewEntity(): void {
      currentEntity.value = {
        id: '', // Will be generated when saved
        entityType: activeEntityType.value as string
      };
      isNewEntity.value = true;
      showEntityModal.value = true;
    }
    
    function editEntity(entity: Entity): void {
      currentEntity.value = { ...entity };
      isNewEntity.value = false;
      showEntityModal.value = true;
    }
    
    function viewEntityHistory(entity: Entity): void {
      currentEntity.value = { ...entity };
      showHistoryModal.value = true;
    }
    
    function confirmDeleteEntity(entity: Entity): void {
      currentEntity.value = entity;
      showDeleteConfirmation.value = true;
    }
    
    async function deleteEntity(): Promise<void> {
      try {
        isLoading.value = true;
        
        // Use worldData to create a deletion history entry
        await worldData.deleteEntity(
          activeEntityType.value,
          currentEntity.value.id
        );
        
        // Reload entities to reflect the deletion
        await loadEntities(activeEntityType.value);
        await updateEventCounts();
        
        message.value = `${capitalizeFirst(activeEntityType.value)} marked as deleted.`;
        messageType.value = 'success';
      } catch (error: any) {
        console.error(`Error deleting ${activeEntityType.value}:`, error);
        message.value = `Error deleting ${activeEntityType.value}: ${error.message}`;
        messageType.value = 'error';
      } finally {
        isLoading.value = false;
        showDeleteConfirmation.value = false;
      }
    }
    
    async function saveEntity(entityData: Record<string, any>): Promise<void> {
      try {
        isLoading.value = true;
        
        // Use worldData for history-based entity creation/updates
        if (isNewEntity.value) {
          // Create new entity via history entry
          await worldData.createEntity(
            activeEntityType.value,
            entityData
          );
          
          message.value = `${capitalizeFirst(activeEntityType.value)} created successfully.`;
        } else {
          // Update existing entity via history entry
          await worldData.updateEntity(
            activeEntityType.value,
            entityData.id,
            entityData
          );
          
          message.value = `${capitalizeFirst(activeEntityType.value)} updated successfully.`;
        }
        
        // Reload entities and update counts
        await loadEntities(activeEntityType.value);
        await updateEventCounts();
        
        messageType.value = 'success';
      } catch (error: any) {
        console.error(`Error saving ${activeEntityType.value}:`, error);
        message.value = `Error saving ${activeEntityType.value}: ${error.message}`;
        messageType.value = 'error';
      } finally {
        isLoading.value = false;
        closeEntityModal();
      }
    }
    
    async function importData(): Promise<void> {
      if (!importText.value) {
        alert('Please provide JSON data to import.');
        return;
      }
      
      try {
        isLoading.value = true;
        const data = JSON.parse(importText.value);
        
        // If clearBeforeImport is true, clear the database first
        if (clearBeforeImport.value) {
          await firestoreService.clearDatabase();
        }
        
        // Use the seedDatabase method to import data
        await firestoreService.seedDatabase(data);
        
        // Reload all data
        await worldData.initWorldData({ forceInit: true });
        dataSource.value = await worldData.getDataSource();
        await loadEntities(activeEntityType.value);
        await updateEventCounts();
        
        showImportDialog.value = false;
        importText.value = '';
        
        message.value = 'Data imported successfully!';
        messageType.value = 'success';
      } catch (error: any) {
        console.error('Error importing data:', error);
        message.value = 'Failed to import data. Please check your JSON format and try again.';
        messageType.value = 'error';
      } finally {
        isLoading.value = false;
      }
    }
    
    async function exportData(): Promise<void> {
      try {
        isLoading.value = true;
        
        // Use the exportDataInHistoryFormat to get data
        const exportData = await firestoreService.exportDataInHistoryFormat();
        
        // Convert to JSON string with pretty formatting
        const jsonString = JSON.stringify(exportData, null, 2);
        
        // Create a blob and download it
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        // Create a download link and click it
        const a = document.createElement('a');
        a.href = url;
        a.download = `dnd-campaign-export-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        
        // Clean up
        setTimeout(() => {
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        }, 100);
        
        message.value = 'Data exported successfully!';
        messageType.value = 'success';
      } catch (error: any) {
        console.error('Error exporting data:', error);
        message.value = `Error exporting data: ${error.message}`;
        messageType.value = 'error';
      } finally {
        isLoading.value = false;
      }
    }
    
    function closeEntityModal(): void {
      showEntityModal.value = false;
      currentEntity.value = {
        id: '',
        entityType: activeEntityType.value as string
      };
    }
    
    function capitalizeFirst(str: string): string {
      return str.charAt(0).toUpperCase() + str.slice(1);
    }
    
    return {
      isLoading,
      message,
      messageType,
      seedDatabase,
      eventCounts,
      dataSource,
      activeEntityType,
      entities,
      entitySearchQuery,
      isLoadingEntities,
      filteredEntities,
      createNewEntity,
      editEntity,
      viewEntityHistory,
      confirmDeleteEntity,
      deleteEntity,
      saveEntity,
      showEntityModal,
      showHistoryModal,
      currentEntity,
      isNewEntity,
      closeEntityModal,
      showDeleteConfirmation,
      capitalizeFirst,
      showImportDialog,
      importText,
      clearBeforeImport,
      importData,
      exportData
    };
  }
});
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

.primary-button, .edit-button, .delete-button, .cancel-button, .history-button, .action-button {
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

.history-button {
  background-color: #9C27B0;
  color: white;
}

.action-button {
  background-color: #607D8B;
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

.event-counts, .data-source-info {
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

/* Import/Export styles */
.import-export-controls {
  margin-top: 30px;
}

.button-group {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.checkbox-group {
  display: flex;
  align-items: center;
}

.checkbox-group input {
  margin-right: 10px;
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

  .entity-actions {
    flex-wrap: wrap;
    gap: 5px;
  }

  .entity-tabs {
    flex-wrap: wrap;
  }

  .tab-button {
    flex-grow: 1;
    text-align: center;
  }
}
</style>

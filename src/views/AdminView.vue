<template>
  <div class="admin-page">
    <h1>Admin Dashboard</h1>
    
    <div v-if="!isAuthorized" class="unauthorized-container">
      <div class="unauthorized-message">
        <h2>Restricted Area</h2>
        <p>You need to be logged in as an authorized editor to access this page.</p>
        <AuthComponent />
      </div>
    </div>
    
    <div v-else class="admin-content">
      <div class="dashboard-header">
        <h2>Campaign Manager</h2>
        <p>Welcome, {{ user.displayName }}. Here you can manage all your campaign data.</p>
      </div>
      
      <div class="section-tabs">
        <button 
          v-for="section in sections" 
          :key="section.id"
          :class="['tab-button', { active: activeSection === section.id }]"
          @click="activeSection = section.id">
          {{ section.name }}
        </button>
      </div>
      
      <div class="admin-section">
        <!-- Characters Section -->
        <div v-if="activeSection === 'characters'" class="entity-editor">
          <h3>Manage Characters</h3>
          <button class="new-entity-button" @click="createNewEntity('character')">
            Add New Character
          </button>
          
          <div class="entity-list">
            <div v-for="entity in characters" :key="entity.id" class="entity-item">
              <div class="entity-name">{{ entity.name }}</div>
              <div class="entity-actions">
                <button @click="editEntity('character', entity)">Edit</button>
                <button class="delete-button" @click="confirmDelete('character', entity)">Delete</button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- NPCs Section -->
        <div v-if="activeSection === 'npcs'" class="entity-editor">
          <h3>Manage NPCs</h3>
          <button class="new-entity-button" @click="createNewEntity('npc')">
            Add New NPC
          </button>
          
          <div class="entity-list">
            <div v-for="entity in npcs" :key="entity.id" class="entity-item">
              <div class="entity-name">{{ entity.name }}</div>
              <div class="entity-actions">
                <button @click="editEntity('npc', entity)">Edit</button>
                <button class="delete-button" @click="confirmDelete('npc', entity)">Delete</button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Locations Section -->
        <div v-if="activeSection === 'locations'" class="entity-editor">
          <h3>Manage Locations</h3>
          <button class="new-entity-button" @click="createNewEntity('location')">
            Add New Location
          </button>
          
          <div class="entity-list">
            <div v-for="entity in locations" :key="entity.id" class="entity-item">
              <div class="entity-name">{{ entity.name }}</div>
              <div class="entity-actions">
                <button @click="editEntity('location', entity)">Edit</button>
                <button class="delete-button" @click="confirmDelete('location', entity)">Delete</button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Items Section -->
        <div v-if="activeSection === 'items'" class="entity-editor">
          <h3>Manage Items</h3>
          <button class="new-entity-button" @click="createNewEntity('item')">
            Add New Item
          </button>
          
          <div class="entity-list">
            <div v-for="entity in items" :key="entity.id" class="entity-item">
              <div class="entity-name">{{ entity.name }}</div>
              <div class="entity-actions">
                <button @click="editEntity('item', entity)">Edit</button>
                <button class="delete-button" @click="confirmDelete('item', entity)">Delete</button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Sessions Section -->
        <div v-if="activeSection === 'sessions'" class="entity-editor">
          <h3>Manage Sessions</h3>
          <button class="new-entity-button" @click="createNewEntity('session')">
            Add New Session
          </button>
          
          <div class="entity-list">
            <div v-for="entity in sessions" :key="entity.id" class="entity-item">
              <div class="entity-name">{{ entity.title || entity.id }}</div>
              <div class="entity-actions">
                <button @click="editEntity('session', entity)">Edit</button>
                <button class="delete-button" @click="confirmDelete('session', entity)">Delete</button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Database Management Section -->
        <div v-if="activeSection === 'database'" class="database-management">
          <h3>Database Management</h3>
          
          <div class="database-actions">
            <div class="action-card">
              <h4>Import Data</h4>
              <p>Import JSON data to populate the Firestore database.</p>
              <button @click="showImportDialog = true">Import Data</button>
            </div>
            
            <div class="action-card">
              <h4>Export Data</h4>
              <p>Export all data from Firestore as JSON.</p>
              <button @click="exportData">Export Data</button>
            </div>
            
            <div class="action-card danger-zone">
              <h4>Danger Zone</h4>
              <p>These actions cannot be undone!</p>
              <button class="delete-button" @click="confirmClearDatabase">Clear Database</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Modal for entity editing -->
    <div v-if="showEntityModal" class="modal-overlay" @click.self="cancelEdit">
      <div class="modal-content">
        <h3>{{ isEditing ? 'Edit' : 'Create' }} {{ capitalizeFirstLetter(currentEntityType) }}</h3>
        
        <div class="form-content">
          <EntityForm
            :entityType="currentEntityType"
            :entity="currentEntity"
            @save="saveEntity"
            @cancel="cancelEdit"
          />
        </div>
      </div>
    </div>
    
    <!-- Import dialog -->
    <div v-if="showImportDialog" class="modal-overlay" @click.self="showImportDialog = false">
      <div class="modal-content">
        <h3>Import Data</h3>
        
        <div class="import-options">
          <div class="form-group">
            <label for="importFile">Upload JSON File:</label>
            <input type="file" id="importFile" accept=".json" @change="handleFileUpload">
          </div>
          
          <div class="or-divider">OR</div>
          
          <div class="form-group">
            <label for="importText">Paste JSON:</label>
            <textarea id="importText" v-model="importText" placeholder="Paste JSON data here..."></textarea>
          </div>
        </div>
        
        <div class="import-options">
          <div class="form-check">
            <input type="checkbox" id="clearBeforeImport" v-model="clearBeforeImport">
            <label for="clearBeforeImport">Clear existing data before import</label>
          </div>
        </div>
        
        <div class="modal-actions">
          <button class="cancel-button" @click="showImportDialog = false">Cancel</button>
          <button class="save-button" @click="importData">Import</button>
        </div>
      </div>
    </div>
    
    <!-- Confirmation dialog -->
    <div v-if="showConfirmDialog" class="modal-overlay" @click.self="showConfirmDialog = false">
      <div class="modal-content confirmation-dialog">
        <h3>{{ confirmTitle }}</h3>
        <p>{{ confirmMessage }}</p>
        
        <div class="modal-actions">
          <button class="cancel-button" @click="showConfirmDialog = false">Cancel</button>
          <button class="delete-button" @click="confirmAction">{{ confirmActionText }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue';
import AuthComponent from '../components/AuthComponent.vue';
import EntityForm from '../components/EntityForm.vue';
import worldData from '../store/worldData';
import authService from '../services/AuthService';
import firestoreService from '../services/FirestoreService';

export default {
  name: 'AdminView',
  components: {
    AuthComponent,
    EntityForm
  },
  data() {
    return {
      isAuthorized: false,
      user: null,
      activeSection: 'characters',
      sections: [
        { id: 'characters', name: 'Characters' },
        { id: 'npcs', name: 'NPCs' },
        { id: 'locations', name: 'Locations' },
        { id: 'items', name: 'Items' },
        { id: 'sessions', name: 'Sessions' },
        { id: 'database', name: 'Database' }
      ],
      characters: [],
      npcs: [],
      locations: [],
      items: [],
      sessions: [],
      
      // Entity editing
      showEntityModal: false,
      isEditing: false,
      currentEntityType: '',
      currentEntity: null,
      
      // Import/Export
      showImportDialog: false,
      importText: '',
      clearBeforeImport: false,
      
      // Confirmation dialog
      showConfirmDialog: false,
      confirmTitle: '',
      confirmMessage: '',
      confirmActionText: 'Confirm',
      confirmAction: () => {}
    };
  },
  created() {
    // Subscribe to auth state changes
    this.unsubscribe = authService.addAuthListener((user, isEditor) => {
      this.user = user;
      this.isAuthorized = isEditor;
      
      // Load data if authorized
      if (isEditor) {
        this.loadAllData();
      }
    });
  },
  beforeUnmount() {
    // Clean up listener on component unmount
    if (this.unsubscribe) {
      this.unsubscribe();
    }
  },
  methods: {
    capitalizeFirstLetter(string) {
      return string.charAt(0).toUpperCase() + string.slice(1);
    },
    
    async loadAllData() {
      try {
        // Load all entity types in parallel
        const [characters, npcs, locations, items, sessions] = await Promise.all([
          firestoreService.getAllCharacters(),
          firestoreService.getAllNpcs(),
          firestoreService.getAllLocations(),
          firestoreService.getAllItems(),
          firestoreService.getAllSessions()
        ]);
        
        this.characters = characters;
        this.npcs = npcs;
        this.locations = locations;
        this.items = items;
        this.sessions = sessions;
      } catch (error) {
        console.error('Error loading data:', error);
        alert('Failed to load data. Please try again.');
      }
    },
    
    // Entity CRUD
    createNewEntity(type) {
      this.isEditing = false;
      this.currentEntityType = type;
      this.currentEntity = {};
      this.showEntityModal = true;
    },
    
    editEntity(type, entity) {
      this.isEditing = true;
      this.currentEntityType = type;
      this.currentEntity = { ...entity };
      this.showEntityModal = true;
    },
    
    cancelEdit() {
      this.showEntityModal = false;
      this.currentEntity = null;
    },
    
    async saveEntity(entityData) {
      try {
        if (this.isEditing) {
          await firestoreService.update(
            this.currentEntityType + 's', 
            entityData.id, 
            entityData
          );
        } else {
          await firestoreService.create(
            this.currentEntityType + 's', 
            entityData
          );
        }
        
        // Reload data after save
        this.loadAllData();
        this.showEntityModal = false;
      } catch (error) {
        console.error('Error saving entity:', error);
        alert('Failed to save. Please try again.');
      }
    },
    
    confirmDelete(type, entity) {
      this.confirmTitle = `Delete ${this.capitalizeFirstLetter(type)}`;
      this.confirmMessage = `Are you sure you want to delete ${entity.name || entity.title || entity.id}? This cannot be undone.`;
      this.confirmActionText = 'Delete';
      this.confirmAction = () => this.deleteEntity(type, entity.id);
      this.showConfirmDialog = true;
    },
    
    async deleteEntity(type, id) {
      try {
        await firestoreService.delete(type + 's', id);
        this.loadAllData();
        this.showConfirmDialog = false;
      } catch (error) {
        console.error('Error deleting entity:', error);
        alert('Failed to delete. Please try again.');
      }
    },
    
    // Database management
    handleFileUpload(event) {
      const file = event.target.files[0];
      if (!file) return;
      
      const reader = new FileReader();
      reader.onload = (e) => {
        this.importText = e.target.result;
      };
      reader.readAsText(file);
    },
    
    async importData() {
      if (!this.importText) {
        alert('Please provide JSON data to import.');
        return;
      }
      
      try {
        const data = JSON.parse(this.importText);
        
        // If clearBeforeImport is true, clear the database first
        if (this.clearBeforeImport) {
          await firestoreService.clearDatabase();
        }
        
        // Use the seedDatabase method to import data
        await firestoreService.seedDatabase(data);
        
        this.loadAllData();
        this.showImportDialog = false;
        alert('Data imported successfully!');
      } catch (error) {
        console.error('Error importing data:', error);
        alert('Failed to import data. Please check your JSON format and try again.');
      }
    },
    
    async exportData() {
      try {
        // Use the new exportDataInHistoryFormat method to get data in the same format
        // as historyBasedDataExpanded (sessions + historyEntries)
        const exportData = await firestoreService.exportDataInHistoryFormat();
        
        // Convert to JSON string
        const jsonString = JSON.stringify(exportData, null, 2);
        
        // Create download link
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        // Create temp link and click it
        const a = document.createElement('a');
        a.href = url;
        a.download = `dnd-campaign-export-${new Date().toISOString().slice(0, 10)}.json`;
        document.body.appendChild(a);
        a.click();
        
        // Clean up
        setTimeout(() => {
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        }, 100);
      } catch (error) {
        console.error('Error exporting data:', error);
        alert('Failed to export data. Please try again.');
      }
    },
    
    confirmClearDatabase() {
      this.confirmTitle = 'Clear Database';
      this.confirmMessage = 'Are you sure you want to clear ALL data from the database? This action cannot be undone!';
      this.confirmActionText = 'Clear Database';
      this.confirmAction = this.clearDatabase;
      this.showConfirmDialog = true;
    },
    
    async clearDatabase() {
      try {
        await firestoreService.clearDatabase();
        this.loadAllData();
        this.showConfirmDialog = false;
        alert('Database cleared successfully.');
      } catch (error) {
        console.error('Error clearing database:', error);
        alert('Failed to clear database. Please try again.');
      }
    }
  }
};
</script>

<style scoped>
.admin-page {
  padding: 2rem 0;
}

.unauthorized-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}

.unauthorized-message {
  text-align: center;
  max-width: 500px;
  padding: 2rem;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--border-color);
}

.admin-content {
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.dashboard-header {
  margin-bottom: 2rem;
}

.section-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 1rem;
}

.tab-button {
  padding: 0.5rem 1rem;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--border-color);
  color: var(--color-text);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tab-button:hover {
  background: rgba(0, 0, 0, 0.4);
}

.tab-button.active {
  background: var(--color-primary);
  color: var(--color-background);
  border-color: var(--color-primary);
}

.admin-section {
  min-height: 300px;
}

.entity-editor h3 {
  margin-bottom: 1rem;
}

.new-entity-button {
  padding: 0.5rem 1rem;
  background: var(--color-primary);
  color: var(--color-background);
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 1.5rem;
  font-weight: bold;
}

.entity-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.entity-item {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.entity-name {
  font-weight: bold;
  font-size: 1.1rem;
}

.entity-actions {
  display: flex;
  gap: 0.5rem;
}

.entity-actions button {
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  cursor: pointer;
  background: rgba(0, 0, 0, 0.3);
  color: var(--color-text);
  border: 1px solid var(--border-color);
}

.delete-button {
  background: rgba(220, 53, 69, 0.2) !important;
  color: #ff6b6b !important;
  border: 1px solid rgba(220, 53, 69, 0.4) !important;
}

.delete-button:hover {
  background: rgba(220, 53, 69, 0.4) !important;
}

/* Database management */
.database-management {
  margin-top: 1rem;
}

.database-actions {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1.5rem;
}

.action-card {
  background: rgba(0, 0, 0, 0.1);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1.5rem;
}

.action-card h4 {
  margin-top: 0;
  margin-bottom: 0.5rem;
}

.action-card p {
  margin-bottom: 1rem;
  opacity: 0.8;
}

.action-card button {
  width: 100%;
  padding: 0.5rem;
  background: var(--color-primary);
  color: var(--color-background);
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.danger-zone {
  background: rgba(220, 53, 69, 0.05);
  border-color: rgba(220, 53, 69, 0.2);
}

.danger-zone h4 {
  color: #ff6b6b;
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: var(--color-background);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 2rem;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
}

.modal-actions button {
  padding: 0.5rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
}

.cancel-button {
  background: rgba(0, 0, 0, 0.2);
  color: var(--color-text);
  border: 1px solid var(--border-color);
}

.save-button {
  background: var(--color-primary);
  color: var(--color-background);
  border: none;
}

/* Import dialog */
.import-options {
  margin-bottom: 1.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
}

.form-group textarea {
  width: 100%;
  height: 150px;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.1);
  border: 1px solid var(--border-color);
  color: var(--color-text);
  border-radius: 4px;
}

.or-divider {
  text-align: center;
  margin: 1rem 0;
  font-weight: bold;
  position: relative;
}

.or-divider::before,
.or-divider::after {
  content: "";
  position: absolute;
  top: 50%;
  width: 40%;
  height: 1px;
  background: var(--border-color);
}

.or-divider::before {
  left: 0;
}

.or-divider::after {
  right: 0;
}

.form-check {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Confirmation dialog */
.confirmation-dialog {
  max-width: 450px;
}

@media (max-width: 768px) {
  .entity-list {
    grid-template-columns: 1fr;
  }
  
  .database-actions {
    grid-template-columns: 1fr;
  }
  
  .section-tabs {
    flex-wrap: nowrap;
    overflow-x: auto;
    padding-bottom: 0.5rem;
  }
  
  .tab-button {
    white-space: nowrap;
  }
}
</style>
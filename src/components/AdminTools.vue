<template>
  <div class="admin-tools">
    <h2>Admin Tools</h2>
    
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
import { ref, onMounted } from 'vue';
import { seedFirestore, getEventCounts } from '../scripts/seedFirestore';
import authService from '../services/AuthService';

export default {
  name: 'AdminTools',
  setup() {
    const isLoading = ref(false);
    const message = ref('');
    const messageType = ref('');
    const eventCounts = ref(null);
    
    // Only authorized editors can see this component
    const isAuthorized = ref(authService.isAuthorizedEditor());
    
    onMounted(() => {
      // Get event counts
      eventCounts.value = getEventCounts();
      
      // Set up auth listener
      authService.addAuthListener((user, isEditor) => {
        isAuthorized.value = isEditor;
      });
    });
    
    async function seedDatabase() {
      if (!isAuthorized.value) {
        message.value = 'You must be an authorized editor to perform this action.';
        messageType.value = 'error';
        return;
      }
      
      try {
        isLoading.value = true;
        message.value = 'Seeding database, please wait...';
        messageType.value = 'info';
        
        await seedFirestore();
        
        message.value = 'Database seeded successfully!';
        messageType.value = 'success';
      } catch (error) {
        console.error('Error seeding database:', error);
        message.value = `Error: ${error.message}`;
        messageType.value = 'error';
      } finally {
        isLoading.value = false;
      }
    }
    
    return {
      isLoading,
      message,
      messageType,
      seedDatabase,
      eventCounts,
      isAuthorized
    };
  }
};
</script>

<style scoped>
.admin-tools {
  padding: 20px;
  background-color: #f5f5f5;
  border-radius: 8px;
  margin-bottom: 20px;
}

.tool-section {
  margin-bottom: 20px;
}

.actions {
  margin-top: 20px;
}

.primary-button {
  background-color: #4CAF50;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
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
  background-color: #e9ecef;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 15px;
}
</style>

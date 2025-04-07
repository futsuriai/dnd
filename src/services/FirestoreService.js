import { db, dbPrefix } from '../firebaseConfig';
import {
  collection,
  doc,
  addDoc,
  setDoc,
  getDoc,
  getDocs,
  updateDoc,
  deleteDoc,
  query,
  where,
  orderBy,
  limit,
  Timestamp,
  serverTimestamp
} from 'firebase/firestore';
import { getAuth } from 'firebase/auth';

class FirestoreService {
  constructor() {
    // Use the prefix to separate dev and prod data
    this.collectionsPrefix = dbPrefix;
  }

  // Helper to get the prefixed collection name
  getCollection(collectionName) {
    return `${this.collectionsPrefix}${collectionName}`;
  }

  // Get current user ID for history tracking
  getCurrentUserId() {
    const auth = getAuth();
    return auth.currentUser ? auth.currentUser.uid : 'system';
  }

  // CRUD operations with history tracking
  async create(collectionName, data, options = {}) {
    try {
      const { trackHistory = true, sessionId = null, changeType = 'creation' } = options;
      
      // Add created timestamp
      const dataWithTimestamp = {
        ...data,
        createdAt: serverTimestamp(),
        updatedAt: serverTimestamp()
      };

      let createdDoc;
      // If the data has an ID, use it, otherwise let Firestore generate one
      if (data.id) {
        const docRef = doc(db, this.getCollection(collectionName), data.id);
        await setDoc(docRef, dataWithTimestamp);
        createdDoc = { id: data.id, ...dataWithTimestamp };
      } else {
        const collectionRef = collection(db, this.getCollection(collectionName));
        const docRef = await addDoc(collectionRef, dataWithTimestamp);
        
        // Update the document with its ID
        await updateDoc(docRef, { id: docRef.id });
        createdDoc = { id: docRef.id, ...dataWithTimestamp };
      }

      // Create history entry if needed and if this is a trackable entity type
      if (trackHistory && this.isTrackableEntityType(collectionName)) {
        await this.createHistoryEvent({
          entityId: createdDoc.id,
          entityType: this.getSingularEntityType(collectionName),
          sessionId: sessionId,
          changeType: changeType,
          data: createdDoc,
          editedBy: this.getCurrentUserId()
        });
      }
      
      return createdDoc;
    } catch (error) {
      console.error(`Error creating document in ${collectionName}:`, error);
      throw error;
    }
  }

  // Helper to determine if an entity type should be tracked in history
  isTrackableEntityType(collectionName) {
    const trackableTypes = ['characters', 'npcs', 'locations', 'items', 'sessions'];
    return trackableTypes.includes(collectionName);
  }

  // Helper to get singular entity type from collection name
  getSingularEntityType(collectionName) {
    // Remove trailing 's' to get singular form
    return collectionName.endsWith('s') ? collectionName.slice(0, -1) : collectionName;
  }

  async get(collectionName, id) {
    try {
      const docRef = doc(db, this.getCollection(collectionName), id);
      const docSnap = await getDoc(docRef);

      if (docSnap.exists()) {
        return { id: docSnap.id, ...docSnap.data() };
      } else {
        return null;
      }
    } catch (error) {
      console.error(`Error getting document from ${collectionName}:`, error);
      throw error;
    }
  }

  async update(collectionName, id, data, options = {}) {
    try {
      const { trackHistory = true, sessionId = null, changeType = 'update' } = options;
      
      // Get the current state before updating
      let previousState = null;
      if (trackHistory) {
        previousState = await this.get(collectionName, id);
      }
      
      const docRef = doc(db, this.getCollection(collectionName), id);
      
      // Add updated timestamp
      const updateData = {
        ...data,
        updatedAt: serverTimestamp()
      };
      
      await updateDoc(docRef, updateData);
      const updatedDoc = { id, ...updateData };
      
      // Create history entry if needed and if this is a trackable entity type
      if (trackHistory && this.isTrackableEntityType(collectionName) && previousState) {
        await this.createHistoryEvent({
          entityId: id,
          entityType: this.getSingularEntityType(collectionName),
          sessionId: sessionId,
          changeType: changeType,
          data: updatedDoc,
          previousData: previousState,
          editedBy: this.getCurrentUserId()
        });
      }
      
      return updatedDoc;
    } catch (error) {
      console.error(`Error updating document in ${collectionName}:`, error);
      throw error;
    }
  }

  async delete(collectionName, id, options = {}) {
    try {
      const { trackHistory = true, sessionId = null } = options;
      
      // Get the current state before deleting
      let deletedEntity = null;
      if (trackHistory) {
        deletedEntity = await this.get(collectionName, id);
      }
      
      const docRef = doc(db, this.getCollection(collectionName), id);
      await deleteDoc(docRef);
      
      // Create history entry if needed and if this is a trackable entity type
      if (trackHistory && this.isTrackableEntityType(collectionName) && deletedEntity) {
        await this.createHistoryEvent({
          entityId: id,
          entityType: this.getSingularEntityType(collectionName),
          sessionId: sessionId,
          changeType: 'deletion',
          previousData: deletedEntity,
          editedBy: this.getCurrentUserId()
        });
      }
      
      return true;
    } catch (error) {
      console.error(`Error deleting document from ${collectionName}:`, error);
      throw error;
    }
  }

  // Query operations
  async getAll(collectionName) {
    try {
      const collectionRef = collection(db, this.getCollection(collectionName));
      const snapshot = await getDocs(collectionRef);
      
      return snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
    } catch (error) {
      console.error(`Error getting all documents from ${collectionName}:`, error);
      throw error;
    }
  }

  async query(collectionName, conditions = [], sortBy = null, limitTo = null) {
    try {
      const collectionRef = collection(db, this.getCollection(collectionName));
      
      // Build query constraints
      const queryConstraints = [];
      
      // Add where conditions
      conditions.forEach(condition => {
        queryConstraints.push(where(condition.field, condition.operator, condition.value));
      });
      
      // Add sorting if provided
      if (sortBy) {
        queryConstraints.push(orderBy(sortBy.field, sortBy.direction || 'asc'));
      }
      
      // Add limit if provided
      if (limitTo) {
        queryConstraints.push(limit(limitTo));
      }
      
      // Execute query
      const q = query(collectionRef, ...queryConstraints);
      const snapshot = await getDocs(q);
      
      return snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
    } catch (error) {
      console.error(`Error querying documents from ${collectionName}:`, error);
      throw error;
    }
  }

  // Specific methods for each entity type
  async getAllCharacters() {
    return this.getAll('characters');
  }

  async getAllNpcs() {
    return this.getAll('npcs');
  }

  async getAllLocations() {
    return this.getAll('locations');
  }

  async getAllItems() {
    return this.getAll('items');
  }

  async getAllSessions() {
    const sessions = await this.getAll('sessions');
    
    // Sort sessions by number (newest first)
    return sessions.sort((a, b) => {
      const aNum = parseInt(a.id.split('-')[1]) || -1;
      const bNum = parseInt(b.id.split('-')[1]) || -1;
      return bNum - aNum;
    });
  }

  async getAllHistoryEvents() {
    return this.getAll('historyEvents');
  }
  
  // History event methods
  async createHistoryEvent(eventData) {
    // Make sure it has a timestamp
    const event = {
      ...eventData,
      timestamp: eventData.timestamp || Timestamp.now()
    };
    
    return this.create('historyEvents', event, { trackHistory: false });
  }

  async getSessionEvents(sessionId) {
    return this.query('historyEvents', [
      { field: 'sessionId', operator: '==', value: sessionId }
    ], { field: 'timestamp', direction: 'asc' });
  }

  async getEntityEvents(entityType, entityId) {
    return this.query('historyEvents', [
      { 
        field: 'entityType', 
        operator: '==', 
        value: entityType 
      },
      { 
        field: 'entityId', 
        operator: '==', 
        value: entityId 
      }
    ], { field: 'timestamp', direction: 'asc' });
  }

  // Initialize the database with seed data in historyBasedDataExpanded format
  async seedDatabase(seedData) {
    try {
      // If the data is in historyBasedDataExpanded format
      if (seedData.sessions && seedData.historyEntries) {
        // First import sessions
        if (seedData.sessions && seedData.sessions.length > 0) {
          for (const session of seedData.sessions) {
            await this.create('sessions', session, { trackHistory: false });
          }
          console.log(`Seeded ${seedData.sessions.length} sessions`);
        }
        
        // Then import history entries
        if (seedData.historyEntries && seedData.historyEntries.length > 0) {
          // Sort by timestamp to ensure correct chronological order
          const sortedEntries = [...seedData.historyEntries].sort((a, b) => 
            new Date(a.timestamp) - new Date(b.timestamp)
          );
          
          for (const entry of sortedEntries) {
            // Create the entity in the current state collections first if it's a creation event
            if (entry.changeType === 'creation' && entry.data) {
              const entityType = entry.data.entityType;
              if (entityType) {
                const collectionName = `${entityType}s`;
                // Don't track history for these initial creations since we're importing the history separately
                await this.create(collectionName, entry.data, { trackHistory: false });
              }
            }
            
            // Add the history event
            await this.create('historyEvents', entry, { trackHistory: false });
          }
          console.log(`Seeded ${sortedEntries.length} history entries`);
        }
        
        return true;
      } 
      // Legacy format handling
      else {
        // Process each collection
        const collections = Object.keys(seedData);
        
        for (const collectionName of collections) {
          const items = seedData[collectionName];
          
          // Add each item to the collection
          for (const item of items) {
            await this.create(collectionName, item, { trackHistory: false });
          }
          
          console.log(`Seeded ${items.length} items to ${collectionName}`);
        }
        
        return true;
      }
    } catch (error) {
      console.error('Error seeding database:', error);
      throw error;
    }
  }

  // Export data in historyBasedDataExpanded format
  async exportDataInHistoryFormat() {
    try {
      const sessions = await this.getAllSessions();
      const historyEntries = await this.getAllHistoryEvents();
      
      return {
        sessions,
        historyEntries
      };
    } catch (error) {
      console.error('Error exporting data in history format:', error);
      throw error;
    }
  }

  // Clear all collections
  async clearDatabase() {
    try {
      const collections = [
        'characters',
        'npcs',
        'locations',
        'items',
        'sessions',
        'historyEvents'
      ];
      
      for (const collectionName of collections) {
        const items = await this.getAll(collectionName);
        
        // Delete each item
        for (const item of items) {
          await this.delete(collectionName, item.id);
        }
        
        console.log(`Cleared ${items.length} items from ${collectionName}`);
      }
      
      return true;
    } catch (error) {
      console.error('Error clearing database:', error);
      throw error;
    }
  }
}

// Create singleton instance
const firestoreService = new FirestoreService();

export default firestoreService;
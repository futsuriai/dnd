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

class FirestoreService {
  constructor() {
    // Use the prefix to separate dev and prod data
    this.collectionsPrefix = dbPrefix;
  }

  // Helper to get the prefixed collection name
  getCollection(collectionName) {
    return `${this.collectionsPrefix}${collectionName}`;
  }

  // CRUD operations
  async create(collectionName, data) {
    try {
      // Add created timestamp
      const dataWithTimestamp = {
        ...data,
        createdAt: serverTimestamp(),
        updatedAt: serverTimestamp()
      };

      // If the data has an ID, use it, otherwise let Firestore generate one
      if (data.id) {
        const docRef = doc(db, this.getCollection(collectionName), data.id);
        await setDoc(docRef, dataWithTimestamp);
        return { id: data.id, ...dataWithTimestamp };
      } else {
        const collectionRef = collection(db, this.getCollection(collectionName));
        const docRef = await addDoc(collectionRef, dataWithTimestamp);
        
        // Update the document with its ID
        await updateDoc(docRef, { id: docRef.id });
        
        return { id: docRef.id, ...dataWithTimestamp };
      }
    } catch (error) {
      console.error(`Error creating document in ${collectionName}:`, error);
      throw error;
    }
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

  async update(collectionName, id, data) {
    try {
      const docRef = doc(db, this.getCollection(collectionName), id);
      
      // Add updated timestamp
      const updateData = {
        ...data,
        updatedAt: serverTimestamp()
      };
      
      await updateDoc(docRef, updateData);
      return { id, ...updateData };
    } catch (error) {
      console.error(`Error updating document in ${collectionName}:`, error);
      throw error;
    }
  }

  async delete(collectionName, id) {
    try {
      const docRef = doc(db, this.getCollection(collectionName), id);
      await deleteDoc(docRef);
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
    
    return this.create('historyEvents', event);
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

  // Initialize the database with seed data
  async seedDatabase(seedData) {
    try {
      // Process each collection
      const collections = Object.keys(seedData);
      
      for (const collectionName of collections) {
        const items = seedData[collectionName];
        
        // Add each item to the collection
        for (const item of items) {
          await this.create(collectionName, item);
        }
        
        console.log(`Seeded ${items.length} items to ${collectionName}`);
      }
      
      return true;
    } catch (error) {
      console.error('Error seeding database:', error);
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
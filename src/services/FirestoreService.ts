// FirestoreService.ts
// Handles all Firestore database interactions for the application

import { db, dbPrefix } from '../firebaseConfig';
import {
  collection,
  doc,
  getDoc,
  getDocs,
  setDoc,
  addDoc,
  deleteDoc,
  query,
  where,
  orderBy,
  DocumentReference,
  CollectionReference,
  DocumentData,
  QuerySnapshot,
  DocumentSnapshot
} from 'firebase/firestore';
import { HistoryEntry, Session, Entity } from '../store/worldData';

// Define interfaces for data structures
interface EntityState {
  id: string;
  entityType: string;
  [key: string]: any;
}

interface DatabaseSeedData {
  sessions?: Session[];
  historyEntries?: HistoryEntry[];
  [key: string]: any;
}

interface ExportData {
  sessions: Session[];
  historyEntries: HistoryEntry[];
  [key: string]: any;
}

// Collection names with environment prefixes
const COLLECTIONS = {
  HISTORY_ENTRIES: `${dbPrefix}history_entries`,
  SESSIONS: `${dbPrefix}sessions`,
  ENTITIES: `${dbPrefix}entities`,
  WORLD_HISTORY: `${dbPrefix}world_history`
};

class FirestoreService {
  // Get all history events
  async getAllHistoryEvents(): Promise<HistoryEntry[]> {
    try {
      const historySnap: QuerySnapshot<DocumentData> = await getDocs(collection(db, COLLECTIONS.HISTORY_ENTRIES));
      return historySnap.docs.map(doc => doc.data() as HistoryEntry);
    } catch (error) {
      console.error('Error getting history events:', error);
      throw error;
    }
  }

  // Get all sessions
  async getAllSessions(): Promise<Session[]> {
    try {
      const sessionsSnap: QuerySnapshot<DocumentData> = await getDocs(
        query(collection(db, COLLECTIONS.SESSIONS), orderBy('id', 'desc'))
      );
      return sessionsSnap.docs.map(doc => doc.data() as Session);
    } catch (error) {
      console.error('Error getting sessions:', error);
      throw error;
    }
  }

  // Create a history entry
  async createHistoryEntry(entryData: HistoryEntry): Promise<string> {
    try {
      // Add a document with auto-generated ID
      const entryRef: DocumentReference = await addDoc(collection(db, COLLECTIONS.HISTORY_ENTRIES), entryData);
      console.log('History entry created with ID:', entryRef.id);
      return entryRef.id;
    } catch (error) {
      console.error('Error creating history entry:', error);
      throw error;
    }
  }

  // Create or update an entity
  async createOrUpdateEntity(entityType: string, entityData: EntityState): Promise<string> {
    try {
      // Set the document with the entity ID
      await setDoc(doc(db, COLLECTIONS.ENTITIES, entityData.id), {
        ...entityData,
        entityType,
        lastUpdated: new Date().toISOString()
      });
      return entityData.id;
    } catch (error) {
      console.error('Error creating/updating entity:', error);
      throw error;
    }
  }

  // Get an entity by ID
  async getEntity(entityId: string): Promise<EntityState | null> {
    try {
      const entityDoc: DocumentSnapshot<DocumentData> = await getDoc(doc(db, COLLECTIONS.ENTITIES, entityId));
      if (entityDoc.exists()) {
        return entityDoc.data() as EntityState;
      }
      return null;
    } catch (error) {
      console.error('Error getting entity:', error);
      throw error;
    }
  }

  // Delete an entity
  async deleteEntity(entityId: string): Promise<boolean> {
    try {
      await deleteDoc(doc(db, COLLECTIONS.ENTITIES, entityId));
      return true;
    } catch (error) {
      console.error('Error deleting entity:', error);
      throw error;
    }
  }

  // Create or update a session
  async createOrUpdateSession(sessionData: Session): Promise<string> {
    try {
      await setDoc(doc(db, COLLECTIONS.SESSIONS, sessionData.id), sessionData);
      return sessionData.id;
    } catch (error) {
      console.error('Error creating/updating session:', error);
      throw error;
    }
  }

  // Clear the database (for imports)
  async clearDatabase(): Promise<boolean> {
    try {
      // Get all entries in collections
      const historyQuery: QuerySnapshot<DocumentData> = await getDocs(collection(db, COLLECTIONS.HISTORY_ENTRIES));
      const sessionsQuery: QuerySnapshot<DocumentData> = await getDocs(collection(db, COLLECTIONS.SESSIONS));
      const entitiesQuery: QuerySnapshot<DocumentData> = await getDocs(collection(db, COLLECTIONS.ENTITIES));
      
      // Delete all history entries
      for (const entry of historyQuery.docs) {
        await deleteDoc(entry.ref);
      }
      
      // Delete all sessions
      for (const session of sessionsQuery.docs) {
        await deleteDoc(session.ref);
      }
      
      // Delete all entities
      for (const entity of entitiesQuery.docs) {
        await deleteDoc(entity.ref);
      }
      
      console.log('Database cleared successfully');
      return true;
    } catch (error) {
      console.error('Error clearing database:', error);
      throw error;
    }
  }

  // Seed the database with initial data
  async seedDatabase(data: DatabaseSeedData): Promise<boolean> {
    try {
      // Add sessions
      if (data.sessions && Array.isArray(data.sessions)) {
        for (const session of data.sessions) {
          await this.createOrUpdateSession(session);
        }
      }
      
      // Add history entries
      if (data.historyEntries && Array.isArray(data.historyEntries)) {
        for (const entry of data.historyEntries) {
          await this.createHistoryEntry(entry);
        }
        
        // Also create/update the final state entities
        // Group history entries by entity
        const entriesByEntity: Record<string, HistoryEntry[]> = {};
        
        for (const entry of data.historyEntries) {
          if (!entriesByEntity[entry.entityId]) {
            entriesByEntity[entry.entityId] = [];
          }
          entriesByEntity[entry.entityId].push(entry);
        }
        
        // For each entity, build its current state and save it
        for (const entityId in entriesByEntity) {
          const entries = entriesByEntity[entityId];
          
          // Get the entity type from creation entry
          const creationEntry = entries.find(e => e.changeType === 'creation');
          
          if (creationEntry && creationEntry.data.entityType) {
            // Start with initial state
            let entityState: EntityState = { 
              id: entityId,
              entityType: creationEntry.data.entityType
            };
            
            // Apply all changes in chronological order
            const sortedEntries = entries.sort((a, b) => {
              // Sort by session ID (assuming format session-X where X is a number)
              const aSession = parseInt(a.sessionId.split('-')[1]) || 0;
              const bSession = parseInt(b.sessionId.split('-')[1]) || 0;
              
              if (aSession !== bSession) return aSession - bSession;
              
              // If same session, sort by timestamp
              return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
            });
            
            // Apply each entry to build final state
            for (const entry of sortedEntries) {
              if (entry.changeType === 'creation' || entry.changeType === 'update') {
                // Apply all data fields
                entityState = { ...entityState, ...entry.data };
              }
              // Handle other change types as needed
            }
            
            // Save the final state to the entities collection
            await this.createOrUpdateEntity(entityState.entityType, entityState);
          }
        }
      }
      
      console.log('Database seeded successfully');
      return true;
    } catch (error) {
      console.error('Error seeding database:', error);
      throw error;
    }
  }

  // Export data in history format (for the export feature)
  async exportDataInHistoryFormat(): Promise<ExportData> {
    try {
      // Get all sessions and history entries
      const sessions = await this.getAllSessions();
      const historyEntries = await this.getAllHistoryEvents();
      
      // Return in the same format as expected for import
      return {
        sessions,
        historyEntries
      };
    } catch (error) {
      console.error('Error exporting data:', error);
      throw error;
    }
  }

  // Generic CRUD operations for AdminView.vue
  async create(collectionName: string, data: any): Promise<string> {
    try {
      if (collectionName === 'characters' || 
          collectionName === 'npcs' || 
          collectionName === 'locations' || 
          collectionName === 'items') {
        // For entity collections, create via history entry and final state
        const entityType = collectionName.slice(0, -1); // Remove 's' to get type
        const historyEntry: HistoryEntry = {
          entityId: data.id,
          sessionId: data.sessionId || 'session-admin',
          timestamp: new Date().toISOString(),
          changeType: 'creation',
          data: {
            ...data,
            entityType
          }
        };
        
        // Create history entry
        await this.createHistoryEntry(historyEntry);
        
        // Create final state entity
        await this.createOrUpdateEntity(entityType, data);
        
        return data.id;
      } else {
        // For other collections, just store the document
        const docRef = await addDoc(collection(db, collectionName), data);
        return docRef.id;
      }
    } catch (error) {
      console.error(`Error creating document in ${collectionName}:`, error);
      throw error;
    }
  }

  async update(collectionName: string, id: string, data: any): Promise<string> {
    try {
      if (collectionName === 'characters' || 
          collectionName === 'npcs' || 
          collectionName === 'locations' || 
          collectionName === 'items') {
        // For entity collections, update via history entry and final state
        const entityType = collectionName.slice(0, -1); // Remove 's' to get type
        const historyEntry: HistoryEntry = {
          entityId: id,
          sessionId: data.sessionId || 'session-admin',
          timestamp: new Date().toISOString(),
          changeType: 'update',
          data: {
            ...data,
            entityType
          }
        };
        
        // Create history entry for the update
        await this.createHistoryEntry(historyEntry);
        
        // Update final state entity
        await this.createOrUpdateEntity(entityType, data);
        
        return id;
      } else {
        // For other collections, just update the document
        await setDoc(doc(db, collectionName, id), data, { merge: true });
        return id;
      }
    } catch (error) {
      console.error(`Error updating document in ${collectionName}:`, error);
      throw error;
    }
  }

  async delete(collectionName: string, id: string): Promise<boolean> {
    try {
      if (collectionName === 'characters' || 
          collectionName === 'npcs' || 
          collectionName === 'locations' || 
          collectionName === 'items') {
        // For entity collections, "delete" via history entry
        const entityType = collectionName.slice(0, -1); // Remove 's' to get type
        const historyEntry: HistoryEntry = {
          entityId: id,
          sessionId: 'session-admin',
          timestamp: new Date().toISOString(),
          changeType: 'deletion',
          data: {
            entityType,
            deleted: true
          }
        };
        
        // Create history entry for the deletion
        await this.createHistoryEntry(historyEntry);
        
        // Get current entity to mark as deleted
        const entity = await this.getEntity(id);
        if (entity) {
          // Mark as deleted in final state
          await this.createOrUpdateEntity(entityType, {
            ...entity,
            deleted: true
          });
        }
        
        return true;
      } else {
        // For other collections, actually delete the document
        await deleteDoc(doc(db, collectionName, id));
        return true;
      }
    } catch (error) {
      console.error(`Error deleting document in ${collectionName}:`, error);
      throw error;
    }
  }

  // Methods needed by AdminView.vue
  async getAllCharacters(): Promise<Entity[]> {
    try {
      const entitiesSnap: QuerySnapshot<DocumentData> = await getDocs(
        query(collection(db, COLLECTIONS.ENTITIES), where('entityType', '==', 'character'))
      );
      
      // Filter out deleted entities
      return entitiesSnap.docs
        .map(doc => doc.data() as Entity)
        .filter(entity => !entity.deleted);
    } catch (error) {
      console.error('Error getting characters:', error);
      throw error;
    }
  }

  async getAllNpcs(): Promise<Entity[]> {
    try {
      const entitiesSnap: QuerySnapshot<DocumentData> = await getDocs(
        query(collection(db, COLLECTIONS.ENTITIES), where('entityType', '==', 'npc'))
      );
      
      // Filter out deleted entities
      return entitiesSnap.docs
        .map(doc => doc.data() as Entity)
        .filter(entity => !entity.deleted);
    } catch (error) {
      console.error('Error getting NPCs:', error);
      throw error;
    }
  }

  async getAllLocations(): Promise<Entity[]> {
    try {
      const entitiesSnap: QuerySnapshot<DocumentData> = await getDocs(
        query(collection(db, COLLECTIONS.ENTITIES), where('entityType', '==', 'location'))
      );
      
      // Filter out deleted entities
      return entitiesSnap.docs
        .map(doc => doc.data() as Entity)
        .filter(entity => !entity.deleted);
    } catch (error) {
      console.error('Error getting locations:', error);
      throw error;
    }
  }

  async getAllItems(): Promise<Entity[]> {
    try {
      const entitiesSnap: QuerySnapshot<DocumentData> = await getDocs(
        query(collection(db, COLLECTIONS.ENTITIES), where('entityType', '==', 'item'))
      );
      
      // Filter out deleted entities
      return entitiesSnap.docs
        .map(doc => doc.data() as Entity)
        .filter(entity => !entity.deleted);
    } catch (error) {
      console.error('Error getting items:', error);
      throw error;
    }
  }
}

// Create and export a singleton instance
const firestoreService = new FirestoreService();
export default firestoreService;
// Script to seed the Firestore database with consolidated data

import { historyBasedDataExpanded } from '../store/consolidatedData.js';
import { worldHistory } from '../store/worldHistory.js';
import firestoreService from '../services/FirestoreService.js';
import { serverTimestamp } from 'firebase/firestore';

// Function to seed Firestore with history-based data
export async function seedFirestore() {
  console.log('Starting database seed process...');
  
  try {
    // Upload sessions first
    console.log(`Uploading ${historyBasedDataExpanded.sessions.length} sessions...`);
    for (const session of historyBasedDataExpanded.sessions) {
      // Add serverTimestamp for createdAt, updatedAt
      await firestoreService.create('sessions', {
        ...session,
        createdAt: serverTimestamp(),
        updatedAt: serverTimestamp()
      });
    }
    
    // Upload history entries
    console.log(`Uploading ${historyBasedDataExpanded.historyEntries.length} history entries...`);
    for (const entry of historyBasedDataExpanded.historyEntries) {
      // Generate an ID based on the entry's properties for deduplication
      const entryId = `${entry.entityType}-${entry.entityId}-${entry.sessionId}-${entry.changeType}`;
      
      await firestoreService.create('historyEntries', {
        ...entry,
        id: entryId, // Use deterministic ID
        timestamp: new Date().toISOString(), // Add a timestamp
        createdAt: serverTimestamp(),
        updatedAt: serverTimestamp()
      });
    }
    
    // Upload world history eras
    console.log(`Uploading ${worldHistory.eras.length} world history eras...`);
    for (const era of worldHistory.eras) {
      await firestoreService.create('worldHistory', {
        ...era,
        createdAt: serverTimestamp(),
        updatedAt: serverTimestamp()
      });
    }
    
    console.log('Database seed completed successfully!');
    
    // Return counts of uploaded data
    return {
      sessions: historyBasedDataExpanded.sessions.length,
      historyEntries: historyBasedDataExpanded.historyEntries.length,
      worldHistoryEras: worldHistory.eras.length
    };
  } catch (error) {
    console.error('Error during database seed:', error);
    throw error;
  }
}

// Function to get counts of all events in the data
export function getEventCounts() {
  return {
    sessions: historyBasedDataExpanded.sessions.length,
    historyEntries: historyBasedDataExpanded.historyEntries.length,
    worldHistoryEvents: worldHistory.eras.reduce((total, era) => total + era.events.length, 0),
    total: historyBasedDataExpanded.sessions.length + 
           historyBasedDataExpanded.historyEntries.length +
           worldHistory.eras.reduce((total, era) => total + era.events.length, 0)
  };
}

export default { seedFirestore, getEventCounts };

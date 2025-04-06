// Database seeder - imports data from store files and seeds Firestore

import firestoreService from '../services/FirestoreService';
import { historyEntries } from '../store/history';
import { sessions } from '../store/sessions';
import { worldHistoryEvents } from '../store/worldHistoryEvents';
import { characterEvents } from '../store/characterEvents';
import { itemEvents } from '../store/itemEvents';
import { locationEvents } from '../store/locationEvents';
import { npcEvents } from '../store/npcEvents';

// Function to seed the Firestore database with all history events
export async function seedFirestore() {
  console.log('Starting database seeding process...');
  
  try {
    // 1. Clear existing data first (optional - might want to comment this out in production)
    console.log('Clearing existing data...');
    await firestoreService.clearDatabase();
    
    // 2. Seed session data
    console.log('Seeding sessions...');
    for (const session of sessions) {
      await firestoreService.create('sessions', session);
    }
    
    // 3. Seed all history events
    console.log('Seeding history events...');
    // Use a batch approach to avoid overwhelming Firestore
    const allEvents = [
      ...historyEntries,
      ...worldHistoryEvents,
    ];
    
    // Process in smaller batches
    const batchSize = 20;
    for (let i = 0; i < allEvents.length; i += batchSize) {
      const batch = allEvents.slice(i, i + batchSize);
      await Promise.all(batch.map(event => 
        firestoreService.createHistoryEvent(event)
      ));
      console.log(`Processed ${i + batch.length} of ${allEvents.length} events`);
    }
    
    console.log('Database seeding complete!');
    return true;
  } catch (error) {
    console.error('Error seeding database:', error);
    throw error;
  }
}

// Export other utility functions
export function getEventCounts() {
  return {
    historyEntries: historyEntries.length,
    sessions: sessions.length,
    worldHistoryEvents: worldHistoryEvents.length,
    characterEvents: characterEvents.length,
    itemEvents: itemEvents.length,
    locationEvents: locationEvents.length,
    npcEvents: npcEvents.length,
    total: historyEntries.length + worldHistoryEvents.length
  };
}

export default {
  seedFirestore,
  getEventCounts
};

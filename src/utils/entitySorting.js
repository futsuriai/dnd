// Utility functions for sorting entities by their history

import { currentSession } from '../store/config.js';

/**
 * Get the most recent session number from an entity's history array
 * @param {Object} entity - The entity with a history array
 * @returns {number} - The most recent session number, or 0 if no history
 */
export function getLastSessionFromHistory(entity) {
  if (!entity.history || !Array.isArray(entity.history) || entity.history.length === 0) {
    return 0;
  }
  
  // Get all session numbers from the history array
  const sessionNumbers = entity.history
    .map(historyItem => historyItem.session)
    .filter(session => typeof session === 'number')
    .sort((a, b) => b - a); // Sort descending to get the highest first
  
  return sessionNumbers.length > 0 ? sessionNumbers[0] : 0;
}

/**
 * Check if an entity is new (introduced in the current session) vs updated (appears in multiple sessions)
 * @param {Object} entity - The entity to check
 * @returns {string} - 'new', 'updated', or 'old' based on history
 */
export function getEntityStatus(entity) {
  if (!entity.history || !Array.isArray(entity.history) || entity.history.length === 0) {
    return 'old'; // No history means it's not from current session
  }
  
  const sessionNumbers = entity.history
    .map(historyItem => historyItem.session)
    .filter(session => typeof session === 'number');
    
  const uniqueSessions = [...new Set(sessionNumbers)];
  const hasCurrentSession = uniqueSessions.includes(currentSession);
  
  if (hasCurrentSession && uniqueSessions.length === 1) {
    return 'new'; // Only appears in current session
  } else if (hasCurrentSession && uniqueSessions.length > 1) {
    return 'updated'; // Appears in current session and others
  } else {
    return 'old'; // Doesn't appear in current session
  }
}

/**
 * Sort entities by their most recent session, with most recent first
 * Prioritizes: New (current session only) > Updated (current + others) > Old (not current)
 * Then sorts alphabetically by name within same session/status
 * @param {Array} entities - Array of entities to sort
 * @returns {Array} - Sorted array (new array, doesn't mutate original)
 */
/**
 * Sort entities by their most recent session, with most recent first
 * Prioritizes: New (current session only) > Updated (current + others) > Old (not current)
 * Then sorts alphabetically by name within same session/status
 * @param {Array} entities - Array of entities to sort
 * @returns {Array} - Sorted array (new array, doesn't mutate original)
 */
export function sortEntitiesByLastSession(entities) {
  return [...entities].sort((a, b) => {
    const lastSessionA = getLastSessionFromHistory(a);
    const lastSessionB = getLastSessionFromHistory(b);
    const statusA = getEntityStatus(a);
    const statusB = getEntityStatus(b);
    
    // First, sort by last session descending (most recent first)
    if (lastSessionA !== lastSessionB) {
      return lastSessionB - lastSessionA;
    }
    
    // If same session, prioritize new over updated over old
    const statusPriority = { 'new': 3, 'updated': 2, 'old': 1 };
    const priorityA = statusPriority[statusA] || 1;
    const priorityB = statusPriority[statusB] || 1;
    
    if (priorityA !== priorityB) {
      return priorityB - priorityA; // Higher priority first
    }
    
    // If same session and same status, sort by name alphabetically
    const nameA = (a.name || a.term || '').toLowerCase();
    const nameB = (b.name || b.term || '').toLowerCase();
    return nameA.localeCompare(nameB);
  });
}

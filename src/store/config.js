// Global config for the app
// The current session is inferred from sessions.js: the session before the upcoming one,
// or otherwise the highest numbered completed session.

import { sessions } from './sessions.js';

function parseSessionNumber(id) {
  const m = typeof id === 'string' && id.match(/^session-(\d+)$/i);
  return m ? parseInt(m[1], 10) : null;
}

export function getCurrentSessionNumber() {
  if (!Array.isArray(sessions)) return 0;

  // Prefer the one before the upcoming session, if present
  const upcoming = sessions.find(s => s && s.upcoming);
  const upNum = upcoming ? parseSessionNumber(upcoming.id) : null;
  if (upNum !== null && upNum > 0) return upNum - 1;

  // Fallback: pick the max numeric session among completed
  const completedNums = sessions
    .filter(s => s && s.upcoming === false)
    .map(s => parseSessionNumber(s.id))
    .filter(n => typeof n === 'number');
  return completedNums.length ? Math.max(...completedNums) : 0;
}

export const currentSession = getCurrentSessionNumber();

export function isEntityNew(entity) {
  if (!entity) return false;
  if (!Array.isArray(entity.history)) return false;
  return entity.history.some(h => h && typeof h.session === 'number' && h.session === currentSession);
}

export function getEntityUpdateHistory(entity) {
  if (!entity) return [];
  if (!Array.isArray(entity.history)) return [];
  const sessions = entity.history
    .map(h => (h && typeof h.session === 'number' ? h.session : null))
    .filter(n => typeof n === 'number');
  return Array.from(new Set(sessions)).sort((a, b) => a - b);
}

export default { currentSession, isEntityNew, getCurrentSessionNumber, getEntityUpdateHistory };

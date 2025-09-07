<template>
  <div class="content-section">
    <h1>Notable NPCs</h1>

    <!-- Major NPCs -->
    <div v-if="majorNpcs.length" class="location-section">
      <h2>Key Figures</h2>
      <div class="entity-grid">
        <EntityCard
          v-for="npc in majorNpcs"
          :key="npc.id"
          :entity="npc"
          entityType="npc"
          :showAvatar="!!npc.avatarUrl"
          :avatarUrl="npc.avatarUrl"
          :portraitUrl="npc.portraitUrl"
          @show-full-text="showFullTextModal"
          @show-portrait="showPortraitModal"
        />
      </div>
    </div>

    <!-- Minor NPCs -->
    <div v-if="minorNpcs.length" class="location-section">
      <h2>Others</h2>
      <div class="npc-list">
        <div class="npc-list-item" v-for="npc in minorNpcs" :key="npc.id" :id="npc.id">
          <div class="npc-list-header">
            <strong class="npc-name">{{ npc.name }}</strong>
            <span class="npc-role">{{ npc.role }}</span>
            <button v-if="hasHistory(npc)" class="history-btn" @click="showMinorHistory(npc)" aria-label="View change history" title="View change history">History</button>
          </div>
          <div class="npc-list-body">
            <span class="npc-meta">{{ npc.location }}</span>
            <span v-if="badgeLabel(npc)" :class="badgeLabel(npc) === 'Updated' ? 'badge-updated' : 'badge-new'">{{ badgeLabel(npc) }}</span>
            <span v-else-if="fallbackBadgeLabel(npc)" class="badge-stale">{{ fallbackBadgeLabel(npc) }}</span>
            <p class="npc-desc">{{ npc.description }}</p>
          </div>
        </div>
      </div>
    </div>

    <p v-if="!npcs.length" class="empty-message">No NPCs recorded yet.</p>

    <FullTextModal 
      :visible="isModalVisible" 
      :title="modalTitle" 
      :text="modalText" 
      :imageUrl="modalImageUrl"
      @close="closeModal" 
    />
  </div>
</template>

<script>
import EntityCard from '@/components/EntityCard.vue';
import FullTextModal from '@/components/FullTextModal.vue';
import { npcs } from '@/store/npcs.js';
import { getEntityUpdateHistory, currentSession } from '@/store/config.js';

export default {
  name: 'NpcsView',
  components: {
    EntityCard,
    FullTextModal
  },
  data() {
    return {
      npcs,
      isModalVisible: false,
      modalText: '',
      modalTitle: '',
      modalImageUrl: null
    };
  },
  computed: {
    majorNpcs() {
  // Treat as major if not explicitly marked minor and meets heuristic (fullText or ally/enemy)
  return this.npcs.filter(n => (n.prominence !== 'minor') && (n.fullText || ['ally', 'enemy'].includes((n.status || '').toLowerCase())));
    },
    minorNpcs() {
  // Explicitly include those marked minor, plus anything not in majors
  const majors = new Set(this.majorNpcs.map(m => m.id));
  return this.npcs.filter(n => n.prominence === 'minor' || !majors.has(n.id));
    }
  },
  methods: {
    badgeLabel(entity) {
      const sessions = getEntityUpdateHistory(entity);
      if (sessions.includes(currentSession)) {
        return sessions.length === 1 ? 'New' : 'Updated';
      }
      return null;
    },
    fallbackBadgeLabel(entity) {
      const sessions = getEntityUpdateHistory(entity);
      if (!sessions || !sessions.length) return null;
      if (sessions.includes(currentSession)) return null;
      const last = Math.max(...sessions);
      return `Session ${last}`;
    },
    hasHistory(entity) {
      const sessions = getEntityUpdateHistory(entity);
      const notes = Array.isArray(entity.history) ? entity.history : [];
      return sessions.length > 0 || notes.length > 0;
    },
    showMinorHistory(entity) {
      const sessions = getEntityUpdateHistory(entity);
      const notes = Array.isArray(entity.history) ? entity.history : [];
      if (!sessions.length && !notes.length) return;
      const title = `History: ${entity.name}`;
      const notesBySession = {};
      notes.forEach(n => {
        if (n && typeof n.session === 'number') {
          if (!notesBySession[n.session]) notesBySession[n.session] = [];
          if (n.note) notesBySession[n.session].push(n.note);
        }
      });
      const allSessions = Array.from(new Set([
        ...sessions,
        ...notes.map(n => (typeof n.session === 'number' ? n.session : null)).filter(s => typeof s === 'number')
      ])).sort((a, b) => a - b);
      const lines = allSessions.map(s => {
        const n = notesBySession[s] && notesBySession[s].length ? ` — ${notesBySession[s].join(' • ')}` : (sessions.includes(s) ? ' — Updated' : '');
        return `- Session ${s}${n}`;
      });
      const text = lines.join('\n');
      this.showFullTextModal({ title, text });
    },
    showMinorHistory(entity) {
      const sessions = getEntityUpdateHistory(entity);
      const notes = Array.isArray(entity.history) ? entity.history : [];
      if (!sessions.length && !notes.length) return;
      const title = `History: ${entity.name}`;
      const notesBySession = {};
      notes.forEach(n => {
        if (n && typeof n.session === 'number') {
          if (!notesBySession[n.session]) notesBySession[n.session] = [];
          if (n.note) notesBySession[n.session].push(n.note);
        }
      });
      const allSessions = Array.from(new Set([
        ...sessions,
        ...notes.map(n => (typeof n.session === 'number' ? n.session : null)).filter(s => typeof s === 'number')
      ])).sort((a, b) => a - b);
      const lines = allSessions.map(s => {
        const n = notesBySession[s] && notesBySession[s].length ? ` — ${notesBySession[s].join(' • ')}` : (sessions.includes(s) ? ' — Updated' : '');
        return `- Session ${s}${n}`;
      });
      const text = lines.join('\n');
      this.showFullTextModal({ title, text });
    },
    showFullTextModal(payload) {
      this.modalTitle = payload.title;
      this.modalText = payload.text;
      this.modalImageUrl = null;
      this.isModalVisible = true;
    },
    showPortraitModal(payload) {
      this.modalTitle = payload.title;
      this.modalImageUrl = payload.imageUrl;
      this.modalText = '';
      this.isModalVisible = true;
    },
    closeModal() {
      this.isModalVisible = false;
      this.modalText = '';
      this.modalTitle = '';
      this.modalImageUrl = null;
    }
  }
}
</script>

<style scoped>
.npc-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1rem;
}

.npc-list-item {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 0.75rem 1rem;
}

.npc-list-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.npc-name { color: var(--color-primary); }

.npc-role { color: var(--color-text-muted); font-style: italic; }

.npc-status { font-weight: bold; margin-left: auto; }

.badge-new {
  padding: 0.05rem 0.4rem;
  font-size: 0.7rem;
  font-weight: bold;
  color: #111;
  background: #ffd54f;
  border-radius: 3px;
}
.badge-updated {
  padding: 0.05rem 0.4rem;
  font-size: 0.7rem;
  font-weight: bold;
  color: #111;
  background: #90caf9; /* light blue */
  border-radius: 3px;
}
.badge-stale {
  padding: 0.05rem 0.4rem;
  font-size: 0.7rem;
  font-weight: bold;
  color: #111;
  background: #e0e0e0; /* grey */
  border-radius: 3px;
}

.history-btn {
  margin-left: auto; /* right align for minor NPCs */
  font-size: 0.85rem;
  line-height: 1.1;
  color: var(--color-accent);
  background: transparent;
  border: none;
  cursor: pointer;
  font-weight: 600;
  padding: 0;
}
.history-btn:hover { text-decoration: underline; }

.npc-meta {
  display: inline-block;
  margin-right: 0.5rem;
  color: var(--color-text-muted);
}
.npc-list-body .badge-new,
.npc-list-body .badge-updated { margin-left: 0.25rem; vertical-align: text-top; }

.npc-desc { margin: 0.25rem 0 0; }

.location-section { margin: 1.5rem 0; }

.empty-message {
  text-align: center;
  margin-top: 2rem;
  color: var(--text-muted);
}

/* Right align the History button in minor NPC header */
.npc-list-header .history-btn {
  margin-left: auto;
  font-size: 0.85rem;
  line-height: 1.1;
  color: var(--color-accent);
  background: transparent;
  border: none;
  cursor: pointer;
  font-weight: 600;
  padding: 0;
}
.npc-list-header .history-btn:hover { text-decoration: underline; }
</style>

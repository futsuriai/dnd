<template>
  <div class="content-section">
    <h1>Campaign Sessions</h1>
    <p class="section-intro">Chronicles of our adventures and key events from each session.</p>

    <div v-if="sessions.length" class="sessions-container">
      <div v-for="session in sessions" :key="session.id" class="session-card" :id="session.id">
        <div class="session-header" :class="{ 'upcoming': session.upcoming }">
          <div class="header-top-line">
            <h3 class="session-title">{{ session.title }}:</h3>
            <span class="session-date">{{ session.date }}</span>
          </div>
          <p class="session-subtitle">{{ session.subtitle }}</p>
        </div>
        
        <div class="session-content">
          <div v-if="session.upcoming" class="upcoming-message">
            <p>{{ session.description }}</p>
          </div>
          <div v-else class="session-summary">
            <p>{{ session.description }}</p>
            
            <!-- Session links container -->
            <div class="session-links">
              <!-- Add Read More link if there's a summaryFile property -->
              <a v-if="session.summaryFile" @click.prevent="showFullSummary(session)" href="#" class="read-more-link">
                📜 Read Full Summary
              </a>
              
              <!-- Add Transcript link if there's a transcriptFile property -->
              <a v-if="session.transcriptFile" @click.prevent="showTranscript(session)" href="#" class="transcript-link">
                📝 View Transcript
              </a>
            </div>
            
            <div v-if="session.highlights" class="highlights">
              <h4>Key Moments:</h4>
              <ul>
                <li v-for="(highlight, i) in session.highlights" :key="i">
                  {{ highlight }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
    <p v-else class="empty-message">No sessions recorded yet.</p>
    
    <!-- Add FullTextModal component -->
    <FullTextModal 
      :visible="isModalVisible" 
      :title="modalTitle" 
      :text="modalText" 
      :loading="isLoading"
      :contentClass="modalContentClass"
      @close="closeModal" 
    />
  </div>
</template>

<script>
import { sessions } from '../store/worldData';
import FullTextModal from '@/components/FullTextModal.vue'; // Import the modal
import { loadSessionMarkdown, loadSessionTranscript } from '@/utils/markdownLoader'; // Import our loader utilities

// Import avatar images for transcript display
const avatarModules = import.meta.glob('@/assets/avatars/avatar/*', { eager: true, import: 'default' });

// Map speaker names to avatar file ids
const speakerAvatarMap = {
  'Nyx': 'nyx',
  'Ellara': 'ellara', 
  'Berridin': 'berridin',
  'Ysidor': 'ysidor',
  'Tsi\'Nyra': 'tsinyra',
  'Tsinyra': 'tsinyra',
  'Whitaker "Witty" Whitman VI': 'witty',
  'Witty': 'witty',
  'GM': 'gm' // GM has no avatar but we track it
};

// Get avatar URL for a speaker
function getAvatarUrl(speaker) {
  const id = speakerAvatarMap[speaker];
  if (!id || id === 'gm') return null;
  
  for (const path in avatarModules) {
    if (path.includes(`/avatar/${id}.`)) {
      return avatarModules[path];
    }
  }
  return null;
}

// Get speaker class for color coding
function getSpeakerClass(speaker) {
  const id = speakerAvatarMap[speaker];
  if (id) return `speaker-${id}`;
  return 'speaker-unknown';
}

export default {
  name: 'SessionsView',
  components: {
    FullTextModal // Register the modal
  },
  data() {
    return {
      sessions,
      isModalVisible: false, // State for modal visibility
      modalText: '', // State for modal content
      modalTitle: '', // Add state for modal title
      isLoading: false, // Track loading state
      modalContentClass: '' // CSS class for modal content
    };
  },
  methods: {
    async showFullSummary(session) {
      this.isLoading = true;
      this.modalTitle = `${session.title}: ${session.subtitle}`;
      this.modalContentClass = ''; // Reset class for summaries
      
      try {
        // Load the markdown file dynamically using our utility
        if (session.summaryFile) {
          try {
            const markdownContent = await loadSessionMarkdown(session.summaryFile);
            this.modalText = markdownContent;
          } catch (importError) {
            console.error("Import error:", importError);
            this.modalText = "Unable to load the session summary file.";
          }
        } else {
          this.modalText = "No detailed summary available for this session.";
        }
      } catch (error) {
        this.modalText = "An error occurred while loading the session summary.";
        console.error("Error loading session summary:", error);
      } finally {
        this.isLoading = false;
        this.isModalVisible = true;
      }
    },
    async showTranscript(session) {
      this.isLoading = true;
      this.modalTitle = `${session.title}: ${session.subtitle} — Transcript`;
      this.modalContentClass = 'transcript-content'; // Add class for transcript styling
      
      try {
        if (session.transcriptFile) {
          try {
            const transcriptContent = await loadSessionTranscript(session.transcriptFile);
            // Format transcript for display (it's already timestamped)
            this.modalText = this.formatTranscript(transcriptContent);
          } catch (importError) {
            console.error("Import error:", importError);
            this.modalText = "Unable to load the session transcript file.";
          }
        } else {
          this.modalText = "No transcript available for this session.";
        }
      } catch (error) {
        this.modalText = "An error occurred while loading the transcript.";
        console.error("Error loading transcript:", error);
      } finally {
        this.isLoading = false;
        this.isModalVisible = true;
      }
    },
    formatTranscript(content) {
      // Format the transcript for better readability as HTML with avatars
      // Each line is in format: [HH:MM:SS] Speaker: Text
      
      const lines = content.split('\n').filter(line => line.trim());
      let formattedLines = [];
      let currentSpeaker = null;
      
      for (const line of lines) {
        // Match timestamp and speaker pattern
        const match = line.match(/^\[(\d{2}:\d{2}:\d{2})\]\s*([^:]+):\s*(.*)$/);
        if (match) {
          const [, timestamp, speaker, text] = match;
          const trimmedSpeaker = speaker.trim();
          
          // Add visual separator when speaker changes
          const isNewSpeaker = currentSpeaker !== null && currentSpeaker !== trimmedSpeaker;
          currentSpeaker = trimmedSpeaker;
          
          // Get avatar for this speaker
          const avatarUrl = getAvatarUrl(trimmedSpeaker);
          const avatarHtml = avatarUrl 
            ? `<img src="${avatarUrl}" alt="${trimmedSpeaker}" class="transcript-avatar" />`
            : `<span class="transcript-avatar-placeholder">${trimmedSpeaker.charAt(0)}</span>`;
          
          // Determine speaker class for color coding (character-specific)
          const speakerClass = getSpeakerClass(trimmedSpeaker);
          
          // Build the line HTML - order: timestamp, avatar, speaker, text
          const lineHtml = `<div class="transcript-line${isNewSpeaker ? ' new-speaker' : ''}">
            <span class="transcript-timestamp">${timestamp}</span>
            ${avatarHtml}
            <span class="transcript-speaker ${speakerClass}">${trimmedSpeaker}:</span>
            <span class="transcript-text">${this.escapeHtml(text)}</span>
          </div>`;
          
          formattedLines.push(lineHtml);
        } else if (line.trim()) {
          // Keep non-matching lines as plain text
          formattedLines.push(`<div class="transcript-line transcript-plain">${this.escapeHtml(line)}</div>`);
        }
      }
      
      return formattedLines.join('');
    },
    escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    },
    closeModal() {
      this.isModalVisible = false;
      this.modalText = '';
      this.modalTitle = '';
      this.modalContentClass = '';
    }
  }
};
</script>

<style scoped>
.section-intro {
  text-align: center;
  max-width: 800px;
  margin: 0 auto 2em;
}

.sessions-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.session-card {
  background: var(--gradient-primary);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.session-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border-accent);
}

.header-top-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.session-title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.4rem;
  line-height: 1.2;
  display: inline-block;
}

.session-subtitle {
  margin: 0.25rem 0 0;
  font-size: 0.95rem;
  color: var(--text-muted, #aaa);
  font-style: italic;
  width: 100%;
}

.session-date {
  font-family: var(--font-accent);
  font-size: 0.9em;
  font-weight: bold;
  padding: 0.3em 0.6em;
  border-radius: 4px;
  background-color: rgba(100, 100, 100, 0.2);
  white-space: nowrap;
}

.session-content {
  padding: 1.5rem;
}

.upcoming-message {
  font-style: italic;
  border-left: 3px solid var(--color-primary);
  padding-left: 1rem;
}

.upcoming .session-header {
  background-color: rgba(65, 105, 225, 0.1);
}

.highlights {
  margin-top: 1.5rem;
}

.highlights h4 {
  margin-bottom: 0.5rem;
  color: var(--color-primary);
}

.highlights ul {
  padding-left: 1.5rem;
}

.highlights li {
  margin-bottom: 0.5rem;
}

.empty-message {
  text-align: center;
  margin-top: 2rem;
  color: var(--text-muted);
}

/* Add styling for session links container */
.session-links {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 0.75rem;
}

/* Add styling for read more link */
.read-more-link {
  color: var(--color-highlight);
  cursor: pointer;
  text-decoration: none;
  font-weight: 700; /* Increased font weight for better visibility */
  font-size: 1.05em; /* Slightly increased font size */
  display: inline-block;
}

.read-more-link:hover {
  color: var(--color-accent);
  text-decoration: underline;
}

/* Add styling for transcript link */
.transcript-link {
  color: var(--color-text-muted, #8a9ba8);
  cursor: pointer;
  text-decoration: none;
  font-weight: 700;
  font-size: 1.05em;
  display: inline-block;
  opacity: 0.85;
}

.transcript-link:hover {
  color: var(--color-highlight);
  text-decoration: underline;
  opacity: 1;
}

@media (max-width: 600px) {
  .header-top-line {
    flex-wrap: wrap;
    gap: 0.5rem;
  }
}
</style>

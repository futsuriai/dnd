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
            
            <!-- Add Read More link if there's a summaryFile property -->
            <a v-if="session.summaryFile" @click.prevent="showFullSummary(session)" href="#" class="read-more-link">
              Read Full Summary...
            </a>
            
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
      @close="closeModal" 
    />
  </div>
</template>

<script>
import { sessions } from '../store/worldData';
import FullTextModal from '@/components/FullTextModal.vue'; // Import the modal
import { loadSessionMarkdown } from '@/utils/markdownLoader'; // Import our markdown loader utility

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
      isLoading: false // Track loading state
    };
  },
  methods: {
    async showFullSummary(session) {
      this.isLoading = true;
      this.modalTitle = `${session.title}: ${session.subtitle}`;
      
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
    closeModal() {
      this.isModalVisible = false;
      this.modalText = '';
      this.modalTitle = '';
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

/* Add styling for read more link */
.read-more-link {
  color: var(--color-primary);
  cursor: pointer;
  text-decoration: none;
  font-weight: 500;
  display: inline-block;
  margin-top: 0.5rem;
}

.read-more-link:hover {
  color: var(--color-accent);
  text-decoration: underline;
}

@media (max-width: 600px) {
  .header-top-line {
    flex-wrap: wrap;
    gap: 0.5rem;
  }
}
</style>

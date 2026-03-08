<template>
  <div class="content-section">
    <h1>{{ campaignName }}</h1>
    <div class="campaign-quick-info">
      <div class="info-card">
        <h3 class="fancy-title">Current Location</h3>
        <p>{{ currentLocation }}</p>
      </div>

      <div class="info-card">
        <h3 class="fancy-title">Current Quest</h3>
        <p>{{ currentQuest }}</p>
      </div>

      <div class="info-card">
        <h3 class="fancy-title">Next Session</h3>
        <p>{{ nextSessionDate }} at {{ nextSessionTime }}</p>
      </div>
    </div>

    <div class="session-bridge" v-if="latestSessionSummary || nextSessionNarrative">
      <div class="bridge-card" v-if="latestSessionSummary">
        <h3 class="fancy-title">Where We Left Off</h3>
        <p>{{ latestSessionSummary }}</p>
      </div>
      <div class="bridge-card" v-if="nextSessionNarrative">
        <h3 class="fancy-title">What Comes Next</h3>
        <p>{{ nextSessionNarrative }}</p>
      </div>
    </div>

    <div class="banner-container">
      <img src="../assets/gaslamp.jpg" alt="Campaign Banner" class="campaign-banner">
    </div>
  </div>
</template>

<script>
import { sessions } from '../store/sessions.js';

const sessionMarkdownModules = import.meta.glob('@/assets/sessions/session-*.md', {
  query: '?raw',
  import: 'default'
});

const HOME_RECAP_BY_SESSION = {
  15: 'The attempt to cripple the ducal encampment with poison and sabotage failed under concentrated resistance; the party surrendered to prevent executions and now sits caged inside enemy lines.',
  14: 'The party reached Hyrda, warned Meri and Ardwin about the warforged threat, and committed to a mine-collapse defense plan before ducal reinforcements could arrive.'
};

function extractSessionNumberFromFile(filePath) {
  const match = filePath.match(/session-(\d+)\.md$/i);
  return match ? Number.parseInt(match[1], 10) : null;
}

function stripMarkdown(text) {
  return text
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/!\[[^\]]*\]\([^)]+\)/g, ' ')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/[*_~>#|]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function isNarrativeBlock(block) {
  const trimmed = block.trim();
  if (!trimmed) return false;
  if (/^(#|\||>|---|\*\*|\d+\s*[.\-]|[-*]\s+)/.test(trimmed)) return false;
  return stripMarkdown(trimmed).length > 80;
}

function splitNarrativeBlocks(markdown) {
  return markdown
    .split(/\n\s*\n/)
    .map(block => block.trim())
    .filter(block => block && isNarrativeBlock(block));
}

function firstSentence(text) {
  const clean = stripMarkdown(text);
  const match = clean.match(/[^.!?]+[.!?]/);
  return (match ? match[0] : clean).trim();
}

function toLowerLead(sentence) {
  if (!sentence) return '';
  return sentence.charAt(0).toLowerCase() + sentence.slice(1);
}

function buildLatestSummary(markdown, sessionNumber) {
  if (HOME_RECAP_BY_SESSION[sessionNumber]) {
    return `Session ${sessionNumber}: ${HOME_RECAP_BY_SESSION[sessionNumber]}`;
  }

  const blocks = splitNarrativeBlocks(markdown);
  const opening = blocks[0] ? firstSentence(blocks[0]) : '';
  const ending = blocks.length > 1 ? firstSentence(blocks[blocks.length - 1]) : '';

  if (opening && ending) {
    return `Session ${sessionNumber}: ${opening} By the end, ${toLowerLead(ending)}`;
  }

  if (opening) {
    return `Session ${sessionNumber}: ${opening}`;
  }

  return `Session ${sessionNumber} closed with consequences that are still unfolding.`;
}

export default {
  name: 'HomeView',
  data() {
    const upcomingSession = sessions.find(session => session.upcoming);

    return {
      campaignName: 'A Blinding Light',
      worldName: 'The Hariolar Empire',
      currentLocation: upcomingSession?.location || 'TBD',
      currentQuest: upcomingSession?.subtitle || 'TBD',
      nextSessionDate: upcomingSession?.date || 'TBD',
      nextSessionTime: upcomingSession?.time || 'TBD',
      latestSessionSummary: '',
      nextSessionNarrative: upcomingSession
        ? `${upcomingSession.subtitle}: ${upcomingSession.description}`
        : 'No upcoming session is currently scheduled.'
    };
  },
  async created() {
    await this.loadLatestSessionSummary();
  },
  methods: {
    async loadLatestSessionSummary() {
      const sessionFiles = Object.entries(sessionMarkdownModules)
        .map(([filePath, loadContent]) => ({
          filePath,
          loadContent,
          number: extractSessionNumberFromFile(filePath)
        }))
        .filter(entry => entry.number !== null)
        .sort((a, b) => b.number - a.number);

      if (!sessionFiles.length) {
        this.latestSessionSummary = 'No completed session summary is available yet.';
        return;
      }

      const latest = sessionFiles[0];
      const markdown = await latest.loadContent();
      this.latestSessionSummary = buildLatestSummary(markdown, latest.number);
    }
  }
};
</script>

<style scoped>
h1 {
  text-align: center;
  margin-bottom: 1em;
  font-size: 3em;
}

.intro-text {
  font-size: 1.1em;
  max-width: 800px;
  margin: 0 auto 2em;
  text-align: center;
}

.banner-placeholder {
  display: none;
}

.banner-container {
  width: 100%;
  margin: 2em 0;
  border-radius: 8px;
  overflow: hidden;
}

.campaign-banner {
  width: 100%;
  height: auto;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.campaign-quick-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.info-card {
  background: var(--gradient-primary);
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  text-align: center;
}

.info-card h3 {
  margin-top: 0;
  margin-bottom: 1rem;
}

.session-bridge {
  margin: 1.75rem 0 1.25rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

.bridge-card {
  background: var(--gradient-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1rem 1.25rem;
}

.bridge-card h3 {
  margin: 0 0 0.5rem;
}

.bridge-card p {
  margin: 0;
  line-height: 1.65;
}

@media (max-width: 768px) {
  .campaign-quick-info {
    grid-template-columns: 1fr;
  }

  .session-bridge {
    grid-template-columns: 1fr;
  }
}
</style>

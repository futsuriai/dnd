<template>
  <div class="content-section story-page">
    <h1>The Story So Far</h1>
    <p class="section-intro">
      A back-of-the-book style summary for readers jumping in now.
    </p>
    <p v-if="isLoading" class="loading-message">Gathering the chronicle...</p>
    <p v-else-if="coverageText" class="coverage-text">{{ coverageText }}</p>

    <article v-if="!isLoading && storyParagraphs.length" class="story-manuscript">
      <p v-for="(paragraph, index) in storyParagraphs" :key="index">{{ paragraph }}</p>
    </article>

    <p v-else-if="!isLoading" class="empty-message">
      No session records were found to build the chronicle.
    </p>
  </div>
</template>

<script>
const sessionMarkdownModules = import.meta.glob('@/assets/sessions/session-*.md', {
  query: '?raw',
  import: 'default'
});

const BACK_OF_BOOK_STAGES = [
  {
    minSession: 1,
    text: 'In Bastion City, crystal lamps burn so bright they throw crueler shadows. Progress is preached as holy, order is sold as mercy, and the people least protected by either are the first to disappear.'
  },
  {
    minSession: 1,
    text: 'Into that fracture step five unlikely allies: Ellara, a faithful acolyte-druid torn between doctrine and conscience; Nyx, a shadowed hunter who trusts little and misses less; Berridin, a silver-tongued halfling survivor; Ysidor, a mountain paladin searching for his mentor Meri; and Witty, a volatile noble artificer whose absurdity often hides real nerve.'
  },
  {
    minSession: 2,
    text: 'What begins as a search for one missing mentor becomes a descent through prisons, church offices, and aristocratic courtyards, each door opening onto a larger lie. Every answer points to institutions that call themselves guardians while treating living people as acceptable cost.'
  },
  {
    minSession: 5,
    text: 'Their trail leads to the Duskbreaker Lighthouse, the empire\'s proud monument to light and invention. Behind secured halls and official smiles, the party uncovers a machine economy where warforged ambition, political influence, and sanctioned cruelty feed one another.'
  },
  {
    minSession: 6,
    text: 'When they break into the depths and pull Meri out of an active synthesis line, the worst truth is no longer rumor: Shadowed bodies are being consumed to power the very crystal light used to civilize the city. Rescue buys breath, not safety, and the circle of enemies widens.'
  },
  {
    minSession: 8,
    text: 'From there the campaign hardens into espionage and open defiance: false names at noble balls, fragile alliances, quiet betrayals, and a bounty order that turns Meri into sanctioned prey. The party keeps winning fragments of truth while losing the safety of anonymity.'
  },
  {
    minSession: 12,
    text: 'The road carries them from Bastion to Hyrda, where ducal pressure threatens to become conquest and village defense becomes a race against reinforcements. Strategy shifts from investigation to resistance, and every plan is measured in lives, not glory.'
  },
  {
    minSession: 15,
    text: 'Their latest gamble - poison, sabotage, and a collapsing timetable - fails to break the encampment before the counterstrike lands. Rather than watch captors begin executions, the party yields, stripped of gear and locked in cages inside enemy lines, with the next move likely deciding not only their fate but Hyrda\'s.'
  }
];

function extractSessionNumber(filePath) {
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

function extractFirstNarrativeSentence(markdown) {
  const proseBlock = markdown
    .split(/\n\s*\n/)
    .map(block => block.trim())
    .find(block => {
      if (!block) return false;
      if (/^(#|\||>|---|\*\*|\d+\s*[.\-]|[-*]\s+)/.test(block)) return false;
      return stripMarkdown(block).length > 100;
    });

  if (!proseBlock) return '';

  const sentenceMatch = stripMarkdown(proseBlock).match(/[^.!?]+[.!?]/);
  return sentenceMatch ? sentenceMatch[0].trim() : stripMarkdown(proseBlock);
}

function lowerFirst(text) {
  if (!text) return text;
  return text.charAt(0).toLowerCase() + text.slice(1);
}

function buildStoryParagraphs(latestSessionNumber, latestSessionContent) {
  const staged = BACK_OF_BOOK_STAGES
    .filter(stage => latestSessionNumber >= stage.minSession)
    .map(stage => stage.text);

  if (latestSessionNumber > 15) {
    const continuation = extractFirstNarrativeSentence(latestSessionContent);
    if (continuation) {
      staged.push(`Beyond that turning point, the tale keeps moving: ${lowerFirst(continuation)}`);
    }
  }

  return staged;
}

export default {
  name: 'StorySoFarView',
  data() {
    return {
      storyParagraphs: [],
      coverageText: '',
      isLoading: true
    };
  },
  async created() {
    await this.buildStory();
  },
  methods: {
    async buildStory() {
      const sessions = (
        await Promise.all(
          Object.entries(sessionMarkdownModules).map(async ([filePath, loadContent]) => {
            const number = extractSessionNumber(filePath);
            if (number === null) return null;

            const content = await loadContent();
            return { number, content };
          })
        )
      )
        .filter(Boolean)
        .sort((a, b) => a.number - b.number);

      if (!sessions.length) {
        this.storyParagraphs = [];
        this.coverageText = '';
        this.isLoading = false;
        return;
      }

      const latest = sessions[sessions.length - 1];
      this.storyParagraphs = buildStoryParagraphs(latest.number, latest.content);
      this.coverageText = 'Updated through the latest recorded chapter.';
      this.isLoading = false;
    }
  }
};
</script>

<style scoped>
.story-page {
  max-width: 980px;
  margin: 0 auto;
}

.section-intro {
  text-align: center;
  max-width: 820px;
  margin: 0 auto 1rem;
}

.loading-message {
  text-align: center;
  margin: 0 auto 1.25rem;
  color: var(--text-muted);
  font-style: italic;
}

.coverage-text {
  text-align: center;
  margin: 0 auto 1.5rem;
  color: var(--text-muted);
  font-style: italic;
}

.story-manuscript {
  background: var(--gradient-primary);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 1.25rem 1.5rem;
}

.story-manuscript p {
  margin: 0 0 1rem;
  line-height: 1.72;
  text-wrap: pretty;
}

.story-manuscript p:last-child {
  margin-bottom: 0;
}

.empty-message {
  text-align: center;
  color: var(--text-muted);
  font-style: italic;
}
</style>

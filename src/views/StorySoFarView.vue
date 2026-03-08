<template>
  <div class="content-section story-page">
    <h1>The Story So Far</h1>
    <p class="section-intro">
      A narrator's account stitched from the full session records.
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

const SESSION_CHRONICLE = {
  1: 'Bastion City introduced itself in bright lamps and quiet prejudice, and five strangers met on an alms-day crossing where missing people were already the common language.',
  2: 'Dreams and rumors pulled them west into noble stone and prison ledgers, where they learned Meri had not simply vanished - she had been transferred into Proctor Eduard\'s hands.',
  3: 'When direct questioning failed to settle truth, the road answered with crystal-driven warforged, and the hunt for one mentor became a war against a system.',
  4: 'At the ambush site they found no Meri, only Lighthouse signatures burned into the evidence, and the party turned back toward Bastion with suspicion now pointed at institutions, not bandits.',
  5: 'False names, stolen passes, and improvised infiltration opened doors that official channels never would, revealing that the Duskbreaker Lighthouse hid an industrial program behind civic light.',
  6: 'In the basement labs they found Meri alive inside synthesis machinery; alarms rose, an extraction barely held, and the party escaped with living proof of the atrocity.',
  7: 'Outside the city, Meri named Eduard directly and exposed the motive beneath the doctrine: displace the Shadowed, seize Hyrda, and feed empire through crystal hunger.',
  8: 'Ellara\'s vision of a screaming lamp made the cost impossible to spiritualize away, and a failed return to the Lighthouse burned cover so badly that trust and timing both began to fray.',
  9: 'They adapted by splitting roles in West Bastion\'s courts and archives, trading lies for intelligence on Donnathan Reeves and on the noble machinery protecting him.',
  10: 'Witty entered the campaign as volatile nobility in human form, and with him came the Whitaker masquerade plan to breach the Grand Duke\'s social perimeter.',
  11: 'At the Soiree, dance and espionage became one discipline; they confirmed the Duke-Reeves alliance and learned their borrowed identities were already cracking.',
  12: 'Then the Black Swan contract named Meri for removal, proving politics had turned into paid pursuit, and the party abandoned Bastion plans for the road to Hyrda.',
  13: 'Debt bought distance but not safety: a bounty hunter approached as a mother with a swaddled lie, and the campfire ended in blood and a note pointing to Hyrda.',
  14: 'In Hyrda, Meri and Ardwin stood against a ducal encampment while the party helped shape a mine-collapse defense that could break an invasion before it formed.',
  15: 'The poison gamble struck only part of the camp, the counterattack landed in full, and by Session 15 the party chose surrender over executions, ending disarmed and caged behind enemy lines.'
};

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

function extractTitle(markdown, sessionNumber) {
  const heading = markdown
    .split('\n')
    .map(line => line.trim())
    .find(line => /^#{1,3}\s*session\s+\d+/i.test(line));

  if (!heading) {
    return `Session ${sessionNumber}`;
  }

  return heading.replace(/^#+\s*/, '').replace(/[*_~`]/g, '').trim();
}

function extractFallbackLine(markdown, sessionNumber, title) {
  const proseBlock = markdown
    .split(/\n\s*\n/)
    .map(block => block.trim())
    .find(block => {
      if (!block) return false;
      if (/^(#|\||>|---|\*\*|\d+\s*[.\-]|[-*]\s+)/.test(block)) return false;
      return stripMarkdown(block).length > 100;
    });

  if (!proseBlock) {
    return `${title} (Session ${sessionNumber}) is recorded in the archive, though this chapter still awaits a fully written retelling.`;
  }

  const sentenceMatch = stripMarkdown(proseBlock).match(/[^.!?]+[.!?]/);
  const sentence = sentenceMatch ? sentenceMatch[0].trim() : stripMarkdown(proseBlock);
  return `${title}: ${sentence}`;
}

function groupLinesIntoParagraphs(lines, chunkSize = 3) {
  const grouped = [];
  for (let index = 0; index < lines.length; index += chunkSize) {
    grouped.push(lines.slice(index, index + chunkSize).join(' '));
  }
  return grouped;
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
            const title = extractTitle(content, number);

            return {
              number,
              title,
              content
            };
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

      const chapterLines = sessions.map(session => {
        if (SESSION_CHRONICLE[session.number]) {
          return SESSION_CHRONICLE[session.number];
        }
        return extractFallbackLine(session.content, session.number, session.title);
      });

      this.storyParagraphs = groupLinesIntoParagraphs(chapterLines, 3);
      this.coverageText = `Chronicling ${sessions.length} sessions (Session ${sessions[0].number} through Session ${sessions[sessions.length - 1].number}).`;
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

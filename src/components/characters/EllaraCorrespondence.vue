<template>
  <div class="ellara-correspondence">
    <h2>Correspondence with Lyra</h2>
    <div class="correspondence-container">
      <div v-for="letter in letters" :key="letter.id" class="letter-card">
        <div
          class="letter-header"
          role="button"
          tabindex="0"
          :aria-expanded="isExpanded(letter.id)"
          @click="toggleLetter(letter.id)"
          @keydown.enter.prevent="toggleLetter(letter.id)"
          @keydown.space.prevent="toggleLetter(letter.id)"
        >
          <div class="letter-meta">
            <div class="letter-title-row">
              <h3 class="letter-title">{{ letter.title }}</h3>
              <div class="expand-icon" :class="{ expanded: isExpanded(letter.id) }" aria-hidden="true">
                <span v-if="isExpanded(letter.id)">▼</span>
                <span v-else>▶</span>
              </div>
            </div>
            <div class="letter-direction" :class="letter.from === 'Ellara' ? 'sent' : 'received'">
              {{ letter.from === 'Ellara' ? 'Sent' : 'Received' }}
            </div>
          </div>
          <div class="letter-from-to">
            From: {{ letter.from }} • To: {{ letter.to }}
          </div>
        </div>

        <transition name="fade">
          <div v-if="isExpanded(letter.id)" class="letter-content-wrapper">
            <div
              class="letter-content"
              :class="{
                'ellara-handwriting': letter.from === 'Ellara',
                'lyra-handwriting': letter.from === 'Lyra',
              }"
            >
              <p v-for="(paragraph, pIndex) in letter.content" :key="`${letter.id}-p-${pIndex}`">
                {{ paragraph }}
              </p>
            </div>

            <div class="letter-footer">
              <div
                class="letter-signature"
                :class="{
                  'ellara-signature': letter.from === 'Ellara',
                  'lyra-signature': letter.from === 'Lyra',
                }"
              >
                {{ letter.signature }}
              </div>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { correspondence } from '@/store/correspondence';

const letters = correspondence;
const expandedLetters = ref([]);

function isExpanded(id) {
  return expandedLetters.value.includes(id);
}

function toggleLetter(id) {
  const idx = expandedLetters.value.indexOf(id);
  if (idx === -1) {
    expandedLetters.value.push(id);
  } else {
    expandedLetters.value.splice(idx, 1);
  }
}
</script>

<style scoped>
.ellara-correspondence {
  margin-top: 2rem;
}

h2 {
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0.5rem;
  margin-bottom: 1.5rem;
}

.correspondence-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.letter-card {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.letter-header {
  background-color: rgba(0, 0, 0, 0.22);
  padding: 1.15rem;
  border-bottom: 1px solid var(--border-color);
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.letter-header:hover {
  background-color: rgba(0, 0, 0, 0.34);
}

.letter-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.45rem;
}

.letter-title-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.expand-icon {
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.letter-direction {
  font-size: 0.82rem;
  padding: 0.2rem 0.65rem;
  border-radius: 999px;
  font-weight: 700;
}

.letter-direction.sent {
  background-color: rgba(75, 175, 80, 0.2);
  color: #6fdc74;
}

.letter-direction.received {
  background-color: rgba(91, 176, 207, 0.2);
  color: var(--color-link-hover);
}

.letter-title {
  margin: 0.25rem 0;
  color: var(--accent-color);
  font-size: 1.2rem;
}

.letter-from-to {
  font-size: 0.9rem;
  color: var(--color-text-muted);
}

.letter-content-wrapper {
  overflow: hidden;
}

.letter-content {
  padding: 1.5rem;
  line-height: 1.7;
  background: linear-gradient(
    to bottom,
    rgba(255, 255, 255, 0.01),
    rgba(255, 255, 255, 0.04) 15%,
    rgba(255, 255, 255, 0.04) 85%,
    rgba(255, 255, 255, 0.01)
  );
}

.letter-content p {
  margin-bottom: 1rem;
}

.letter-content p:first-child {
  font-style: italic;
}

.letter-footer {
  padding: 1.1rem 1.5rem;
  border-top: 1px solid var(--border-color);
  text-align: right;
}

.letter-signature {
  font-style: italic;
  color: var(--accent-color);
}

.fade-enter-active,
.fade-leave-active {
  transition: max-height 0.3s ease, opacity 0.3s ease;
  max-height: 2000px;
  overflow: hidden;
}

.fade-enter-from,
.fade-leave-to {
  max-height: 0;
  opacity: 0;
}

/* Loaded handwriting fonts from fonts.css */
.ellara-handwriting {
  font-family: 'Lugrasimo', Georgia, serif;
  font-size: 1.08rem;
  line-height: 1.65;
  letter-spacing: 0.25px;
  font-weight: 500;
}

.lyra-handwriting {
  font-family: 'Kalam', Georgia, serif;
  font-size: 1.08rem;
  letter-spacing: 0.25px;
}

.ellara-signature {
  font-family: 'Lugrasimo', Georgia, 'Times New Roman', serif;
  font-style: italic;
  font-size: 1.35rem;
  font-weight: 600;
  letter-spacing: 0.4px;
}

.lyra-signature {
  font-family: 'Kalam', Georgia, serif;
  font-size: 1.25rem;
  font-weight: 400;
}

@media (max-width: 768px) {
  .letter-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .letter-header {
    padding: 1rem;
  }

  .letter-content {
    padding: 1.2rem;
  }
}
</style>

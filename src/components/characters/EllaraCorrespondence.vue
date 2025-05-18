<template>
  <div class="ellara-correspondence">
    <h2>Correspondence with Lyra</h2>
    <div class="correspondence-container">
      <div v-for="(letter, index) in letters" :key="index" class="letter-card">
        <div class="letter-header" @click="toggleLetter(letter.id)">
          <div class="letter-meta">
            <div class="letter-title-row">
              <h3 class="letter-title">{{ letter.title }}</h3>
              <div class="expand-icon" :class="{ 'expanded': expandedLetters.includes(letter.id) }">
                <span v-if="expandedLetters.includes(letter.id)">▼</span>
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
          <div v-if="expandedLetters.includes(letter.id)" class="letter-content-wrapper">
            <div class="letter-content" :class="{'ellara-handwriting': letter.from === 'Ellara', 'lyra-handwriting': letter.from === 'Lyra'}">
              <p v-for="(paragraph, pIndex) in letter.content" :key="'p'+pIndex">{{ paragraph }}</p>
            </div>
            
            <div class="letter-footer">
              <div class="letter-signature" :class="{'ellara-signature': letter.from === 'Ellara', 'lyra-signature': letter.from === 'Lyra'}">{{ letter.signature }}</div>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script>
import { correspondence } from '@/store/correspondence';
import '@/assets/fonts/fonts.css';

export default {
  name: 'EllaraCorrespondence',
  data() {
    return {
      letters: correspondence,
      expandedLetters: []
    };
  },
  methods: {
    toggleLetter(id) {
      const index = this.expandedLetters.indexOf(id);
      if (index === -1) {
        this.expandedLetters.push(id);
      } else {
        this.expandedLetters.splice(index, 1);
      }
    }
  }
};
</script>

<style scoped>
.ellara-correspondence {
  margin-top: 2rem;
}

h2 {
  border-bottom: 1px solid var(--border-color, #333);
  padding-bottom: 0.5rem;
  margin-bottom: 2rem;
}

.correspondence-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.letter-card {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  border: 1px solid var(--border-color, #333);
  overflow: hidden;
}

.letter-header {
  background-color: rgba(0, 0, 0, 0.2);
  padding: 1.2rem;
  border-bottom: 1px solid var(--border-color, #333);
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.letter-header:hover {
  background-color: rgba(0, 0, 0, 0.3);
}

.letter-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.letter-title-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.expand-icon {
  font-size: 0.8rem;
  transition: transform 0.3s ease;
}

.expand-icon.expanded {
  transform: rotate(0deg);
}

.letter-date {
  font-style: italic;
  color: var(--color-text-muted, #aaa);
}

.letter-direction {
  font-size: 0.85rem;
  padding: 0.2rem 0.6rem;
  border-radius: 10px;
  font-weight: bold;
}

.letter-direction.sent {
  background-color: rgba(75, 175, 80, 0.2);
  color: #4baf50;
}

.letter-direction.received {
  background-color: rgba(33, 150, 243, 0.2);
  color: #2196f3;
}

.letter-title {
  margin: 0.5rem 0;
  color: var(--accent-color, #d4af37);
}

.letter-from-to {
  font-size: 0.9rem;
  color: var(--color-text-muted, #aaa);
}

.letter-content-wrapper {
  overflow: hidden;
}

.letter-content {
  padding: 1.5rem;
  line-height: 1.7;
  background: linear-gradient(to bottom, 
    rgba(255, 255, 255, 0.01), 
    rgba(255, 255, 255, 0.05) 15%, 
    rgba(255, 255, 255, 0.05) 85%,
    rgba(255, 255, 255, 0.01));
}

.letter-content p {
  margin-bottom: 1rem;
}

.letter-content p:first-child {
  font-style: italic;
}

.letter-footer {
  padding: 1.2rem;
  border-top: 1px solid var(--border-color, #333);
  text-align: right;
}

.letter-signature {
  font-style: italic;
  color: var(--accent-color, #d4af37);
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

/* Custom handwriting fonts */
.ellara-handwriting {
  font-family: 'Lugrasimo', cursive;
  font-size: 1.1rem;
  line-height: 1.6;
  letter-spacing: 0.3px;
  font-weight: 500;
}

.lyra-handwriting {
  font-family: 'Kalam', cursive;
  font-size: 1.1rem;
  letter-spacing: 0.3px;
}

.ellara-signature {
  font-family: 'Dancing Script', cursive;
  font-size: 1.6rem;
  font-weight: 600;
}

.lyra-signature {
  font-family: 'Kalam', cursive;
  font-size: 1.3rem;
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

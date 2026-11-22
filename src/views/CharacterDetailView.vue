<template>
  <div class="character-detail-view">
    <div class="content-section">
      <!-- Character submenu for navigation between characters -->
      <CharacterSubmenu :currentCharacterId="activeCharacterId" />

      <div v-if="character">
        <div class="character-header">
          <div
            class="character-avatar"
            :class="{ clickable: Boolean(character.portraitUrl) }"
            @click="showPortrait"
            :title="character.portraitUrl ? `View ${character.name} full portrait` : undefined"
          >
            <img v-if="character.avatarUrl" :src="character.avatarUrl" :alt="character.name" />
            <div v-else class="avatar-placeholder">{{ getInitials(character.name) }}</div>
          </div>

          <div class="character-info">
            <h1>{{ character.name }}</h1>
            <div class="character-subtitle">
              <div>{{ character.race }}</div>
              <div>{{ character.class }} (Level {{ character.level }})</div>
              <div>{{ character.background }}</div>
            </div>

            <div class="character-actions">
              <a
                v-if="character.dndBeyondLink"
                :href="character.dndBeyondLink"
                target="_blank"
                rel="noopener noreferrer"
                class="dndbeyond-link"
              >
                View on D&amp;D Beyond
              </a>
              <button
                v-if="character.portraitUrl"
                type="button"
                @click="showPortrait"
                class="view-portrait-btn"
              >
                View Full Portrait
              </button>
            </div>
          </div>
        </div>

        <div class="character-bio">
          <h2>Biography</h2>
          <p>{{ character.bio }}</p>
        </div>

        <!-- Character-specific correspondence for Ellara -->
        <EllaraCorrespondence v-if="activeCharacterId === 'ellara'" />

        <!-- Optional slot for extensibility -->
        <slot></slot>

        <!-- Character Connections (bidirectional: outgoing + auto-derived backlinks) -->
        <div class="character-connections">
          <h2>Connections</h2>
          <EntityConnections
            :key="activeCharacterId"
            :entity="character"
            entityType="character"
            :entityId="activeCharacterId"
            :defaultExpanded="true"
          />
        </div>
      </div>

      <div v-else class="character-not-found">
        <h2>Character not found</h2>
        <p>Sorry, the character you're looking for doesn't exist.</p>
        <router-link to="/characters" class="back-link">Return to Characters</router-link>
      </div>
    </div>

    <FullTextModal
      :visible="isOpen"
      :title="modalTitle"
      :imageUrl="modalMeta.imageUrl || null"
      @close="closeModal"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { characters } from '@/store/worldData.js';
import CharacterSubmenu from '@/components/CharacterSubmenu.vue';
import EntityConnections from '@/components/EntityConnections.vue';
import FullTextModal from '@/components/FullTextModal.vue';
import EllaraCorrespondence from '@/components/characters/EllaraCorrespondence.vue';
import { useModal } from '@/composables/useModal.js';

const props = defineProps({
  characterId: {
    type: String,
    default: null,
  },
});

const route = useRoute();
const { isOpen, modalTitle, modalMeta, openModal, closeModal } = useModal();

const activeCharacterId = computed(() => props.characterId || String(route.params.id || ''));

const character = computed(() =>
  characters.find((char) => char.id === activeCharacterId.value) || null
);

function getInitials(name) {
  if (!name) return '?';
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0])
    .join('')
    .toUpperCase();
}

function showPortrait() {
  if (character.value && character.value.portraitUrl) {
    openModal(character.value.name, '', { imageUrl: character.value.portraitUrl });
  }
}
</script>

<style scoped>
.character-detail-view {
  padding-bottom: 1rem;
}

.character-header {
  display: flex;
  margin-bottom: 2rem;
  gap: 2rem;
}

.character-avatar {
  width: 180px;
  height: 180px;
  flex-shrink: 0;
  border-radius: 10px;
  overflow: hidden;
  border: 3px solid var(--border-color);
  box-shadow: var(--shadow-lg);
}

.character-avatar.clickable {
  cursor: pointer;
  transition: border-color 0.2s ease, transform 0.2s ease;
}

.character-avatar.clickable:hover {
  border-color: var(--color-primary);
  transform: scale(1.02);
}

.character-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  background-color: var(--color-primary);
  color: var(--color-background);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3rem;
  font-weight: bold;
  font-family: var(--heading-font);
}

.character-info {
  flex: 1;
}

.character-info h1 {
  margin-top: 0;
  margin-bottom: 0.75rem;
  color: var(--accent-color);
}

.character-subtitle {
  color: var(--color-text-muted);
  margin-bottom: 1.25rem;
  font-size: 1.05rem;
}

.character-subtitle > div {
  margin-bottom: 0.2rem;
}

.character-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.9rem;
  margin-top: 1rem;
}

.dndbeyond-link,
.view-portrait-btn {
  padding: 0.65rem 1.3rem;
  border-radius: 6px;
  text-decoration: none;
  display: inline-block;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.dndbeyond-link {
  background-color: #c8101a;
  color: #fff;
}

.dndbeyond-link:hover {
  background-color: #a60d15;
  color: #fff;
  border-bottom: none;
}

.view-portrait-btn {
  background-color: var(--color-primary);
  color: var(--color-background);
}

.view-portrait-btn:hover {
  background-color: var(--color-primary-dark);
  color: var(--color-background);
}

.character-bio {
  margin-bottom: 2rem;
  line-height: 1.75;
  font-size: 1.04rem;
}

.character-bio h2,
.character-connections h2 {
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0.5rem;
  margin-bottom: 1rem;
}

.character-connections {
  margin-top: 2rem;
}

.character-not-found {
  text-align: center;
  padding: 4rem 0;
}

.back-link {
  display: inline-block;
  margin-top: 1rem;
  color: var(--color-link);
  font-weight: bold;
}

@media (max-width: 768px) {
  .character-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 1rem;
  }

  .character-info h1::after {
    left: 50%;
    transform: translateX(-50%);
  }

  .character-avatar {
    width: 150px;
    height: 150px;
  }

  .character-actions {
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .character-actions {
    flex-direction: column;
    gap: 0.7rem;
  }

  .dndbeyond-link,
  .view-portrait-btn {
    width: 100%;
    text-align: center;
    box-sizing: border-box;
  }
}
</style>

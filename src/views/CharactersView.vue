<template>
  <div class="content-section">
    <h1>Player Characters</h1>

    <CharacterSubmenu :currentCharacterId="null" />

    <div class="entity-grid">
      <EntityCard
        v-for="character in characters"
        :key="character.id"
        :entity="character"
        entityType="character"
        :showAvatar="true"
        @show-full-text="handleShowFullText"
        @show-portrait="handleShowPortrait"
      />
    </div>

    <FullTextModal
      :visible="isOpen"
      :title="modalTitle"
      :text="modalContent"
      :imageUrl="modalMeta.imageUrl || null"
      @close="closeModal"
    />
  </div>
</template>

<script setup>
import { characters } from '@/store/worldData.js';
import EntityCard from '@/components/EntityCard.vue';
import FullTextModal from '@/components/FullTextModal.vue';
import CharacterSubmenu from '@/components/CharacterSubmenu.vue';
import { useModal } from '@/composables/useModal.js';

const { isOpen, modalTitle, modalContent, modalMeta, openModal, closeModal } = useModal();

function handleShowFullText(payload) {
  openModal(payload.title, payload.text, { imageUrl: null });
}

function handleShowPortrait(payload) {
  openModal(payload.title, '', { imageUrl: payload.imageUrl });
}
</script>

<style scoped>
/* Uses global layout tokens from src/style.css */
</style>

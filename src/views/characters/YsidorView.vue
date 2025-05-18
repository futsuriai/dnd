<template>
  <CharacterDetailView :characterId="characterId" />
</template>

<script>
import CharacterDetailView from '../CharacterDetailView.vue';

export default {
  name: 'YsidorView',
  components: {
    CharacterDetailView
  },
  computed: {
    characterId() {
      return 'ysidor';
    }
  }
};
</script>

<template>
  <CharacterDetailView :characterId="characterId" />
</template>

<script>
import CharacterDetailView from '../CharacterDetailView.vue';

export default {
  name: 'NyxView',
  components: {
    CharacterDetailView
  },
  computed: {
    characterId() {
      return 'nyx';
    }
  }
};
</script>

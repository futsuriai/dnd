<template>
  <CharacterDetailView :characterId="characterId" />
</template>

<script>
import CharacterDetailView from '../CharacterDetailView.vue';

export default {
  name: 'BerridinView',
  components: {
    CharacterDetailView
  },
  computed: {
    characterId() {
      return 'berridin';
    }
  }
};
</script>

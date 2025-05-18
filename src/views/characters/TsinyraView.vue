<template>
  <CharacterDetailView :characterId="characterId" />
</template>

<script>
import CharacterDetailView from '../CharacterDetailView.vue';

export default {
  name: 'TsinyraView',
  components: {
    CharacterDetailView
  },
  computed: {
    characterId() {
      return 'tsinyra';
    }
  }
};
</script>

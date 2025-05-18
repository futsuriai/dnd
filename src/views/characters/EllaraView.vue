<template>
  <CharacterDetailView :characterId="characterId">
    <EllaraCorrespondence />
  </CharacterDetailView>
</template>

<script>
import CharacterDetailView from '../CharacterDetailView.vue';
import EllaraCorrespondence from '../../components/characters/EllaraCorrespondence.vue';

export default {
  name: 'EllaraView',
  components: {
    CharacterDetailView,
    EllaraCorrespondence
  },
  computed: {
    characterId() {
      return 'ellara';
    }
  }
};
</script>

<template>
  <div class="character-submenu">
    <div class="submenu-toggle" @click="toggleSubMenu" v-if="isMobileView">
      <div class="current-character">
        {{ currentCharacterName }}
      </div>
      <div class="toggle-icon" :class="{ 'open': isOpen }">
        <span></span>
        <span></span>
      </div>
    </div>
    <ul :class="{ 'submenu-open': isOpen || !isMobileView }">
      <li v-for="character in characters" :key="character.id" :class="{ 'active': isActive(character.id) }">
        <router-link :to="'/characters/' + character.id">
          <img v-if="character.avatarUrl" :src="character.avatarUrl" :alt="character.name" class="submenu-avatar" />
          <span v-else class="submenu-initials">{{ getInitials(character.name) }}</span>
          <span class="submenu-name">{{ character.name }}</span>
        </router-link>
      </li>
    </ul>
  </div>
</template>

<script>
import { characters } from '../store/worldData';

export default {
  name: 'CharacterSubmenu',
  props: {
    currentCharacterId: {
      type: String,
      default: null
    }
  },
  data() {
    return {
      characters,
      isOpen: false,
      isMobileView: false
    };
  },
  computed: {
    currentCharacterName() {
      if (!this.currentCharacterId) return 'Character Selection';
      const character = this.characters.find(char => char.id === this.currentCharacterId);
      return character ? character.name : 'Character Selection';
    }
  },
  methods: {
    toggleSubMenu() {
      this.isOpen = !this.isOpen;
    },
    isActive(id) {
      return id === this.currentCharacterId;
    },
    getInitials(name) {
      return name.split(' ').map(word => word[0]).join('');
    },
    checkMobileView() {
      this.isMobileView = window.innerWidth <= 600;
    }
  },
  mounted() {
    this.checkMobileView();
    window.addEventListener('resize', this.checkMobileView);
    
    // If there's a current character ID, open the submenu on desktop
    if (this.currentCharacterId && !this.isMobileView) {
      this.isOpen = true;
    }
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.checkMobileView);
  },
  watch: {
    // Reset menu state when mobile view changes
    isMobileView(newVal) {
      if (!newVal) {
        // On desktop, always show submenu
        this.isOpen = true;
      } else {
        // On mobile, collapse by default
        this.isOpen = false;
      }
    }
  }
};
</script>

<style scoped>
.character-submenu {
  position: relative;
  margin-bottom: 2rem;
  z-index: 90;
}

.submenu-toggle {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.8rem 1rem;
  background-color: var(--bg-secondary, #1e1e1e);
  border: 1px solid var(--border-color, #333);
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.submenu-toggle:hover {
  background-color: var(--bg-hover, #252525);
  border-color: var(--accent-color, #d4af37);
}

.current-character {
  font-weight: bold;
  font-family: var(--heading-font, inherit);
  color: var(--accent-color, #d4af37);
}

.toggle-icon {
  width: 14px;
  height: 14px;
  position: relative;
}

.toggle-icon span {
  display: block;
  position: absolute;
  width: 100%;
  height: 2px;
  background-color: var(--accent-color, #d4af37);
  transition: transform 0.3s;
}

.toggle-icon span:nth-child(1) {
  top: 6px;
  transform: rotate(45deg);
}

.toggle-icon span:nth-child(2) {
  top: 6px;
  transform: rotate(-45deg);
}

.toggle-icon.open span:nth-child(1) {
  transform: rotate(-45deg);
}

.toggle-icon.open span:nth-child(2) {
  transform: rotate(45deg);
}

ul {
  list-style: none;
  padding: 0;
  margin: 0;
  background-color: var(--bg-secondary, #1e1e1e);
  border: 1px solid var(--border-color, #333);
  border-radius: 4px;
  overflow: hidden;
}

@media (max-width: 600px) {
  ul {
    max-height: 0;
    transition: max-height 0.4s ease-in-out;
    overflow: hidden;
    border: none;
  }

  ul.submenu-open {
    max-height: 1000px; /* Large enough to show all content */
    border: 1px solid var(--border-color, #333);
    margin-top: 0.5rem;
  }
}

@media (min-width: 601px) {
  .submenu-toggle {
    display: none;
  }
  
  ul {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
}

li {
  border-bottom: 1px solid var(--border-color, #333);
}

li:last-child {
  border-bottom: none;
}

@media (min-width: 601px) {
  li {
    border: none;
    border-right: 1px solid var(--border-color, #333);
    padding-right: 0.5rem;
  }
  
  li:last-child {
    border-right: none;
    padding-right: 0;
  }
}

li.active a {
  background-color: rgba(212, 175, 55, 0.2);
  color: var(--accent-color, #d4af37);
  border-left: 3px solid var(--accent-color, #d4af37);
  font-weight: 600;
}

li a {
  display: flex;
  align-items: center;
  padding: 0.8rem 1rem;
  text-decoration: none;
  color: var(--color-text, white);
  transition: background-color 0.3s ease;
}

li a:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.submenu-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  margin-right: 10px;
  object-fit: cover;
}

.submenu-initials {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background-color: var(--color-primary, #375a7f);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 10px;
  font-size: 0.8rem;
  font-weight: bold;
  color: var(--color-background, black);
}
</style>

<template>
  <div id="app-container">
    <header>
      <nav>
        <div class="mobile-nav-toggle" @click="toggleMobileMenu" v-show="isMobileView">
          <div class="hamburger-icon">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <span class="current-page">{{ currentRouteName }}</span>
        </div>
        <ul :class="{ 'mobile-open': mobileMenuOpen }">
          <li><router-link to="/">Home</router-link></li>
          <li><router-link to="/sessions">Sessions</router-link></li>
          <li><router-link to="/characters">Characters</router-link></li>
          <!-- <li><router-link to="/npcs">NPCs</router-link></li> -->
          <li><router-link to="/locations">Locations</router-link></li>
          <li><router-link to="/bastion-city">Bastion City</router-link> <!-- Add link to Bastion City --></li>
          <!-- <li><router-link to="/items">Items</router-link></li> -->
          <li><router-link to="/lore">Lore</router-link></li>
          <li><router-link to="/history">History</router-link></li>
        </ul>
      </nav>
    </header>

    <main>
      <router-view />
    </main>

    <footer>
      <p class="text-center muted">Hic sunt dracones</p>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      mobileMenuOpen: false,
      isMobileView: false
    }
  },
  computed: {
    currentRouteName() {
      // Get the current route path
      const route = this.$route.path;
      
      // Default for home route
      if (route === '/') return 'Home';
      
      // Extract main section from path
      const pathParts = route.split('/').filter(Boolean);
      const mainSection = pathParts[0];
      
      // Special handling for character detail pages
      if (mainSection === 'characters' && pathParts.length > 1) {
        // For character detail pages, show "Characters > CharacterName"
        if (this.$route.name && this.$route.name !== 'Character Detail') {
          return 'Characters';
        }
        return 'Characters';
      }
      
      // For other routes, capitalize the first letter
      return mainSection.charAt(0).toUpperCase() + mainSection.slice(1);
    }
  },
  methods: {
    toggleMobileMenu() {
      this.mobileMenuOpen = !this.mobileMenuOpen;
    },
    closeMenu() {
      this.mobileMenuOpen = false;
    },
    checkMobileView() {
      this.isMobileView = window.innerWidth <= 600;
    }
  },
  watch: {
    '$route'() {
      this.closeMenu();
    }
  },
  mounted() {
    this.checkMobileView();
    window.addEventListener('resize', this.checkMobileView);
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.checkMobileView);
  }
}
</script>

<style>
#app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  box-sizing: border-box;
  overflow-x: hidden;
}

main {
  flex-grow: 1;
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 1rem;
  box-sizing: border-box;
}

header {
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  padding-top: 1rem;
  box-sizing: border-box;
}

footer {
  padding: 1.5rem;
  margin-top: 2rem;
  width: 100%;
  max-width: 1100px;
  margin-left: auto;
  margin-right: auto;
  position: relative;
  box-sizing: border-box;
}

footer::before {
  content: "";
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 70%;
  height: 1px;
  background: var(--border-color);
}

nav {
  width: 100%;
  position: relative;
}

nav ul {
  display: flex;
  justify-content: space-between;
  padding: 0;
  list-style: none;
  margin: 0;
}

.mobile-nav-toggle {
  display: none;
  cursor: pointer;
  padding: 10px 0;
  font-weight: bold;
  width: 100%;
  justify-content: flex-start;
  align-items: center;
}

.hamburger-icon {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  width: 24px;
  height: 18px;
  margin-right: 12px;
}

.hamburger-icon span {
  display: block;
  height: 2px;
  width: 100%;
  background-color: var(--accent-color, #d4af37);
  border-radius: 2px;
}

.current-page {
  font-family: var(--heading-font, inherit);
  color: var(--accent-color, #d4af37);
  font-size: 1.2rem;
  line-height: 1;
  display: inline-block;
  vertical-align: middle;
}

@media (max-width: 600px) {
  nav ul {
    flex-direction: column;
    align-items: center;
    background-color: var(--bg-secondary, #1e1e1e);
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    height: 0;
    overflow: hidden;
    transition: height 0.3s ease;
    z-index: 100;
    border-radius: 0 0 5px 5px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    border: 1px solid var(--border-color, #333);
  }
  
  nav ul.mobile-open {
    height: auto;
    padding: 10px 0;
  }
  
  nav li {
    margin-bottom: 12px;
    width: 100%;
    text-align: center;
  }
  
  nav li a {
    display: block;
    padding: 8px 0;
  }
  
  .mobile-nav-toggle {
    display: flex;
    align-items: center;
  }
  
  main, header, footer {
    padding-left: 1rem;
    padding-right: 1rem;
    width: 100%;
    box-sizing: border-box;
  }
  
  nav {
    padding-right: 1rem;
    box-sizing: border-box;
  }
}
</style>
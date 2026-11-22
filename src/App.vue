<template>
  <div id="app-container">
    <header>
      <nav aria-label="Primary navigation">
        <div class="nav-top-bar">
          <button
            type="button"
            class="mobile-nav-toggle"
            @click="toggleMobileMenu"
            :aria-expanded="mobileMenuOpen"
            aria-controls="primary-nav-list"
            v-show="isMobileView"
          >
            <span class="hamburger-icon" :class="{ open: mobileMenuOpen }" aria-hidden="true">
              <span></span>
              <span></span>
              <span></span>
            </span>
            <span class="current-page">{{ currentRouteName }}</span>
          </button>

          <div class="nav-drawer" :class="{ 'mobile-open': mobileMenuOpen }">
            <ul id="primary-nav-list">
              <li>
                <router-link to="/" class="nav-home-link">Home</router-link>
              </li>
              <li>
                <router-link to="/sessions">Sessions</router-link>
              </li>
              <li>
                <router-link to="/characters">Characters</router-link>
              </li>
              <li>
                <router-link to="/npcs">NPCs</router-link>
              </li>
              <li>
                <router-link to="/locations">Locations</router-link>
              </li>
              <li>
                <router-link to="/bastion-city">Bastion City</router-link>
              </li>
              <li>
                <router-link to="/lore">Lore</router-link>
              </li>
              <li>
                <router-link to="/history">History</router-link>
              </li>
            </ul>
          </div>

          <button
            type="button"
            class="global-search-trigger"
            @click="openSearch"
            aria-label="Search campaign wiki (Ctrl+K or Command+K)"
            title="Search campaign (⌘K / Ctrl+K)"
          >
            <span class="search-icon" aria-hidden="true">⌕</span>
            <span class="search-label">Search</span>
            <kbd class="search-kbd">{{ shortcutHint }}</kbd>
          </button>
        </div>
      </nav>
    </header>

    <main>
      <router-view />
    </main>

    <footer>
      <p class="text-center muted">Hic sunt dracones</p>
    </footer>

    <GlobalSearch :visible="isSearchOpen" @close="closeSearch" />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';
import { useRoute } from 'vue-router';
import GlobalSearch from '@/components/GlobalSearch.vue';
import { getCharacter, getSession } from '@/store/worldData.js';

const route = useRoute();

const mobileMenuOpen = ref(false);
const isMobileView = ref(false);
const isSearchOpen = ref(false);

const shortcutHint = computed(() => {
  if (typeof navigator !== 'undefined' && /Mac|iPhone|iPad/i.test(navigator.platform || navigator.userAgent)) {
    return '⌘K';
  }
  return 'Ctrl K';
});

const currentRouteName = computed(() => {
  if (route.path === '/') return 'Home';
  if (route.path === '/bastion-city') return 'Bastion City';
  if (route.path === '/sessions/story-so-far') return 'Story So Far';

  if (route.name === 'Session Detail' && route.params?.id) {
    const session = getSession(String(route.params.id));
    return session ? session.title : 'Session';
  }

  if (route.name === 'Character Detail' && route.params?.id) {
    const character = getCharacter(String(route.params.id));
    return character ? `Characters · ${character.name}` : 'Characters';
  }

  if (route.meta?.title) return String(route.meta.title);
  if (typeof route.name === 'string') return route.name;

  const mainSection = route.path.split('/').filter(Boolean)[0] || 'Home';
  return mainSection
    .split('-')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
});

function toggleMobileMenu() {
  mobileMenuOpen.value = !mobileMenuOpen.value;
}

function closeMenu() {
  mobileMenuOpen.value = false;
}

function checkMobileView() {
  isMobileView.value = window.innerWidth <= 860;
  if (!isMobileView.value) {
    mobileMenuOpen.value = false;
  }
}

function openSearch() {
  isSearchOpen.value = true;
  closeMenu();
}

function closeSearch() {
  isSearchOpen.value = false;
}

function handleGlobalKeydown(event) {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault();
    isSearchOpen.value = !isSearchOpen.value;
  }
}

watch(
  () => route.fullPath,
  () => {
    closeMenu();
  }
);

onMounted(() => {
  checkMobileView();
  window.addEventListener('resize', checkMobileView);
  window.addEventListener('keydown', handleGlobalKeydown);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', checkMobileView);
  window.removeEventListener('keydown', handleGlobalKeydown);
});
</script>

<style>
#app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  box-sizing: border-box;
  overflow-x: hidden;
  overflow-x: clip;
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
  padding: 1rem 1rem 0;
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

.nav-top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  width: 100%;
}

.nav-drawer {
  flex: 1;
}

.global-search-trigger {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.4rem 0.75rem;
  background-color: var(--color-background-soft);
  color: var(--color-text);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 0.88rem;
  font-family: var(--font-main);
  cursor: pointer;
  flex-shrink: 0;
  transition: border-color 0.2s ease, background-color 0.2s ease, color 0.2s ease;
}

.global-search-trigger:hover {
  background-color: var(--bg-hover);
  border-color: var(--color-primary);
  color: var(--color-highlight);
}

.search-icon {
  font-size: 1.05rem;
  line-height: 1;
  color: var(--color-primary);
}

.search-kbd {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
  background: var(--color-background);
  border: 1px solid var(--border-color);
  color: var(--color-text-muted);
}

.mobile-nav-toggle {
  display: none;
  cursor: pointer;
  padding: 0.35rem 0.4rem;
  font-weight: bold;
  background: transparent;
  border: none;
  color: var(--accent-color);
  justify-content: flex-start;
  align-items: center;
  flex: 1;
  min-width: 0;
}

.mobile-nav-toggle:hover {
  background: transparent;
  color: var(--color-highlight);
}

.hamburger-icon {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  width: 22px;
  height: 16px;
  margin-right: 12px;
  flex-shrink: 0;
}

.hamburger-icon span {
  display: block;
  height: 2px;
  width: 100%;
  background-color: var(--accent-color);
  border-radius: 2px;
  transition: transform 0.25s ease, opacity 0.2s ease;
}

.hamburger-icon.open span:nth-child(1) {
  transform: translateY(7px) rotate(45deg);
}

.hamburger-icon.open span:nth-child(2) {
  opacity: 0;
}

.hamburger-icon.open span:nth-child(3) {
  transform: translateY(-7px) rotate(-45deg);
}

.current-page {
  font-family: var(--heading-font);
  color: var(--accent-color);
  font-size: 1.1rem;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 860px) {
  .nav-top-bar {
    flex-wrap: wrap;
    position: relative;
  }

  .mobile-nav-toggle {
    display: flex;
  }

  .search-kbd {
    display: none;
  }

  .nav-drawer {
    order: 3;
    flex-basis: 100%;
    display: grid;
    grid-template-rows: 0fr;
    opacity: 0;
    transition: grid-template-rows 0.28s ease, opacity 0.22s ease, margin-top 0.25s ease;
    margin-top: 0;
  }

  .nav-drawer.mobile-open {
    grid-template-rows: 1fr;
    opacity: 1;
    margin-top: 0.75rem;
  }

  .nav-drawer > ul {
    overflow: hidden;
    flex-direction: column;
    align-items: stretch;
    gap: 0;
    background-color: var(--color-background-soft);
    border-radius: 6px;
    border: 1px solid transparent;
    transition: border-color 0.25s ease;
  }

  .nav-drawer.mobile-open > ul {
    border-color: var(--border-color);
    padding: 0.35rem 0;
  }

  .nav-drawer li {
    width: 100%;
    text-align: center;
    border-bottom: 1px solid rgba(var(--border-color-rgb), 0.35);
  }

  .nav-drawer li:last-child {
    border-bottom: none;
  }

  .nav-drawer li a {
    display: block;
    padding: 0.65rem 1rem;
    border-bottom: none;
  }

  .nav-drawer li a.router-link-exact-active,
  .nav-drawer li a.router-link-active:not(.nav-home-link) {
    background-color: rgba(201, 169, 89, 0.12);
    border-bottom: none;
  }
}

@media (max-width: 480px) {
  .search-label {
    display: none;
  }
}
</style>

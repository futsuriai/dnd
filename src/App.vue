<template>
  <div id="app-container">
    <header>
      <nav>
        <ul>
          <li><router-link to="/">Home</router-link></li>
          <li><router-link to="/characters">Characters</router-link></li>
          <li><router-link to="/npcs">NPCs</router-link></li>
          <li><router-link to="/history">History</router-link></li>
          <li><router-link to="/items">Items</router-link></li>
        </ul>
      </nav>
    </header>

    <main>
      <router-view />
    </main>

    <footer>
      <p class="text-center muted">Campaign Compendium</p>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
#app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

main {
  flex-grow: 1;
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 1rem;
}

header {
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  padding-top: 1rem;
}

footer {
  padding: 1.5rem;
  margin-top: 2rem;
  width: 100%;
  max-width: 1100px;
  margin-left: auto;
  margin-right: auto;
  position: relative;
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
}

nav ul {
  display: flex;
  justify-content: space-between;
  padding: 0;
  list-style: none;
}

@media (max-width: 600px) {
  nav ul {
    flex-direction: column;
    align-items: center;
  }
  
  nav li {
    margin-bottom: 8px;
  }
}
</style>
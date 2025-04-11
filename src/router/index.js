import { createRouter, createWebHashHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';
import CharactersView from '../views/CharactersView.vue';
import NpcView from '../views/NpcView.vue';
import HistoryView from '../views/HistoryView.vue';
import ItemsView from '../views/ItemsView.vue';
import SessionsView from '../views/SessionsView.vue';
import LocationsView from '../views/LocationsView.vue';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: HomeView,
  },
  {
    path: '/characters',
    name: 'Characters',
    component: CharactersView,
  },
  {
    path: '/npcs',
    name: 'NPCs',
    component: NpcView,
  },
  {
    path: '/history',
    name: 'History',
    component: HistoryView,
  },
  {
    path: '/items',
    name: 'Items',
    component: ItemsView,
  },
  {
    path: '/sessions',
    name: 'Sessions',
    component: SessionsView,
  },
  {
    path: '/locations',
    name: 'Locations',
    component: LocationsView,
  },
  // Add other routes here (e.g., Locations, Sessions)
];

// Use the same base path logic as in vite.config.js
const base = '/'

const router = createRouter({
  history: createWebHashHistory(base),
  routes,
  linkActiveClass: 'router-link-active',
  linkExactActiveClass: 'router-link-exact-active'
})

export default router;
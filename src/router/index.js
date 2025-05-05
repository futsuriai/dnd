import { createRouter, createWebHashHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';
import CharactersView from '../views/CharactersView.vue';
// import NpcView from '../views/NpcView.vue';
// import HistoryView from '../views/HistoryView.vue';
// import ItemsView from '../views/ItemsView.vue';
import SessionsView from '../views/SessionsView.vue';
import LocationsView from '../views/LocationsView.vue';
import LoreView from '../views/LoreView.vue'; // Import LoreView
import BastionCityView from '../views/BastionCityView.vue' // Import the new view

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
  // {
  //   path: '/npcs',
  //   name: 'NPCs',
  //   component: NpcView,
  // },
  // {
  //   path: '/history',
  //   name: 'History',
  //   component: HistoryView,
  // },
  // {
  //   path: '/items',
  //   name: 'Items',
  //   component: ItemsView,
  // },
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
  {
    path: '/bastion-city',
    name: 'Bastion City',
    component: BastionCityView // Add route for Bastion City
  },
  {
    path: '/lore', // Add lore route
    name: 'Lore',
    component: LoreView,
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
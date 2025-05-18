import { createRouter, createWebHashHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';
import CharactersView from '../views/CharactersView.vue';
// import NpcView from '../views/NpcView.vue';
import HistoryView from '../views/HistoryView.vue';
// import ItemsView from '../views/ItemsView.vue';
import SessionsView from '../views/SessionsView.vue';
import LocationsView from '../views/LocationsView.vue';
import LoreView from '../views/LoreView.vue'; // Import LoreView
import BastionCityView from '../views/BastionCityView.vue'; // Import the new view

// Import character detail views
import EllaraView from '../views/characters/EllaraView.vue';
import TsinyraView from '../views/characters/TsinyraView.vue';
import BerridinView from '../views/characters/BerridinView.vue';
import NyxView from '../views/characters/NyxView.vue';
import YsidorView from '../views/characters/YsidorView.vue';

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
  {
    path: '/history',
    name: 'History',
    component: HistoryView,
  },
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
  // Character specific routes first (need to come before the generic route)
  {
    path: '/characters/ellara',
    name: 'Ellara',
    component: EllaraView
  },
  {
    path: '/characters/tsinyra',
    name: 'Tsi\'nyra',
    component: TsinyraView
  },
  {
    path: '/characters/berridin',
    name: 'Berridin',
    component: BerridinView
  },
  {
    path: '/characters/nyx',
    name: 'Nyx',
    component: NyxView
  },
  {
    path: '/characters/ysidor',
    name: 'Ysidor',
    component: YsidorView
  },
  // Generic character detail route (must come after specific routes)
  {
    path: '/characters/:id',
    name: 'Character Detail',
    component: CharactersView,
    props: true
  },
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
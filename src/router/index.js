import { createRouter, createWebHashHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';
import CharactersView from '../views/CharactersView.vue';
import NpcView from '../views/NpcView.vue';
import HistoryView from '../views/HistoryView.vue';
import ItemsView from '../views/ItemsView.vue';
import SessionsView from '../views/SessionsView.vue';
import LocationsView from '../views/LocationsView.vue';
import AdminView from '../views/AdminView.vue';
import authService from '../services/AuthService';

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
  {
    path: '/admin',
    name: 'Admin',
    component: AdminView,
    meta: {
      requiresAuth: true
    }
  }
];

// Use the same base path logic as in vite.config.js
const base = process.env.NODE_ENV === 'production' ? '/dnd/' : '/'

const router = createRouter({
  history: createWebHashHistory(base),
  routes,
  linkActiveClass: 'router-link-active',
  linkExactActiveClass: 'router-link-exact-active'
});

// Navigation guard for routes that require authentication
router.beforeEach(async (to, from, next) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  
  if (requiresAuth) {
    // Check if user is authorized editor
    const isAuthorized = authService.isAuthorizedEditor();
    
    if (!isAuthorized) {
      // User will still navigate to the page, but will see the auth UI
      console.log('User not authorized to access admin page');
    }
  }
  
  next();
});

export default router;
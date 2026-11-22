import { defineComponent, h } from 'vue';
import { createRouter, createWebHashHistory, RouterLink } from 'vue-router';
import { getCharacter, getSession } from '../store/worldData.js';

const SITE_TITLE = 'A Blinding Light';

const NotFoundView = defineComponent({
  name: 'NotFoundView',
  setup() {
    return () =>
      h('div', { class: 'content-section text-center' }, [
        h('h1', 'Lost in the Shadow'),
        h(
          'p',
          { class: 'section-intro muted', style: { marginTop: '1.5rem' } },
          'The chronicle page you are looking for does not exist or may have moved.'
        ),
        h(
          'div',
          {
            style: {
              display: 'flex',
              justifyContent: 'center',
              gap: '1rem',
              flexWrap: 'wrap',
              marginTop: '1rem',
            },
          },
          [
            h(RouterLink, { to: '/', class: 'button-link button-primary' }, () => 'Return Home'),
            h(RouterLink, { to: '/sessions', class: 'button-link' }, () => 'Browse Sessions'),
          ]
        ),
      ]);
  },
});

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue'),
    meta: { title: 'Home' },
  },
  {
    path: '/sessions',
    name: 'Sessions',
    component: () => import('../views/SessionsView.vue'),
    meta: { title: 'Sessions' },
  },
  {
    path: '/sessions/story-so-far',
    name: 'Story So Far',
    component: () => import('../views/StorySoFarView.vue'),
    meta: { title: 'The Story So Far' },
  },
  {
    path: '/sessions/:id',
    name: 'Session Detail',
    component: () => import('../views/SessionDetailView.vue'),
    props: true,
    meta: { title: 'Session' },
  },
  {
    path: '/characters',
    name: 'Characters',
    component: () => import('../views/CharactersView.vue'),
    meta: { title: 'Characters' },
  },
  {
    path: '/characters/:id',
    name: 'Character Detail',
    component: () => import('../views/CharacterDetailView.vue'),
    props: (route) => ({ characterId: route.params.id }),
    meta: { title: 'Character' },
  },
  {
    path: '/npcs',
    name: 'NPCs',
    component: () => import('../views/NpcsView.vue'),
    meta: { title: 'Notable NPCs' },
  },
  {
    path: '/locations',
    name: 'Locations',
    component: () => import('../views/LocationsView.vue'),
    meta: { title: 'World Locations' },
  },
  {
    path: '/bastion-city',
    name: 'Bastion City',
    component: () => import('../views/BastionCityView.vue'),
    meta: { title: 'Bastion City' },
  },
  {
    path: '/lore',
    name: 'Lore',
    component: () => import('../views/LoreView.vue'),
    meta: { title: 'World Lore' },
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('../views/HistoryView.vue'),
    meta: { title: 'World History' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFoundView,
    meta: { title: 'Page Not Found' },
  },
];

function applyHashHighlight(el) {
  if (!el) return;
  el.classList.remove('hash-highlight');
  // Force reflow so repeated navigations to the same hash replay the animation
  void el.offsetWidth;
  el.classList.add('hash-highlight');
  window.setTimeout(() => {
    el.classList.remove('hash-highlight');
  }, 2100);
}

function findHashElement(hash) {
  if (!hash) return null;
  const rawId = decodeURIComponent(hash.replace(/^#/, ''));
  if (!rawId) return null;
  return document.getElementById(rawId);
}

function scrollToHashWithRetry(hash, maxAttempts = 20, intervalMs = 80) {
  return new Promise((resolve) => {
    let attempts = 0;
    const tryScroll = () => {
      const target = findHashElement(hash);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        applyHashHighlight(target);
        resolve(false);
        return;
      }
      attempts += 1;
      if (attempts >= maxAttempts) {
        resolve({ top: 0 });
        return;
      }
      window.setTimeout(tryScroll, intervalMs);
    };
    window.requestAnimationFrame(tryScroll);
  });
}

function resolveDocumentTitle(to) {
  if (to.name === 'Home') {
    return SITE_TITLE;
  }
  if (to.name === 'Character Detail' && to.params?.id) {
    const character = getCharacter(String(to.params.id));
    if (character) {
      return `${character.name} · ${SITE_TITLE}`;
    }
  }
  if (to.name === 'Session Detail' && to.params?.id) {
    const session = getSession(String(to.params.id));
    if (session) {
      const label = session.subtitle ? `${session.title}: ${session.subtitle}` : session.title;
      return `${label} · ${SITE_TITLE}`;
    }
  }
  const pageTitle = to.meta?.title || (typeof to.name === 'string' ? to.name : '');
  return pageTitle ? `${pageTitle} · ${SITE_TITLE}` : SITE_TITLE;
}

const base = '/';

const router = createRouter({
  history: createWebHashHistory(base),
  routes,
  linkActiveClass: 'router-link-active',
  linkExactActiveClass: 'router-link-exact-active',
  scrollBehavior(to, _from, savedPosition) {
    if (savedPosition) {
      return savedPosition;
    }
    if (to.hash) {
      return scrollToHashWithRetry(to.hash);
    }
    return { top: 0, behavior: 'smooth' };
  },
});

router.afterEach((to) => {
  if (typeof document !== 'undefined') {
    document.title = resolveDocumentTitle(to);
  }
});

export default router;

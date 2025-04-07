<template>
  <div class="auth-container">
    <div v-if="user" class="user-info">
      <div class="user-avatar">
        <img :src="user.photoURL || undefined" :alt="user.displayName || ''">
      </div>
      <div class="user-details">
        <div class="user-name">{{ user.displayName }}</div>
        <div class="user-email">{{ user.email }}</div>
        <div v-if="isEditor" class="editor-badge">Editor</div>
      </div>
      <button class="auth-button logout" @click="signOut">
        Sign Out
      </button>
    </div>
    <div v-else class="login-container">
      <button class="auth-button google" @click="signInWithGoogle">
        <span class="google-icon">G</span>
        Sign in with Google
      </button>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import authService from '../services/AuthService';
import { User } from 'firebase/auth';

export default defineComponent({
  name: 'AuthComponent',
  data() {
    return {
      user: null as User | null,
      isEditor: false,
      unsubscribe: null as (() => void) | null
    };
  },
  created() {
    // Subscribe to auth state changes
    this.unsubscribe = authService.addAuthListener((user, isEditor) => {
      this.user = user;
      this.isEditor = isEditor;
    });
  },
  beforeUnmount() {
    // Clean up listener on component unmount
    if (this.unsubscribe) {
      this.unsubscribe();
    }
  },
  methods: {
    async signInWithGoogle(): Promise<void> {
      try {
        await authService.signInWithGoogle();
      } catch (error) {
        console.error('Error signing in:', error);
        alert('Failed to sign in. Please try again.');
      }
    },
    async signOut(): Promise<void> {
      try {
        await authService.signOut();
      } catch (error) {
        console.error('Error signing out:', error);
        alert('Failed to sign out. Please try again.');
      }
    }
  }
});
</script>

<style scoped>
.auth-container {
  margin-top: 1rem;
}

.user-info {
  display: flex;
  align-items: center;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  padding: 0.5rem;
  border: 1px solid var(--border-color);
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  margin-right: 0.75rem;
  border: 2px solid var(--color-primary);
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-details {
  flex-grow: 1;
}

.user-name {
  font-weight: bold;
  font-size: 0.9rem;
}

.user-email {
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.editor-badge {
  display: inline-block;
  background: var(--color-primary);
  color: var(--color-background);
  font-size: 0.7rem;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  margin-top: 0.25rem;
}

.auth-button {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s ease;
  border: none;
}

.google {
  background: #fff;
  color: #444;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
}

.google:hover {
  background: #f1f1f1;
}

.google-icon {
  font-weight: bold;
  color: #4285F4;
}

.logout {
  background: rgba(255, 255, 255, 0.1);
  color: var(--color-text);
  border: 1px solid var(--border-color);
  white-space: nowrap;
  margin-left: 0.5rem;
}

.logout:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>
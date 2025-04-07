<template>
  <div class="auth-container">
    <div class="profile-icon" @click="toggleDropdown">
      <img v-if="user && user.photoURL" :src="user.photoURL" :alt="user.displayName || ''" class="user-avatar-img">
      <div v-else class="default-avatar">
        <span>{{ getUserInitials }}</span>
      </div>
      <div v-if="isEditor" class="editor-indicator"></div>
    </div>
    
    <div v-if="dropdownOpen" class="auth-dropdown">
      <div v-if="user" class="dropdown-user-info">
        <div class="dropdown-user-details">
          <div class="dropdown-user-name">{{ user.displayName }}</div>
          <div class="dropdown-user-email">{{ user.email }}</div>
          <div v-if="isEditor" class="dropdown-editor-badge">Editor</div>
        </div>
        <button class="auth-button logout" @click="signOut">
          Sign Out
        </button>
      </div>
      <div v-else class="dropdown-login">
        <button class="auth-button google" @click="signInWithGoogle">
          <span class="google-icon">G</span>
          Sign in with Google
        </button>
      </div>
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
      unsubscribe: null as (() => void) | null,
      dropdownOpen: false
    };
  },
  computed: {
    getUserInitials(): string {
      if (this.user && this.user.displayName) {
        const names = this.user.displayName.split(' ');
        if (names.length > 1) {
          return (names[0][0] + names[names.length - 1][0]).toUpperCase();
        }
        return names[0][0].toUpperCase();
      }
      return '?';
    }
  },
  created() {
    // Subscribe to auth state changes
    this.unsubscribe = authService.addAuthListener((user, isEditor) => {
      this.user = user;
      this.isEditor = isEditor;
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', this.handleOutsideClick);
  },
  beforeUnmount() {
    // Clean up listeners on component unmount
    if (this.unsubscribe) {
      this.unsubscribe();
    }
    document.removeEventListener('click', this.handleOutsideClick);
  },
  methods: {
    toggleDropdown(event: Event): void {
      event.stopPropagation();
      this.dropdownOpen = !this.dropdownOpen;
    },
    handleOutsideClick(event: Event): void {
      const target = event.target as HTMLElement;
      if (!target.closest('.auth-container')) {
        this.dropdownOpen = false;
      }
    },
    async signInWithGoogle(): Promise<void> {
      try {
        await authService.signInWithGoogle();
        this.dropdownOpen = false;
      } catch (error) {
        console.error('Error signing in:', error);
        alert('Failed to sign in. Please try again.');
      }
    },
    async signOut(): Promise<void> {
      try {
        await authService.signOut();
        this.dropdownOpen = false;
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
  position: relative;
  margin-left: auto;
}

.profile-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  cursor: pointer;
  position: relative;
  border: 2px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.2);
}

.user-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.default-avatar {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.15);
  color: var(--color-text);
  font-size: 0.9rem;
  font-weight: bold;
}

.editor-indicator {
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary);
  bottom: 0;
  right: 0;
  border: 1px solid var(--color-background);
}

.auth-dropdown {
  position: absolute;
  top: calc(100% + 5px);
  right: 0;
  min-width: 200px;
  background: var(--bg-secondary, #1e1e1e);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-color);
  z-index: 1000;
  padding: 0.75rem;
  animation: fade-in 0.2s ease;
}

@keyframes fade-in {
  from { opacity: 0; transform: translateY(-5px); }
  to { opacity: 1; transform: translateY(0); }
}

.dropdown-user-info {
  display: flex;
  flex-direction: column;
}

.dropdown-user-details {
  margin-bottom: 0.75rem;
}

.dropdown-user-name {
  font-weight: bold;
  font-size: 0.9rem;
}

.dropdown-user-email {
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.dropdown-editor-badge {
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
  width: 100%;
}

.google {
  background: #fff;
  color: #444;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
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
  text-align: center;
}

.logout:hover {
  background: rgba(255, 255, 255, 0.2);
}

@media (max-width: 600px) {
  .auth-container {
    margin: 0.5rem 0;
    align-self: flex-end;
  }

  .profile-icon {
    margin-left: auto;
  }
}
</style>
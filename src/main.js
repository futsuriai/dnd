import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // Import the router
import './style.css' // Your existing styles

// Import Firebase config
import { auth } from './firebaseConfig'
import { onAuthStateChanged } from 'firebase/auth'

// Create Vue app instance
const app = createApp(App)

// Use the router
app.use(router)

// Wait for Firebase Auth to initialize before mounting the app
let appMounted = false

onAuthStateChanged(auth, () => {
  // Only mount the app once
  if (!appMounted) {
    app.mount('#app')
    appMounted = true
    console.log('Firebase Auth initialized')
  }
})
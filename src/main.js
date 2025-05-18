import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // Import the router
import './style.css' // Your existing styles
import './assets/fonts/fonts.css' // Import custom fonts

const app = createApp(App)

app.use(router) // Tell the Vue app to use the router

app.mount('#app')
import { createApp } from 'vue'
import App from './App.vue'
import store from './store'
import 'leaflet/dist/leaflet.css'

createApp(App).use(store).mount('#app')

import { createApp } from 'vue'
import App from './App.vue'
import store from './store'
import 'leaflet/dist/leaflet.css'
setTimeout(() => {
  document.querySelector('svg.leaflet-attribution-flag').remove()
}, 2000)
createApp(App).use(store).mount('#app')

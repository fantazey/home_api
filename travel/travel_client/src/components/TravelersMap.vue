<template>
  <div style="display: flex;flex-direction: column;justify-content: flex-start">
    <l-map
        v-model="zoom"
        v-model:zoom="zoom"
        :center=center
        :min-zoom="3"
        :max-zoom="18"
        style="height:100vh"
        @update:center="onUpdateCenter"
        @update:zoom="onUpdateZoom"
    >
      <l-tile-layer
          :url="url"
          :attribution="attribution"
      >
      </l-tile-layer>
      <l-marker
          v-for="place of places"
          :key="place.name"
          :lat-lng="[place.latitude, place.longitude]"
      >
        <l-icon :icon-url="getIconUrlForUser(place.user)"
                :icon-size="getIconSizeForUser(place.user)"
                :icon-anchor="getIconAnchorForUser(place.user)"
        ></l-icon>
        <l-tooltip :options="tooltipOptions">{{place.name}} {{place.user}}</l-tooltip>
      </l-marker>
    </l-map>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { LMap, LTileLayer, LMarker, LTooltip, LIcon } from '@vue-leaflet/vue-leaflet'

const icon1 = require('@/assets/marker.svg')
const icon2 = require('@/assets/marker2.svg')

export default {
  name: 'TravelersMap',
  components: {
    LMap,
    LTileLayer,
    LMarker,
    LTooltip,
    LIcon
  },
  data () {
    return {
      zoom: 12,
      center: [59.939, 30.3160],
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
      tooltipOptions: {
        permatent: true
      },
      icons: [
        {
          url: icon1,
          anchor: [15, 0],
          size: [30, 30]
        },
        {
          url: icon2,
          anchor: [15, 30],
          size: [30, 30]
        }
      ],
      iconMap: {}
    }
  },
  computed: {
    ...mapGetters(['places'])
  },
  methods: {
    onUpdateCenter ({ lat, lng }) {
      this.center = [lat, lng]
      console.log(lat, lng)
    },
    onUpdateZoom (zoom) {
      this.zoom = zoom
    },
    getIconUrlForUser (userName) {
      if (userName in this.iconMap) {
        return this.iconMap[userName].url
      }
      this.iconMap[userName] = this.icons.pop()
      return this.iconMap[userName].url
    },
    getIconSizeForUser (userName) {
      if (userName in this.iconMap) {
        return this.iconMap[userName].size
      }
      this.iconMap[userName] = this.icons.pop()
      return this.iconMap[userName].size
    },
    getIconAnchorForUser (userName) {
      if (userName in this.iconMap) {
        return this.iconMap[userName].anchor
      }
      this.iconMap[userName] = this.icons.pop()
      return this.iconMap[userName].anchor
    }
  }
}
</script>

<style scoped>

</style>

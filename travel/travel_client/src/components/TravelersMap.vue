<template>
  <div style="display: flex;flex-direction: column;justify-content: flex-start">
    <l-map
        v-model="zoom"
        v-model:zoom="zoom"
        :center=center
        :min-zoom="3"
        :max-zoom="12"
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
        <!--<l-icon :icon-url="getIconUrlForPlaceType(place.place_type)" :icon-size="[30,30]"></l-icon>-->
        <l-tooltip>{{place.name}} {{place.user}}</l-tooltip>
      </l-marker>
    </l-map>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { LMap, LTileLayer, LMarker, LTooltip /*, LIcon */ } from '@vue-leaflet/vue-leaflet'

export default {
  name: 'TravelersMap',
  components: {
    LMap,
    LTileLayer,
    LMarker,
    LTooltip
    // LIcon
  },
  data () {
    return {
      zoom: 7,
      center: [59.9312, 30.3626],
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
    }
  },
  computed: {
    ...mapGetters(['places'])
  },
  methods: {
    onUpdateCenter ({ lat, lng }) {
      this.center = [lat, lng]
    },
    onUpdateZoom (zoom) {
      this.zoom = zoom
    }
    // getIconUrlForPlaceType (placeType) {
    //   const map = {
    //     'both': bothIcon,
    //     'oksana': oksanaIcon
    //   };
    //   return map[placeType];
    // }
  }
}
</script>

<style scoped>

</style>

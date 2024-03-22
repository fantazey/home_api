<template>
  <travelers-map/>
</template>

<script>
import { mapActions } from 'vuex'
import TravelersMap from './components/TravelersMap'

export default {
  name: 'App',
  components: {
    TravelersMap
  },
  beforeMount () {
    this.loadPlacesData()
  },
  methods: {
    ...mapActions(['loadPlacesData'])
  }
}
</script>

<style>
body {
  margin: 0;
  padding: 0
}
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}
</style>

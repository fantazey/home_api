import { createStore } from 'vuex'

export default createStore({
  state () {
    return {
      places: [],
      postcards: []
    }
  },
  getters: {
    places: state => {
      return state.places
    }
  },
  mutations: {},
  actions: {
    async loadPlacesData ({ state }) {
      const response = await fetch('/travel/api/places.json')
      state.places = await response.json()
    }
  },
  modules: {}
})

<template>
    <div class="map-search">
      <div class="sidebar">
        <div class="search-container">
          <input type="text" placeholder="搜尋位置..." v-model="searchText" class="search-input" />
          <button class="search-btn">搜尋</button>
        </div>
        
        <div class="filters">
          <h3>快速篩選</h3>
          <div class="filter-chips">
            <div class="chip active">全部</div>
            <div class="chip">5000以下</div>
            <div class="chip">5000-8000</div>
            <div class="chip">8000以上</div>
            <div class="chip">限學生</div>
            <div class="chip">可養寵物</div>
          </div>
        </div>
        
        <div class="results">
          <h3>搜尋結果 <span class="result-count">({{ filteredProperties.length }})</span></h3>
          <div class="result-list">
            <div 
              v-for="property in filteredProperties" 
              :key="property.編碼" 
              class="result-item"
              :class="{ active: selectedProperty === property.編碼 }"
              @click="selectProperty(property.編碼)"
            >
              <div class="property-image">
                <div 
                  class="thumbnail"
                  :style="{ backgroundImage: getPropertyImage(property, 0) }"
                >
                  <div class="price-tag">
                    NT$ {{ formatPrice(property.房租) }}/月
                  </div>
                  <button 
                    class="favorite-btn"
                    @click.stop="toggleFavorite(property.編碼)"
                  >
                    <div :class="isFavorite(property.編碼) ? 'heart-filled' : 'heart-outline'"></div>
                  </button>
                  <div class="no-photo-notice" v-if="!hasPhotos(property)">
                    屋主尚未更新照片
                  </div>
                </div>
              </div>
              <div class="item-details">
                <h4>{{ property.標題 }}</h4>
                <div class="price">NT$ {{ formatPrice(property.房租) }}/月</div>
                <div class="location">
                  <i class="location-icon">📍</i> {{ property.地址 }}
                </div>
                <div class="amenities">
                  <span>{{ getRoomTypeInfo(property) }}</span>
                  <span>{{ getSizeInfo(property) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="map-container">
        <div id="google-map" style="height: 100%; width: 100%"></div>
      </div>
    </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useStore } from 'vuex'

export default {
  name: "MapSearch",
  setup() {
    const store = useStore()
    const imageLoadStatus = ref({})
    const searchText = ref('')
    const selectedProperty = ref(null)
    const map = ref(null)
    const markers = ref([])
    const mapLoadError = ref(false)
    const API_KEY = 'YOUR_GOOGLE_MAPS_API_KEY' // 替換成你的 Google Maps API Key

    // 初始化地圖
    const initMap = () => {
      if (!window.google) return
      
      const ncuLocation = { lat: 24.968, lng: 121.1944 }
      map.value = new window.google.maps.Map(document.getElementById('google-map'), {
        center: ncuLocation,
        zoom: 15,
        styles: [],
        mapTypeControl: false,
        fullscreenControl: false,
      })

      // 添加房源標記
      addMarkers()
    }

    // 添加標記
    const addMarkers = () => {
      // 清除現有標記
      markers.value.forEach(marker => marker.setMap(null))
      markers.value = []

      // 為每個房源添加標記
      store.state.accommodations.forEach(property => {
        if (property.latitude && property.longitude) {
          const marker = new window.google.maps.Marker({
            position: {
              lat: parseFloat(property.latitude),
              lng: parseFloat(property.longitude)
            },
            map: map.value,
            title: property.標題
          })

          marker.addListener('click', () => {
            selectedProperty.value = property.編碼
          })

          markers.value.push(marker)
        }
      })
    }

    // 載入 Google Maps
    const loadGoogleMaps = () => {
      if (window.google) {
        initMap()
        return
      }

      const script = document.createElement('script')
      script.src = `https://maps.googleapis.com/maps/api/js?key=${API_KEY}`
      script.async = true
      script.defer = true

      script.onload = () => {
        initMap()
      }

      script.onerror = () => {
        console.error('Google Maps 載入失敗')
        mapLoadError.value = true
        createFallbackMap()
      }

      document.head.appendChild(script)
    }

    // 創建後備地圖
    const createFallbackMap = () => {
      const mapContainer = document.getElementById('google-map')
      if (!mapContainer) return

      mapContainer.innerHTML = `
        <div style="height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; background: #f5f5f5;">
          <p style="color: #666; text-align: center; padding: 20px;">
            地圖暫時無法載入<br>
            請稍後再試
          </p>
        </div>
      `
    }

    // 監聽選中房源變化
    const watchSelectedProperty = (id) => {
      if (mapLoadError.value || !map.value) return

      markers.value.forEach(marker => {
        const position = marker.getPosition()
        const property = store.state.accommodations.find(p =>
          p.latitude === position.lat().toString() &&
          p.longitude === position.lng().toString()
        )

        if (property && property.編碼 === id) {
          marker.setAnimation(window.google.maps.Animation.BOUNCE)
          map.value.panTo(position)
        } else {
          marker.setAnimation(null)
        }
      })
    }

    // 組件掛載時載入地圖
    onMounted(() => {
      loadGoogleMaps()
    })

    return {
      imageLoadStatus,
      searchText,
      selectedProperty,
      mapLoadError,
      filteredProperties: computed(() => store.state.filteredAccommodations),
      watchSelectedProperty
    }
  },

  methods: {
    selectProperty(id) {
      this.selectedProperty = id;
    },
    closeInfoWindow() {
      this.selectedProperty = null;
    },
    getInfoWindowPosition() {
      const marker = this.mapMarkers.find(m => m.id === this.selectedProperty);
      if (!marker) return {};
      
      return {
        left: marker.x + "%",
        top: (marker.y - 15) + "%"
      };
    },
    getPropertyImage(property, index) {
      if (!property) return ""

      if (property.房屋照片 && Array.isArray(property.房屋照片) && property.房屋照片.length > 0) {
        let attempts = 0
        let currentIndex = index
        const maxAttempts = property.房屋照片.length

        const findValidImage = (idx) => {
          if (attempts >= maxAttempts) {
            return `url(https://picsum.photos/id/${((property.編碼 || 0) * 13) % 100 + 1000}/600/400)`
          }

          attempts++

          if (idx >= property.房屋照片.length) {
            idx = 0
          }

          try {
            const imageUrl = property.房屋照片[idx]
            const loadedImg = require("@/" + imageUrl)

            if (loadedImg && typeof loadedImg === "string" && loadedImg.includes("-1.49632716")) {
              return findValidImage(idx + 1)
            }

            return `url(${loadedImg})`
          } catch (e) {
            return findValidImage(idx + 1)
          }
        }

        return findValidImage(currentIndex)
      }

      return 'url(\'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="1" height="1" viewBox="0 0 1 1"%3E%3Crect width="1" height="1" fill="%23f5f5f5"/%3E%3C/svg%3E\')'
    },
    formatPrice(priceString) {
      if (!priceString) return "0"
      try {
        const prices = priceString.toString().match(/\d+/g)
        if (prices && prices.length > 0) {
          return parseInt(prices[0]).toLocaleString()
        }
        return "0"
      } catch (error) {
        return "0"
      }
    },
    hasPhotos(property) {
      return property?.房屋照片?.length > 0
    },
    getRoomTypeInfo(property) {
      if (!property.出租房數) return "類型不詳"
      let types = []
      if (property.出租房數.套房) {
        types.push(`套房${property.出租房數.套房.總數}間`)
      }
      if (property.出租房數.雅房) {
        types.push(`雅房${property.出租房數.雅房.總數}間`)
      }
      return types.join(" / ") || "類型不詳"
    },
    getSizeInfo(property) {
      if (!property.出租房數) return "坪數不詳"
      let sizes = []
      if (property.出租房數.套房?.坪數) {
        sizes.push(property.出租房數.套房.坪數)
      }
      if (property.出租房數.雅房?.坪數) {
        sizes.push(property.出租房數.雅房.坪數)
      }
      return sizes.join(" / ") || "坪數不詳"
    }
  },
  beforeUnmount() {
    if (this.map) {
      this.markers.forEach(marker => marker.setMap(null));
      this.markers = [];
      this.map = null;
    }
  },
  watch: {
    selectedProperty(newValue) {
      this.watchSelectedProperty(newValue);
    }
  }
}
</script>

<style scoped>
.map-search {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: 350px;
  background-color: #fff;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  z-index: 10;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.05);
}

.search-container {
  padding: 20px;
  border-bottom: 1px solid #eee;
  display: flex;
}

.search-input {
  flex: 1;
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 8px 0 0 8px;
  font-size: 1rem;
}

.search-btn {
  padding: 10px 15px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 0 8px 8px 0;
  cursor: pointer;
}

.filters {
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
}

.filters h3 {
  font-size: 1rem;
  margin: 0 0 10px;
  color: #555;
}

.filter-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  padding: 6px 12px;
  background: #f5f7fa;
  border-radius: 20px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.chip.active {
  background: #007bff;
  color: white;
}

.chip:hover:not(.active) {
  background: #e5e9f0;
}

.results {
  padding: 15px 20px;
  flex: 1;
  overflow-y: auto;
}

.results h3 {
  font-size: 1rem;
  margin: 0 0 15px;
  color: #555;
  display: flex;
  align-items: center;
}

.result-count {
  color: #888;
  margin-left: 5px;
  font-weight: normal;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.result-item {
  display: flex;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
}

.result-item:hover,
.result-item.active {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.result-item.active {
  border: 2px solid #007bff;
}

.property-thumbnail {
  width: 100px;
  height: 100px;
  object-fit: cover;
}

.item-details {
  padding: 10px;
  flex: 1;
}

.item-details h4 {
  margin: 0 0 5px;
  font-size: 0.95rem;
  color: #333;
}

.price {
  font-weight: bold;
  color: #007bff;
  margin-bottom: 5px;
  font-size: 0.9rem;
}

.location {
  color: #666;
  font-size: 0.8rem;
  margin-bottom: 5px;
  display: flex;
  align-items: center;
}

.location-icon {
  margin-right: 3px;
  font-size: 0.8rem;
}

.amenities {
  display: flex;
  gap: 8px;
  font-size: 0.75rem;
  color: #777;
}

.map-container {
  flex: 1;
  position: relative;
}

#google-map {
  width: 100%;
  height: 100%;
}

.map-placeholder {
  width: 100%;
  height: 100%;
  position: relative;
}

.map-placeholder img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.map-marker {
  position: absolute;
  transform: translate(-50%, -100%);
  cursor: pointer;
  z-index: 1;
}

.marker-price {
  background: #6B5FF0;
  color: white;
  padding: 8px 12px;
  border-radius: 8px;
  font-weight: bold;
  font-size: 0.9rem;
  white-space: nowrap;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.map-marker.active {
  z-index: 100;
}

.map-marker.active .marker-price {
  background: #9747FF;
}

.info-window {
  position: absolute;
  width: 400px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  transform: translate(-50%, -120%);
  z-index: 101;
  overflow: hidden;
}

.info-window.show-below {
  transform: translate(-50%, 20px);
}

.info-header {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 2;
}

.title-link {
  color: #333;
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  cursor: pointer;
  text-decoration: none;
}

.title-link:hover {
  color: #6B5FF0;
}

.heart-btn {
  background: white;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  transition: transform 0.2s;
}

.heart-btn:hover {
  transform: scale(1.1);
}

.info-body {
  display: flex;
  align-items: stretch;
}

.image-container {
  width: 150px;
  height: 150px;
  flex-shrink: 0;
}

.info-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.info-details {
  flex: 1;
  padding: 15px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-price {
  color: #6B5FF0;
  font-weight: bold;
  font-size: 18px;
}

.info-amenities {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  color: #666;
  font-size: 14px;
}

.close-btn {
  display: none;
}

.info-window::before {
  content: '';
  position: absolute;
  border: 8px solid transparent;
}

.info-window:not(.show-below)::before {
  bottom: -16px;
  left: 50%;
  transform: translateX(-50%);
  border-top-color: white;
}

.info-window.show-below::before {
  top: -16px;
  left: 50%;
  transform: translateX(-50%);
  border-bottom-color: white;
}
</style>
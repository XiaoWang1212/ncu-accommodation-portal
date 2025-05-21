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
          <div class="chip" 
               :class="{ active: currentFilter === 'all' }"
               @click="filterByPrice('all')">全部</div>
          <div class="chip" 
               :class="{ active: currentFilter === '5000以下' }"
               @click="filterByPrice('5000以下')">5000以下</div>
          <div class="chip" 
               :class="{ active: currentFilter === '5000-8000' }"
               @click="filterByPrice('5000-8000')">5000-8000</div>
          <div class="chip" 
               :class="{ active: currentFilter === '8000以上' }"
               @click="filterByPrice('8000以上')">8000以上</div>
        </div>
      </div>
      
      <div class="results">
        <h3>搜尋結果 <span class="result-count">(12)</span></h3>
        <div class="result-list">
          <div class="result-item"
               v-for="property in filteredProperties" 
               :key="property.編碼"
               :class="{ active: selectedProperty === property.編碼 }"
               @click="selectProperty(property.編碼)">
            <div class="item-details">
              <div class="details-left">
                <div class="image-container">
                  <!-- 預設圖片容器 -->
                  <div v-if="!imageLoadStatus[property.編碼]" class="default-image">
                  <i class="no-image-icon">🏠</i>
                  </div>
                  <!-- 實際圖片 -->
                  <img 
                  :src="getImageUrl(property)"
                  :alt="property.標題"
                  class="property-thumbnail"
                  :class="{ 'image-loaded': imageLoadStatus[property.編碼] }"
                  @load="handleImageLoad(property.編碼)"
                  @error="handleImageError($event, property.編碼)"
                  loading="lazy"
                  />
                </div>
              </div>
              <div class="details-right">
                <h4>{{ property.標題 }}</h4>
                <div class="price">{{ property.房租 }}</div>
                <div class="location">
                  <i class="location-icon">📍</i> {{ property.地址 }}
                </div>
                <div class="amenities">
                  <span>{{ property.出租房數.套房.坪數 }}</span>
                  <span v-if="property.出租房數.套房.空房">空房: {{ property.出租房數.套房.空房 }}</span>
                </div>
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
import { ref } from 'vue'
import propertyData from '../data.json'

export default {
  name: "MapSearch",
  setup() {
    const imageLoadStatus = ref({});
    
    const getDefaultImage = () => {
      return 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="1" height="1" viewBox="0 0 1 1"%3E%3Crect width="1" height="1" fill="%23f5f5f5"/%3E%3C/svg%3E';
    };

    const handleImageLoad = (propertyId) => {
      imageLoadStatus.value[propertyId] = true;
    };

    const handleImageError = (event, propertyId) => {
      console.error(`圖片載入失敗: ${propertyId}`);
      imageLoadStatus.value[propertyId] = false;
      event.target.src = getDefaultImage();
    };

    return {
      imageLoadStatus,
      handleImageLoad,
      handleImageError,
      getDefaultImage
    }
  },
  data() {
    return {
      searchText: "",
      selectedProperty: null,
      properties: [], // 改為儲存房屋資料
      markers: [],
      map: null,
      isMapLoaded: false,
      mapLoadError: false,
      selectedMarker: null,
      API_KEY: 'AIzaSyCqNQRo2JFh8XSiBN0pZzemAmUh3WR910s',
      currentFilter: 'all',
      favorites: []
    }
  },

  created() {
    // 在組件創建時載入資料
    this.loadPropertyData()
  },

  computed: {
    selectedPropertyDetails() {
      return this.searchResults.find(p => p.id === this.selectedProperty) || {};
    },
    filteredProperties() {
      let filtered = this.properties;
      
      // 文字搜尋
      if (this.searchText) {
        const searchLower = this.searchText.toLowerCase();
        filtered = filtered.filter(p => 
          p.標題.toLowerCase().includes(searchLower) ||
          p.地址.toLowerCase().includes(searchLower)
        );
      }
      
      // 價格過濾
      if (this.currentFilter !== 'all') {
        filtered = filtered.filter(p => {
          const price = this.extractPrice(p.房租);
          switch(this.currentFilter) {
            case '5000以下':
              return price <= 5000;
            case '5000-8000':
              return price > 5000 && price <= 8000;
            case '8000以上':
              return price > 8000;
            default:
              return true;
          }
        });
      }
      
      return filtered;
    }
  },

  mounted() {
    this.initGoogleMaps();
  },

  methods: {
    loadPropertyData() {
      try {
        // 確保 propertyData 是陣列
        if (Array.isArray(propertyData)) {
          this.properties = propertyData;
        } else {
          console.error('載入的資料格式不正確');
          this.properties = [];
        }
        
        if (this.map && this.isMapLoaded) {
          this.updateMapMarkers();
        }
      } catch (error) {
        console.error('載入物件資料失敗:', error);
        this.properties = [];
      }
    },

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
    initGoogleMaps() {
      // 添加錯誤處理
      const script = document.createElement('script');
      script.src = `https://maps.googleapis.com/maps/api/js?key=${this.API_KEY}&callback=initMap`;
      script.async = true;
      script.defer = true;
      
      // 添加載入錯誤處理
      script.onerror = () => {
        console.error('Google Maps 載入失敗');
        this.mapLoadError = true;
        this.createFallbackMap();
      };

      window.initMap = () => {
        try {
          this.createMap();
          this.isMapLoaded = true;
        } catch (error) {
          console.error('地圖初始化失敗:', error);
          this.mapLoadError = true;
          this.createFallbackMap();
        }
      };

      document.head.appendChild(script);
    },
    createMap() {
      const ncuLocation = { lat: 24.9683, lng: 121.1945 };
      
      if (window.google && window.google.maps) {
        this.map = new window.google.maps.Map(document.getElementById('google-map'), {
          center: ncuLocation,
          zoom: 15,
          styles: [],
          mapTypeControl: false,
          fullscreenControl: false,
        });

        // 確保在地圖載入後再新增標記
        this.isMapLoaded = true;
        this.updateMapMarkers();
      } else {
        this.createFallbackMap();
      }
    },
    createFallbackMap() {
      const mapContainer = document.getElementById('google-map');
      if (!mapContainer) return;

      mapContainer.innerHTML = `
        <div style="height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; background: #f5f5f5;">
          <img src="https://picsum.photos/800/400" alt="Map placeholder" style="max-width: 100%; height: auto; margin-bottom: 20px;"/>
          <p style="color: #666; text-align: center; padding: 20px;">
            地圖暫時無法載入<br>
            請稍後再試
          </p>
        </div>
      `;
      this.mapLoadError = true;
    },
    selectMarker(markerId) {
      this.selectedMarker = this.selectedMarker === markerId ? null : markerId;
    },
    showMarkerInfo(markerId, event) {
      this.selectedMarker = markerId;
      const marker = event.target;
      const markerRect = marker.getBoundingClientRect();
      const windowHeight = window.innerHeight;
      this.shouldShowBelow = markerRect.top < (windowHeight / 2);
    },
    hideMarkerInfo() {
      this.selectedMarker = null;
    },
    toggleFavorite(markerId) {
      if (!this.favorites) this.favorites = [];
      const index = this.favorites.indexOf(markerId);
      if (index === -1) {
        this.favorites.push(markerId);
      } else {
        this.favorites.splice(index, 1);
      }
    },
    isFavorite(markerId) {
      return this.favorites && this.favorites.includes(markerId);
    },
    viewDetails(markerId) {
      console.log(`Viewing details for marker ID: ${markerId}`);
    },
    updateMapMarkers() {
      // 清除現有標記
      if (this.markers && this.markers.length) {
        this.markers.forEach(marker => marker.setMap(null));
        this.markers = [];
      }

      if (!this.map || !this.properties || !window.google) return;

      // 建立地理編碼服務
      const geocoder = new window.google.maps.Geocoder();

      // 為每個物件建立標記
      this.properties.forEach(property => {
        // 使用地址進行地理編碼
        geocoder.geocode({ address: property.地址 }, (results, status) => {
          if (status === 'OK' && results[0]) {
            const position = results[0].geometry.location;
            
            // 在 marker 建立時保存物件 ID
            const marker = new window.google.maps.Marker({
              position: position,
              map: this.map,
              title: property.標題,
              animation: window.google.maps.Animation.DROP
            });
            marker.propertyId = property.編碼; // 新增這行

            // 建立資訊視窗內容
            const content = `
              <div class="info-window-content">
                <h3>${property.標題}</h3>
                <p>${property.房租}</p>
                <p>${property.地址}</p>
                <p>聯絡方式: ${property.聯絡資訊}</p>
              </div>
            `;

            // 建立資訊視窗
            const infoWindow = new window.google.maps.InfoWindow({
              content: content
            });

            // 添加點擊事件
            marker.addListener('click', () => {
              // 關閉其他開啟的資訊視窗
              this.markers.forEach(m => m.infoWindow?.close());
              
              infoWindow.open(this.map, marker);
              this.selectProperty(property.編碼);
              this.map.panTo(position);
            });

            // 儲存標記和資訊視窗的引用
            marker.infoWindow = infoWindow;
            this.markers.push(marker);
          } else {
            console.warn(`地理編碼失敗: ${property.地址}`, status);
          }
        });
      });
    },
    filterByPrice(range) {
      this.currentFilter = range;
      // 不需要額外過濾，因為 filteredProperties computed 屬性會處理
    },
    extractPrice(priceString) {
      // 從價格字串中提取數字
      const matches = priceString.match(/\d+/g);
      if (matches && matches.length > 0) {
        // 如果是範圍價格，取第一個數字
        return parseInt(matches[0]);
      }
      return 0;
    },
    getImageUrl(property) {
      if (!property || !Array.isArray(property.房屋照片) || property.房屋照片.length === 0) {
        return this.getDefaultImage();
      }

      const findValidImage = (index) => {
        if (index >= property.房屋照片.length) {
          return this.getDefaultImage();
        }

        try {
          const imagePath = property.房屋照片[index];
          const image = require(`@/assets/images-data/${imagePath}`);

          // 檢查是否成功載入圖片
          if (image && typeof image === 'string') {
            // 檢查是否為無效的圖片（可以根據實際情況調整條件）
            if (image.includes('-1.49632716') || image.includes('data:image/svg+xml')) {
              return findValidImage(index + 1);
            }
            return image;
          }
          return findValidImage(index + 1);
        } catch (error) {
          console.error(`圖片載入錯誤 (${index}):`, error);
          return findValidImage(index + 1);
        }
      };

      return findValidImage(0);
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
      if (this.mapLoadError || !this.map) return;

      this.markers.forEach(marker => {
        if (marker.propertyId === newValue) {
          marker.setAnimation(window.google.maps.Animation.BOUNCE);
          this.map.panTo(marker.getPosition());
        } else {
          marker.setAnimation(null);
        }
      });
    },
    searchResults: {
      handler(newResults) {
        console.log('Search results updated:', newResults); // 除錯用
        if (this.map && this.isMapLoaded && newResults.length > 0) {
          this.updateMapMarkers();
        }
      },
      deep: true
    }
  }
};
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
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
  height: 120px;
}

.result-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.item-details {
  display: flex;
  height: 100%;
}

.details-left {
  width: 120px;
  flex-shrink: 0;
}

.details-right {
  flex: 1;
  padding: 12px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-width: 0;
}

.image-container {
  position: relative;
  width: 100%;
  height: 100%;
  background-color: #f5f5f5;
  overflow: hidden;
}

.property-thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.property-thumbnail.image-loaded {
  opacity: 1;
}

.default-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
  z-index: 1;
}

.no-image-icon {
  font-size: 2rem;
  color: #ccc;
}

h4 {
  margin: 0 0 4px;
  font-size: 0.9rem;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.price {
  font-weight: bold;
  color: #007bff;
  margin-bottom: 4px;
  font-size: 0.9rem;
}

.location {
  color: #666;
  font-size: 0.8rem;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
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
  background: #6B5FF0; /* 更新為紫色系 */
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
  background: #9747FF; /* 更亮的紫色 */
}

.info-window {
  position: absolute;
  width: 400px; /* 增加寬度 */
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
  width: 150px; /* 固定寬度 */
  height: 150px; /* 固定高度，保持正方形 */
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
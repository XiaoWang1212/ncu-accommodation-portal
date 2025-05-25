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
                <div class="property-thumbnail"
                :style="{ backgroundImage: getPropertyImage(property, 0) }">
                </div>
                <!-- 加入遮罩防止圖片超出範圍 -->
                <div style="position:absolute;inset:0;pointer-events:none;border-radius:8px;box-shadow:0 0 0 1px #f5f5f5;"></div>
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

    <!-- 詳細資訊視窗 -->
    <div v-if="selectedProperty" class="property-detail-modal">
      <div class="modal-content">
        <span class="close" @click="closePropertyDetail">&times;</span>
        
        <div class="slideshow-container">
          <div class="mySlides fade" v-for="(image, index) in selectedProperty.房屋照片" :key="index">
            <div class="numbertext">{{ index + 1 }} / {{ selectedProperty.房屋照片.length }}</div>
            <div class="property-image" :style="{ backgroundImage: 'url(' + image + ')' }"></div>
          </div>
          
          <a class="prev" @click="plusSlides(-1)">&#10094;</a>
          <a class="next" @click="plusSlides(1)">&#10095;</a>
        </div>
        
        <div class="property-details">
          <h2>{{ selectedProperty.標題 }}</h2>
          <div class="price">{{ selectedProperty.房租 }}</div>
          <div class="location">
            <i class="location-icon">📍</i> {{ selectedProperty.地址 }}
          </div>
          <div class="amenities">
            <span>{{ selectedProperty.出租房數.套房.坪數 }}</span>
            <span v-if="selectedProperty.出租房數.套房.空房">空房: {{ selectedProperty.出租房數.套房.空房 }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import '@/assets/map-info-window.css';
import { ref, onMounted, computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router';
import propertyData from '../data.json'

export default {
  name: "MapSearch",
  setup() {
    const store = useStore()
    const router = useRouter();
    const imageLoadStatus = ref({})
    
    // 修改圖片處理邏輯
    const getPropertyImage = (property, index = 0) => {
      if (!property) return "";

      // 有照片時顯示真實照片
      if (
        property.房屋照片 &&
        Array.isArray(property.房屋照片) &&
        property.房屋照片.length > 0
      ) {
        // 檢查圖片並找到可用的
        let attempts = 0;
        let currentIndex = index;
        const maxAttempts = property.房屋照片.length;

        // 遞迴查找可用圖片
        const findValidImage = (idx) => {
          // 防止無限循環
          if (attempts >= maxAttempts) {
            return `url(https://picsum.photos/id/${
              (((property.編碼 || 0) * 13) % 100) + 1000
            }/600/400)`;
          }

          attempts++;

          // 確保索引在範圍內
          if (idx >= property.房屋照片.length) {
            idx = 0; // 循環回到第一張
          }

          const imageUrl = property.房屋照片[idx];

          // 嘗試載入圖片
          try {
            const loadedImg = require("@/" + imageUrl);

            // 檢查實際載入後的圖片URL是否包含"-1.49632716"
            if (
              loadedImg &&
              typeof loadedImg === "string" &&
              loadedImg.includes("-1.49632716")
            ) {
              return findValidImage(idx + 1);
            }

            return `url(${loadedImg})`;
          } catch (e) {
            return findValidImage(idx + 1);
          }
        };

        // 開始查找有效圖片
        return findValidImage(currentIndex);
      }

      // 無照片時使用預設圖片
      return 'url(\'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="1" height="1" viewBox="0 0 1 1"%3E%3Crect width="1" height="1" fill="%23f5f5f5"/%3E%3C/svg%3E\')';
    }

    // 簡化圖片載入狀態處理
    const handleImageLoad = (propertyId) => {
      imageLoadStatus.value[propertyId] = true
    }

    const handleImageError = (event, propertyId) => {
      console.error(`圖片載入失敗: ${propertyId}`)
      imageLoadStatus.value[propertyId] = false
      event.target.style.backgroundImage = getPropertyImage(null)
    }

    const selectedProperty = ref(null);
    const currentPhotoIndex = ref(0);
    const slideShowInterval = ref(null);

    // 添加顯示詳細資訊的方法
    const showPropertyDetail = (property) => {
      selectedProperty.value = property;
      currentPhotoIndex.value = 0;
      document.body.style.overflow = "hidden";
    };

    // 關閉詳細資訊
    const closePropertyDetail = () => {
      selectedProperty.value = null;
      document.body.style.overflow = "auto";
    };

    return {
      imageLoadStatus,
      getPropertyImage,
      handleImageLoad,
      handleImageError,
      filteredProperties: computed(() => store.state.filteredAccommodations),
      router,
      selectedProperty,
      currentPhotoIndex,
      showPropertyDetail,
      closePropertyDetail,
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

    // 添加全局函數用於按鈕點擊
    window.viewDetails = (propertyId) => {
      this.router.push({
        name: 'accommodation-detail',
        params: { id: propertyId }
      });
    };
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

      if (!this.map || !this.filteredProperties || !window.google) return;

      // 建立地理編碼服務
      const geocoder = new window.google.maps.Geocoder();

      // 為每個物件建立標記
      this.filteredProperties.forEach(property => {
        // 使用地址進行地理編碼
        geocoder.geocode({ address: property.地址 }, (results, status) => {
          if (status === 'OK' && results[0]) {
            const position = results[0].geometry.location;
            const marker = new window.google.maps.Marker({
              position: position,
              map: this.map,
              title: property.標題,
              animation: window.google.maps.Animation.DROP
            });

            const imageStyle = this.getPropertyImage(property, 0);
            
            // 使用與 FavoritesPage 相同的愛心按鈕結構
            const content = `
              <div class="gm-info-window">
                <div class="gm-info-content">
                  <div class="gm-image-container">
                    <div class="gm-property-image" style="background-image: ${imageStyle}"></div>
                    <button class="gm-favorite-btn" data-property-id="${property.編碼}">
                      <div class="gm-heart-icon"></div>
                    </button>
                  </div>
                  <div class="gm-details">
                    <div class="gm-rating">
                      <span class="gm-score">${(Math.random() * 2 + 8).toFixed(1)}</span>
                      <span class="gm-reviews">${Math.floor(Math.random() * 100)} 則評價</span>
                    </div>
                    <h3 class="gm-title">${property.標題}</h3>
                    <div class="gm-location">
                      <span>中壢</span>
                      <span class="gm-dot">•</span>
                      <span>距中心 ${(Math.random() * 3 + 1).toFixed(1)} 公里</span>
                    </div>
                    <div class="gm-price">NT$ ${property.房租}/月</div>
                    <div class="gm-tags">
                      <span>${property.出租房數.套房.坪數}</span>
                      ${property.出租房數.套房.空房 ? `<span>空房: ${property.出租房數.套房.空房}間</span>` : ''}
                    </div>
                    <button class="gm-action-btn" onclick="window.viewPropertyDetails(${property.編碼})">
                      前往查看
                    </button>
                  </div>
                </div>
              </div>
            `;

            const infoWindow = new window.google.maps.InfoWindow({
              content: content,
              maxWidth: 400
            });

            // 添加信息窗口的 domready 事件監聽
            google.maps.event.addListener(infoWindow, 'domready', () => {
              const favoriteBtn = document.querySelector(`.remove-favorite[data-property-id="${property.編碼}"]`);
              if (favoriteBtn) {
                favoriteBtn.addEventListener('click', (e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  this.removeFavorite(property.編碼);
                });
              }

              const actionButton = document.querySelector('.action-button');
              if (actionButton) {
                actionButton.addEventListener('click', () => {
                  router.push({
                    name: 'accommodation-detail',
                    params: { id: property.編碼 }
                  });
                });
              }
            });

            marker.addListener('click', () => {
              this.markers.forEach(m => m.infoWindow?.close());
              infoWindow.open(this.map, marker);
            });

            marker.infoWindow = infoWindow;
            marker.propertyId = property.編碼;
            this.markers.push(marker);
          }
        });
      });
    },

    // 添加移除收藏方法
    async removeFavorite(id) {
      try {
        const success = await this.$store.dispatch('removeFavorite', id);
        if (!success) {
          setTimeout(() => {
            // alert("因連線問題，變更僅保存在本機。下次登入時將同步變更。");
          }, 300);
        }
      } catch (error) {
        console.error("Error removing favorite:", error);
      }
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
/* 保留現有的地圖和側邊欄樣式 */
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
  height: auto; /* 改為自動高度 */
  min-height: 120px; /* 設定最小高度 */
  padding: 10px; /* 添加內距 */
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
  justify-content: flex-start; /* 改為靠上對齊 */
  gap: 8px; /* 添加間距 */
}

.image-container {
  position: relative;
  width: 120px;
  height: 120px;
  background-color: #f5f5f5;
  overflow: hidden;
  border-radius: 8px;
  flex-shrink: 0; /* 防止圖片容器縮小 */
}

.property-thumbnail {
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

/* 圖片容器相關樣式 */
.image-container {
  position: relative;
  width: 120px;
  height: 120px;
  background-color: #f5f5f5;
  overflow: hidden;
  border-radius: 8px;
  flex-shrink: 0; /* 防止圖片容器縮小 */
}

.property-thumbnail {
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

h4 {
  margin: 0;
  font-size: 1rem;
  color: #333;
  line-height: 1.4; /* 添加行高 */
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2; /* 限制兩行 */
  -webkit-box-orient: vertical;
  word-break: break-word; /* 允許文字換行 */
}

.price {
  font-weight: bold;
  color: #007bff;
  font-size: 1rem;
  line-height: 1.2;
}

.location {
  color: #666;
  font-size: 0.9rem;
  margin: 4px 0;
  display: flex;
  align-items: flex-start; /* 改為靠上對齊 */
  gap: 4px;
  line-height: 1.4;
  word-break: break-word; /* 允許文字換行 */
}

.location-icon {
  flex-shrink: 0; /* 防止圖示縮小 */
  margin-top: 2px; /* 微調圖示位置 */
}

.amenities {
  display: flex;
  flex-wrap: wrap; /* 允許換行 */
  gap: 8px;
  font-size: 0.85rem;
  color: #666;
  line-height: 1.2;
}

.amenities span {
  background: #f5f5f5;
  padding: 4px 8px;
  border-radius: 4px;
  white-space: nowrap; /* 防止文字換行 */
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

/* 確保這些樣式存在且沒有重複 */
.map-info-window {
  width: 300px;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0,0,0,0.15);
}

.info-image-container {
  width: 100%;
  height: 200px;
  position: relative;
  overflow: hidden;
}

.info-image {
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  transition: transform 0.3s;
}

.info-content {
  padding: 16px;
}

.action-button {
  width: 100%;
  height: 44px;
  background: #0066cc;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 16px;
}

.action-button:hover {
  background: #0052a3;
}

/* 評分和其他內容樣式 */
.rating-section {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.score {
  background: #0066cc;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: bold;
}

.reviews {
  color: #666;
  font-size: 14px;
}

.location {
  color: #666;
  font-size: 14px;
  margin: 8px 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.dot {
  color: #999;
}

.price {
  color: #0066cc;
  font-size: 18px;
  font-weight: bold;
  margin: 12px 0;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.tags span {
  background: #f5f5f5;
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 14px;
  color: #666;
}

/* Google Maps InfoWindow 樣式覆蓋 */
::v-deep .gm-style .gm-style-iw-c {
  padding: 0 !important;
  border-radius: 12px !important;
}

::v-deep .gm-style .gm-style-iw-d {
  overflow: hidden !important;
  padding: 0 !important;
}

::v-deep .gm-style .gm-style-iw-t::after {
  display: none;
}

::v-deep .gm-ui-hover-effect {
  display: none !important;
}
</style>
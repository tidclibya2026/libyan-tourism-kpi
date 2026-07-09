const MAP_API_BASE = "http://127.0.0.1:8000";

let tourismMap;
let cityMarkersLayer;

document.addEventListener("DOMContentLoaded", () => {
  initTourismMap();
});

async function initTourismMap() {
  const mapElement = document.getElementById("tourismMap");
  if (!mapElement) return;

  tourismMap = L.map("tourismMap", {
    zoomControl: true,
    scrollWheelZoom: true
  }).setView([27.5, 17.0], 6);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "© OpenStreetMap"
  }).addTo(tourismMap);

  cityMarkersLayer = L.layerGroup().addTo(tourismMap);

  addMapLegend();

  const response = await fetch(`${MAP_API_BASE}/api/cities`);
  const data = await response.json();

  renderCityMarkers(data.cities, "all");
  initMapButtons(data.cities);
}

function renderCityMarkers(cities, filter) {
  cityMarkersLayer.clearLayers();

  const filteredCities = filterCities(cities, filter);

  filteredCities.forEach(city => {
    if (!city.lat || !city.lng) return;

    const marker = L.circleMarker([city.lat, city.lng], {
      radius: getMarkerRadius(city.total_guests),
      color: getCityColor(city.total_guests),
      fillColor: getCityColor(city.total_guests),
      fillOpacity: 0.72,
      weight: 2
    });

    marker.bindPopup(buildCityPopup(city));
    marker.addTo(cityMarkersLayer);
  });

  if (filteredCities.length > 0) {
    const bounds = filteredCities.map(city => [city.lat, city.lng]);
    tourismMap.fitBounds(bounds, {
      padding: [35, 35]
    });
  }
}

function filterCities(cities, filter) {
  if (filter === "major") {
    return cities.filter(city => city.total_guests >= 50000);
  }

  if (filter === "medium") {
    return cities.filter(city => city.total_guests >= 4000 && city.total_guests < 50000);
  }

  if (filter === "limited") {
    return cities.filter(city => city.total_guests < 4000);
  }

  return cities;
}

function getCityColor(totalGuests) {
  if (totalGuests >= 100000) return "#1e5a88";
  if (totalGuests >= 10000) return "#d4af37";
  if (totalGuests >= 4000) return "#2c7a4d";
  return "#c0392b";
}

function getMarkerRadius(totalGuests) {
  if (totalGuests >= 100000) return 18;
  if (totalGuests >= 50000) return 15;
  if (totalGuests >= 10000) return 12;
  if (totalGuests >= 4000) return 10;
  return 8;
}

function buildCityPopup(city) {
  return `
    <div class="city-popup">
      <h3>${city.name_ar}</h3>
      <p><strong>الاسم الإنجليزي:</strong> ${city.name_en}</p>
      <p><strong>إجمالي النزلاء:</strong> ${formatMapNumber(city.total_guests)}</p>
      <p><strong>الحصة الوطنية:</strong> ${city.share_percent}%</p>

      <div class="popup-kpi">
        <div>
          <strong>${formatMapNumber(city.libyans)}</strong>
          ليبيون
        </div>
        <div>
          <strong>${formatMapNumber(city.arabs)}</strong>
          عرب
        </div>
        <div>
          <strong>${formatMapNumber(city.foreigners)}</strong>
          أجانب
        </div>
        <div>
          <strong>${city.foreign_share_percent}%</strong>
          نسبة الأجانب
        </div>
      </div>
    </div>
  `;
}

function initMapButtons(cities) {
  const buttons = document.querySelectorAll(".map-btn");

  buttons.forEach(button => {
    button.addEventListener("click", () => {
      buttons.forEach(btn => btn.classList.remove("active"));
      button.classList.add("active");

      const layer = button.dataset.layer;
      renderCityMarkers(cities, layer);
    });
  });

  const allButton = document.querySelector('.map-btn[data-layer="all"]');
  if (allButton) allButton.classList.add("active");
}

function addMapLegend() {
  const legend = L.control({
    position: "bottomright"
  });

  legend.onAdd = function () {
    const div = L.DomUtil.create("div", "legend");

    div.innerHTML = `
      <strong>تصنيف النشاط السياحي</strong>
      <div class="legend-item">
        <span class="legend-dot" style="background:#1e5a88"></span>
        أكثر من 100 ألف نزيل
      </div>
      <div class="legend-item">
        <span class="legend-dot" style="background:#d4af37"></span>
        من 10 آلاف إلى 100 ألف
      </div>
      <div class="legend-item">
        <span class="legend-dot" style="background:#2c7a4d"></span>
        من 4 آلاف إلى 10 آلاف
      </div>
      <div class="legend-item">
        <span class="legend-dot" style="background:#c0392b"></span>
        أقل من 4 آلاف
      </div>
    `;

    return div;
  };

  legend.addTo(tourismMap);
}

function formatMapNumber(value) {
  return Number(value).toLocaleString("ar-LY");
}
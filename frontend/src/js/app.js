const API_BASE = "http://127.0.0.1:8000";

async function loadDashboard() {
  const kpiResponse = await fetch(`${API_BASE}/api/kpis`);
  const data = await kpiResponse.json();

  const forecastResponse = await fetch(`${API_BASE}/api/forecast/2035`);
  const forecast = await forecastResponse.json();

  renderKPIs(data);
  renderContinentsChart(data.continents);
  renderForecast(forecast);
}

function renderKPIs(data) {
  const grid = document.getElementById("kpiGrid");

  const items = [
    ["السواح الدوليون", data.international_tourists],
    ["الرحلات السياحية", data.tourism_trips],
    ["نزلاء الفنادق", data.hotel_guests],
    ["الفنادق", data.hotels],
    ["الشقق الفندقية", data.hotel_apartments],
    ["الشركات السياحية", data.tourism_companies],
    ["زوار المواقع الأثرية", data.heritage_visitors],
    ["إيرادات الاصطياف", data.summer_revenue_lyd + " د.ل"]
  ];

  grid.innerHTML = items.map(item => `
    <div class="kpi-card">
      <h2>${Number(item[1]).toLocaleString("ar-LY")}</h2>
      <p>${item[0]}</p>
    </div>
  `).join("");
}

function renderContinentsChart(continents) {
  new Chart(document.getElementById("continentsChart"), {
    type: "doughnut",
    data: {
      labels: ["أوروبا", "آسيا", "أفريقيا", "الأمريكيتين", "أستراليا"],
      datasets: [{
        data: [
          continents.Europe,
          continents.Asia,
          continents.Africa,
          continents.Americas,
          continents.Australia
        ]
      }]
    }
  });
}

function renderForecast(forecast) {
  document.getElementById("forecastBox").innerHTML = `
    <div class="kpi-grid">
      <div class="kpi-card">
        <h2>${forecast.international_tourists_2035.toLocaleString("ar-LY")}</h2>
        <p>السواح الدوليون 2035</p>
      </div>
      <div class="kpi-card">
        <h2>${forecast.hotel_guests_2035.toLocaleString("ar-LY")}</h2>
        <p>نزلاء الفنادق 2035</p>
      </div>
      <div class="kpi-card">
        <h2>${forecast.hotels_2035.toLocaleString("ar-LY")}</h2>
        <p>الفنادق 2035</p>
      </div>
      <div class="kpi-card">
        <h2>${forecast.companies_2035.toLocaleString("ar-LY")}</h2>
        <p>الشركات السياحية 2035</p>
      </div>
    </div>
  `;
}

loadDashboard();
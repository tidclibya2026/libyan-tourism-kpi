const API_BASE = "http://127.0.0.1:8000";

let charts = {};

document.addEventListener("DOMContentLoaded", () => {
  loadDashboard();
});

async function loadDashboard() {
  try {
    const [kpiResponse, forecastResponse, citiesResponse, continentsResponse] = await Promise.all([
      fetch(`${API_BASE}/api/kpis`),
      fetch(`${API_BASE}/api/forecast/2035`),
      fetch(`${API_BASE}/api/cities`),
      fetch(`${API_BASE}/api/continents`)
    ]);

    if (!kpiResponse.ok) throw new Error("فشل تحميل المؤشرات الوطنية");
    if (!forecastResponse.ok) throw new Error("فشل تحميل التنبؤات");
    if (!citiesResponse.ok) throw new Error("فشل تحميل بيانات المدن");
    if (!continentsResponse.ok) throw new Error("فشل تحميل بيانات القارات");

    const data = await kpiResponse.json();
    const forecast = await forecastResponse.json();
    const citiesData = await citiesResponse.json();
    const continentsData = await continentsResponse.json();

    renderKPIs(data);
    renderContinentsChart(continentsData.continents);
    renderForecast(forecast);
    renderCitiesTable(citiesData.cities);
    renderCitiesChart(citiesData.cities);
    renderNationalityChart(citiesData.cities);
    renderTripoliDashboard(citiesData.cities);

  } catch (error) {
    showError(error.message);
    console.error(error);
  }
}

function renderKPIs(data) {
  const grid = document.getElementById("kpiGrid");
  if (!grid) return;

  const items = [
    {
      title: "السواح الدوليون",
      value: data.international_tourists,
      note: "بتأشيرة سياحية",
      icon: "🌍"
    },
    {
      title: "الرحلات السياحية",
      value: data.tourism_trips,
      note: "إجمالي الرحلات",
      icon: "🧭"
    },
    {
      title: "نزلاء مرافق الإيواء",
      value: data.hotel_guests,
      note: "فنادق وقرى وشقق",
      icon: "👥"
    },
    {
      title: "الفنادق",
      value: data.hotels,
      note: "منشآت فندقية",
      icon: "🏨"
    },
    {
      title: "الشقق الفندقية",
      value: data.hotel_apartments,
      note: "شقق فندقية",
      icon: "🏢"
    },
    {
      title: "القرى السياحية",
      value: data.tourist_villages,
      note: "قرى ومنتجعات",
      icon: "🏖️"
    },
    {
      title: "الشركات السياحية",
      value: data.tourism_companies,
      note: "لديها إذن مزاولة",
      icon: "💼"
    },
    {
      title: "زوار المواقع الأثرية",
      value: data.heritage_visitors,
      note: "زوار المدن الأثرية",
      icon: "🏛️"
    },
    {
      title: "إيرادات الاصطياف",
      value: `${formatNumber(data.summer_revenue_lyd)} د.ل`,
      note: "تقدير موسم الاصطياف",
      icon: "💰"
    }
  ];

  grid.innerHTML = items.map(item => `
    <div class="kpi-card">
      <div class="kpi-icon">${item.icon}</div>
      <h2>${typeof item.value === "number" ? formatNumber(item.value) : item.value}</h2>
      <p>${item.title}</p>
      <small>${item.note}</small>
    </div>
  `).join("");
}

function renderContinentsChart(continents) {
  const canvas = document.getElementById("continentsChart");
  if (!canvas) return;

  destroyChart("continentsChart");

  charts.continentsChart = new Chart(canvas, {
    type: "doughnut",
    data: {
      labels: continents.map(item => `${item.name_ar} (${item.share_percent}%)`),
      datasets: [{
        label: "عدد السواح",
        data: continents.map(item => item.value),
        backgroundColor: [
          "#1e5a88",
          "#d4af37",
          "#2c7a4d",
          "#8b5a2b",
          "#7f8c8d"
        ],
        borderWidth: 2
      }]
    },
    options: defaultChartOptions()
  });
}

function renderForecast(forecast) {
  const box = document.getElementById("forecastBox");
  if (!box) return;

  box.innerHTML = `
    <div class="mini-grid">
      <div class="mini-kpi">
        <h3>${formatNumber(forecast.international_tourists_2035)}</h3>
        <p>السواح الدوليون 2035</p>
      </div>

      <div class="mini-kpi">
        <h3>${formatNumber(forecast.hotel_guests_2035)}</h3>
        <p>نزلاء الإيواء 2035</p>
      </div>

      <div class="mini-kpi">
        <h3>${formatNumber(forecast.hotels_2035)}</h3>
        <p>الفنادق 2035</p>
      </div>

      <div class="mini-kpi">
        <h3>${formatNumber(forecast.companies_2035)}</h3>
        <p>الشركات 2035</p>
      </div>

      <div class="mini-kpi">
        <h3>${formatNumber(forecast.heritage_visitors_2035)}</h3>
        <p>زوار الآثار 2035</p>
      </div>

      <div class="mini-kpi">
        <h3>${formatNumber(forecast.summer_revenue_lyd_2035)} د.ل</h3>
        <p>إيرادات الاصطياف 2035</p>
      </div>
    </div>
  `;
}

function renderCitiesTable(cities) {
  const tbody = document.querySelector("#citiesTable tbody");
  if (!tbody) return;

  tbody.innerHTML = cities.map(city => `
    <tr>
      <td>
        <strong>${city.name_ar}</strong>
        <small class="table-subtitle">${city.name_en}</small>
      </td>
      <td>${formatNumber(city.libyans)}</td>
      <td>${formatNumber(city.arabs)}</td>
      <td>${formatNumber(city.foreigners)}</td>
      <td><strong>${formatNumber(city.total_guests)}</strong></td>
      <td>${city.share_percent}%</td>
      <td>${city.domestic_share_percent}%</td>
      <td>${city.arab_share_percent}%</td>
      <td>${city.foreign_share_percent}%</td>
    </tr>
  `).join("");
}

function renderCitiesChart(cities) {
  const canvas = document.getElementById("citiesChart");
  if (!canvas) return;

  destroyChart("citiesChart");

  const sorted = [...cities].sort((a, b) => b.total_guests - a.total_guests);

  charts.citiesChart = new Chart(canvas, {
    type: "bar",
    data: {
      labels: sorted.map(city => city.name_ar),
      datasets: [{
        label: "عدد النزلاء",
        data: sorted.map(city => city.total_guests),
        backgroundColor: "#1e5a88",
        borderRadius: 8
      }]
    },
    options: {
      ...defaultChartOptions(),
      indexAxis: "y",
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: context => `${formatNumber(context.raw)} نزيل`
          }
        }
      }
    }
  });
}

function renderNationalityChart(cities) {
  const canvas = document.getElementById("nationalityChart");
  if (!canvas) return;

  destroyChart("nationalityChart");

  const totals = cities.reduce(
    (acc, city) => {
      acc.libyans += city.libyans;
      acc.arabs += city.arabs;
      acc.foreigners += city.foreigners;
      return acc;
    },
    { libyans: 0, arabs: 0, foreigners: 0 }
  );

  charts.nationalityChart = new Chart(canvas, {
    type: "pie",
    data: {
      labels: ["ليبيون", "عرب", "أجانب"],
      datasets: [{
        data: [totals.libyans, totals.arabs, totals.foreigners],
        backgroundColor: ["#2c7a4d", "#d4af37", "#c0392b"],
        borderWidth: 2
      }]
    },
    options: defaultChartOptions()
  });
}

function renderTripoliDashboard(cities) {
  const tripoli = cities.find(city => city.id === "tripoli");
  const box = document.getElementById("tripoliBox");

  if (!tripoli || !box) return;

  box.innerHTML = `
    <div class="mini-grid">
      <div class="mini-kpi">
        <h3>${formatNumber(tripoli.companies)}</h3>
        <p>الشركات السياحية</p>
      </div>

      <div class="mini-kpi">
        <h3>${formatNumber(tripoli.offices)}</h3>
        <p>المكاتب السياحية</p>
      </div>

      <div class="mini-kpi">
        <h3>${formatNumber(tripoli.accommodation_total)}</h3>
        <p>إجمالي مرافق الإيواء</p>
      </div>

      <div class="mini-kpi">
        <h3>${formatNumber(tripoli.hotels)}</h3>
        <p>الفنادق</p>
      </div>

      <div class="mini-kpi">
        <h3>${formatNumber(tripoli.hotel_apartments)}</h3>
        <p>الشقق الفندقية</p>
      </div>

      <div class="mini-kpi">
        <h3>${formatNumber(tripoli.tourist_villages)}</h3>
        <p>القرى السياحية</p>
      </div>
    </div>
  `;

  renderTripoliAccommodationChart(tripoli);
}

function renderTripoliAccommodationChart(tripoli) {
  const canvas = document.getElementById("tripoliAccommodationChart");
  if (!canvas) return;

  destroyChart("tripoliAccommodationChart");

  charts.tripoliAccommodationChart = new Chart(canvas, {
    type: "doughnut",
    data: {
      labels: [
        `فنادق ${tripoli.accommodation_structure.hotels_percent}%`,
        `شقق فندقية ${tripoli.accommodation_structure.hotel_apartments_percent}%`,
        `قرى سياحية ${tripoli.accommodation_structure.tourist_villages_percent}%`
      ],
      datasets: [{
        data: [
          tripoli.hotels,
          tripoli.hotel_apartments,
          tripoli.tourist_villages
        ],
        backgroundColor: ["#1e5a88", "#d4af37", "#2c7a4d"],
        borderWidth: 2
      }]
    },
    options: defaultChartOptions()
  });
}

function defaultChartOptions() {
  return {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        position: "bottom",
        labels: {
          font: {
            family: "Tahoma"
          }
        }
      }
    }
  };
}

function destroyChart(chartId) {
  if (charts[chartId]) {
    charts[chartId].destroy();
    delete charts[chartId];
  }
}

function formatNumber(value) {
  return Number(value).toLocaleString("ar-LY");
}

function showError(message) {
  document.body.insertAdjacentHTML("afterbegin", `
    <div class="error-banner">
      ${message}
    </div>
  `);
}
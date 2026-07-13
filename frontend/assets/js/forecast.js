/**
 * National Tourism Forecast Module
 * Libyan Tourism Information & Documentation Center
 *
 * مسؤوليات الملف:
 * - الاتصال بمسار التنبؤات حتى 2035.
 * - قراءة القيم الأساسية لسنة 2025.
 * - حساب نسب النمو المتوقعة.
 * - عرض بطاقات التنبؤات.
 * - إنشاء رسم بياني لمعدلات النمو.
 */

(function initializeDashboardForecast() {
    "use strict";

    /* =====================================================
       Required dependencies
    ====================================================== */

    if (!window.DashboardConfig) {
        throw new Error(
            "DashboardConfig غير متاح. "
            + "يجب تحميل config.js قبل forecast.js."
        );
    }

    if (!window.DashboardAPI) {
        throw new Error(
            "DashboardAPI غير متاح. "
            + "يجب تحميل api.js قبل forecast.js."
        );
    }

    const config = window.DashboardConfig;
    const api = window.DashboardAPI;


    /* =====================================================
       State
    ====================================================== */

    const state = {
        initialized: false,
        loading: false,
        forecast: null,
        summary: null,
        growthRates: {},
        chart: null,
        error: null,
        loadedAt: null,
    };


    /* =====================================================
       Forecast definitions
    ====================================================== */

    const forecastDefinitions = [
        {
            code: "international_tourists",
            label: "السياح الدوليون",
            baseKey: "international_tourists",
            forecastKey:
                "international_tourists_2035",
            valueElementId:
                "forecast-international-tourists",
            growthElementId:
                "forecast-international-tourists-growth",
            format: "integer",
        },
        {
            code: "hotel_guests",
            label: "نزلاء منشآت الإيواء",
            baseKey: "hotel_guests",
            forecastKey:
                "hotel_guests_2035",
            valueElementId:
                "forecast-hotel-guests",
            growthElementId:
                "forecast-hotel-guests-growth",
            format: "integer",
        },
        {
            code: "hotels",
            label: "الفنادق",
            baseKey: "hotels",
            forecastKey:
                "hotels_2035",
            valueElementId:
                "forecast-hotels",
            growthElementId:
                "forecast-hotels-growth",
            format: "integer",
        },
        {
            code: "companies",
            label: "الشركات السياحية",
            baseKey: "tourism_companies",
            forecastKey:
                "companies_2035",
            valueElementId:
                "forecast-companies",
            growthElementId:
                "forecast-companies-growth",
            format: "integer",
        },
        {
            code: "heritage_visitors",
            label: "زوار التراث والمتاحف",
            baseKey: "heritage_visitors",
            forecastKey:
                "heritage_visitors_2035",
            valueElementId:
                "forecast-heritage-visitors",
            growthElementId:
                "forecast-heritage-visitors-growth",
            format: "integer",
        },
        {
            code: "summer_revenue",
            label: "الإيرادات السياحية الصيفية",
            baseKey: "summer_revenue_lyd",
            forecastKey:
                "summer_revenue_lyd_2035",
            valueElementId:
                "forecast-summer-revenue",
            growthElementId:
                "forecast-summer-revenue-growth",
            format: "currency",
        },
    ];


    /* =====================================================
       General helpers
    ====================================================== */

    function toNumber(
        value,
        fallback = 0
    ) {
        const numericValue = Number(value);

        return Number.isFinite(numericValue)
            ? numericValue
            : fallback;
    }


    function getElement(elementId) {
        return document.getElementById(
            elementId
        );
    }


    function setText(
        elementId,
        value
    ) {
        const element = getElement(
            elementId
        );

        if (!element) {
            return;
        }

        element.textContent = value;
    }


    function formatInteger(value) {
        return new Intl.NumberFormat(
            config.format?.locale || "ar-LY",
            {
                maximumFractionDigits: 0,
            }
        ).format(
            toNumber(value, 0)
        );
    }


    function formatCurrency(value) {
        return new Intl.NumberFormat(
            config.format?.locale || "ar-LY",
            {
                style: "currency",
                currency: "LYD",
                currencyDisplay: "symbol",
                maximumFractionDigits: 0,
            }
        ).format(
            toNumber(value, 0)
        );
    }


    function formatPercentage(value) {
        return (
            new Intl.NumberFormat(
                config.format?.locale || "ar-LY",
                {
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 1,
                }
            ).format(
                toNumber(value, 0)
            )
            + "%"
        );
    }


    function formatValue(
        value,
        format
    ) {
        if (format === "currency") {
            return formatCurrency(value);
        }

        return formatInteger(value);
    }


    function calculateGrowthRate(
        baseValue,
        forecastValue
    ) {
        const base = toNumber(
            baseValue,
            0
        );

        const forecast = toNumber(
            forecastValue,
            0
        );

        if (base <= 0) {
            return null;
        }

        return (
            (
                forecast - base
            )
            / base
        ) * 100;
    }


    function getForecastEndpoint() {
        return (
            String(
                config.api.baseUrl || ""
            )
                .replace(/\/+$/, "")
            + "/api/forecast/2035"
        );
    }


    function debugLog(...values) {
        if (config.app?.debug) {
            console.info(
                "[LNTIP Forecast]",
                ...values
            );
        }
    }


    function debugError(...values) {
        console.error(
            "[LNTIP Forecast]",
            ...values
        );
    }


    /* =====================================================
       Status handling
    ====================================================== */

    function setStatus(
        status,
        message
    ) {
        const statusElement = getElement(
            "forecast-status"
        );

        if (!statusElement) {
            return;
        }

        statusElement.dataset.status =
            status;

        statusElement.textContent =
            message;
    }


    function setLoading(isLoading) {
        state.loading = isLoading;

        const refreshButton = getElement(
            "forecast-refresh-button"
        );

        if (refreshButton) {
            refreshButton.disabled =
                isLoading;

            refreshButton.textContent =
                isLoading
                    ? "جاري تحديث التنبؤات…"
                    : "تحديث التنبؤات";
        }

        const section = getElement(
            "forecast-section"
        );

        if (section) {
            section.dataset.loading =
                String(isLoading);
        }
    }


    function showError(error) {
        state.error = error;

        setStatus(
            "error",
            "تعذر تحميل بيانات التنبؤات"
        );

        const errorElement = getElement(
            "forecast-error"
        );

        if (errorElement) {
            errorElement.hidden = false;

            errorElement.textContent = (
                error?.message
                || "حدث خطأ أثناء الاتصال بمحرك التنبؤ."
            );
        }
    }


    function hideError() {
        const errorElement = getElement(
            "forecast-error"
        );

        if (errorElement) {
            errorElement.hidden = true;
            errorElement.textContent = "";
        }
    }


    /* =====================================================
       API
    ====================================================== */

    function getForecast2035() {
        return api.request(
            getForecastEndpoint(),
            {
                endpointName:
                    "التنبؤات السياحية حتى 2035",
            }
        );
    }


    async function loadForecastData() {
        setLoading(true);
        hideError();

        state.error = null;

        setStatus(
            "loading",
            "جاري تحميل توقعات 2035"
        );

        try {
            const results =
                await Promise.allSettled([
                    getForecast2035(),
                    api.getSummary(),
                ]);

            const forecastResult =
                results[0];

            const summaryResult =
                results[1];

            if (
                forecastResult.status
                !== "fulfilled"
            ) {
                throw forecastResult.reason;
            }

            state.forecast =
                forecastResult.value;

            state.summary = (
                summaryResult.status
                === "fulfilled"
                    ? summaryResult.value
                    : {}
            );

            state.loadedAt =
                new Date().toISOString();

            calculateAllGrowthRates();
            renderAll();

            setStatus(
                "success",
                "التنبؤات متاحة حتى 2035"
            );

            debugLog(
                "Forecast data loaded.",
                {
                    forecast:
                        state.forecast,
                    summary:
                        state.summary,
                    growthRates:
                        state.growthRates,
                }
            );

            return {
                forecast:
                    state.forecast,
                summary:
                    state.summary,
                growthRates:
                    state.growthRates,
            };

        } catch (error) {
            showError(error);

            debugError(
                "Failed to load forecast.",
                error
            );

            throw error;

        } finally {
            setLoading(false);
        }
    }


    /* =====================================================
       Growth calculations
    ====================================================== */

    function calculateAllGrowthRates() {
        const growthRates = {};

        forecastDefinitions.forEach(
            (definition) => {
                const baseValue = toNumber(
                    state.summary?.[
                        definition.baseKey
                    ],
                    0
                );

                const forecastValue =
                    toNumber(
                        state.forecast?.[
                            definition.forecastKey
                        ],
                        0
                    );

                growthRates[
                    definition.code
                ] = calculateGrowthRate(
                    baseValue,
                    forecastValue
                );
            }
        );

        state.growthRates =
            growthRates;
    }


    /* =====================================================
       Rendering
    ====================================================== */

    function renderYears() {
        setText(
            "forecast-base-year",
            formatInteger(
                state.forecast?.base_year
                || 2025
            )
        );

        setText(
            "forecast-target-year",
            formatInteger(
                state.forecast?.target_year
                || 2035
            )
        );
    }


    function renderForecastCards() {
        forecastDefinitions.forEach(
            (definition) => {
                const forecastValue =
                    toNumber(
                        state.forecast?.[
                            definition.forecastKey
                        ],
                        0
                    );

                const growthRate =
                    state.growthRates[
                        definition.code
                    ];

                setText(
                    definition.valueElementId,
                    formatValue(
                        forecastValue,
                        definition.format
                    )
                );

                setText(
                    definition.growthElementId,
                    growthRate === null
                        ? "لا تتوفر سنة أساس"
                        : (
                            "+"
                            + formatPercentage(
                                growthRate
                            )
                        )
                );
            }
        );
    }


    function renderMethodology() {
        setText(
            "forecast-methodology",
            (
                "تقديرات مركبة انطلاقًا من سنة الأساس "
                + formatInteger(
                    state.forecast?.base_year
                    || 2025
                )
                + " وحتى سنة الهدف "
                + formatInteger(
                    state.forecast?.target_year
                    || 2035
                )
                + "."
            )
        );
    }


    function destroyChart() {
        if (state.chart) {
            state.chart.destroy();
            state.chart = null;
        }

        const canvas = getElement(
            "forecast-growth-chart"
        );

        if (
            canvas
            && window.Chart
            && typeof window.Chart.getChart
                === "function"
        ) {
            const existingChart =
                window.Chart.getChart(
                    canvas
                );

            if (existingChart) {
                existingChart.destroy();
            }
        }
    }


    function renderGrowthChart() {
        const canvas = getElement(
            "forecast-growth-chart"
        );

        if (!canvas) {
            return;
        }

        if (
            typeof window.Chart
            === "undefined"
        ) {
            debugError(
                "Chart.js غير متاح."
            );

            return;
        }

        destroyChart();

        const labels =
            forecastDefinitions.map(
                (definition) => {
                    return definition.label;
                }
            );

        const values =
            forecastDefinitions.map(
                (definition) => {
                    return toNumber(
                        state.growthRates[
                            definition.code
                        ],
                        0
                    );
                }
            );

        const chartColors = [
            config.charts?.colors?.primary
                || "#174b7e",

            config.charts?.colors?.gold
                || "#c99a2e",

            config.charts?.colors?.info
                || "#2d7fb8",

            config.charts?.colors?.success
                || "#2f855a",

            config.charts?.colors?.warning
                || "#b7791f",

            config.charts?.colors?.secondary
                || "#586b7d",
        ];

        state.chart = new window.Chart(
            canvas,
            {
                type: "bar",

                data: {
                    labels,

                    datasets: [
                        {
                            label:
                                "النمو المتوقع بين 2025 و2035",

                            data: values,

                            backgroundColor:
                                chartColors,

                            borderWidth: 0,

                            borderRadius: 8,

                            maxBarThickness: 42,
                        },
                    ],
                },

                options: {
                    responsive: true,
                    maintainAspectRatio: false,

                    indexAxis: "y",

                    locale:
                        config.format?.locale
                        || "ar-LY",

                    animation: {
                        duration: 750,
                    },

                    interaction: {
                        mode: "nearest",
                        intersect: false,
                    },

                    plugins: {
                        legend: {
                            display: false,
                        },

                        tooltip: {
                            rtl: true,

                            callbacks: {
                                label(context) {
                                    return (
                                        " النمو المتوقع: "
                                        + formatPercentage(
                                            context.raw
                                        )
                                    );
                                },
                            },
                        },
                    },

                    scales: {
                        x: {
                            beginAtZero: true,

                            grid: {
                                color:
                                    "rgba(10,36,64,0.08)",
                            },

                            ticks: {
                                callback(value) {
                                    return (
                                        formatInteger(
                                            value
                                        )
                                        + "%"
                                    );
                                },

                                color: "#586b7d",
                            },

                            title: {
                                display: true,
                                text:
                                    "نسبة النمو المتوقعة",

                                color: "#586b7d",
                            },
                        },

                        y: {
                            grid: {
                                display: false,
                            },

                            ticks: {
                                color: "#152435",

                                font: {
                                    family:
                                        config.charts
                                            ?.fontFamily
                                        || (
                                            '"Segoe UI", '
                                            + "Tahoma, Arial, "
                                            + "sans-serif"
                                        ),

                                    size: 12,
                                },
                            },
                        },
                    },
                },
            }
        );
    }


    function renderAll() {
        renderYears();
        renderForecastCards();
        renderMethodology();
        renderGrowthChart();
    }


    /* =====================================================
       Lifecycle
    ====================================================== */

    async function init() {
        if (state.initialized) {
            return;
        }

        const forecastSection =
            getElement(
                "forecast-section"
            );

        if (!forecastSection) {
            debugLog(
                "قسم التنبؤات غير موجود "
                + "في الصفحة الحالية."
            );

            return;
        }

        state.initialized = true;

        const refreshButton =
            getElement(
                "forecast-refresh-button"
            );

        if (refreshButton) {
            refreshButton.addEventListener(
                "click",
                () => {
                    loadForecastData()
                        .catch(() => {
                            // الخطأ معالج داخل الوحدة.
                        });
                }
            );
        }

        await loadForecastData();
    }


    function destroy() {
        destroyChart();

        state.initialized = false;
        state.loading = false;
        state.forecast = null;
        state.summary = null;
        state.growthRates = {};
        state.error = null;
        state.loadedAt = null;
    }


    function resize() {
        if (state.chart) {
            state.chart.resize();
        }
    }


    /* =====================================================
       Public interface
    ====================================================== */

    const DashboardForecast = {
        version: "1.0.0",

        init,
        load: loadForecastData,
        render: renderAll,
        resize,
        destroy,

        getForecast2035,

        isAvailable() {
            return Boolean(
                state.forecast
            );
        },

        getState() {
            return {
                initialized:
                    state.initialized,

                loading:
                    state.loading,

                forecast:
                    state.forecast,

                summary:
                    state.summary,

                growthRates: {
                    ...state.growthRates,
                },

                error:
                    state.error,

                loadedAt:
                    state.loadedAt,
            };
        },
    };

    Object.freeze(
        DashboardForecast
    );

    Object.defineProperty(
        window,
        "DashboardForecast",
        {
            value:
                DashboardForecast,

            writable: false,
            enumerable: true,
            configurable: false,
        }
    );


    /* =====================================================
       Automatic initialization
    ====================================================== */

    document.addEventListener(
        "DOMContentLoaded",
        () => {
            DashboardForecast.init()
                .catch(() => {
                    // الخطأ معالج داخل الوحدة.
                });
        }
    );

    window.addEventListener(
        "resize",
        () => {
            window.clearTimeout(
                resize.timeoutId
            );

            resize.timeoutId =
                window.setTimeout(
                    resize,
                    180
                );
        }
    );


    /* =====================================================
       Development log
    ====================================================== */

    debugLog(
        "Forecast module ready.",
        {
            endpoint:
                getForecastEndpoint(),
        }
    );
})();
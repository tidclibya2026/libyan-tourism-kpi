/**
 * Monthly Accommodation Operations Dashboard
 * لوحة التشغيل الشهري لمنشآت الإيواء
 */

(function initializeAccommodationMonthlyDashboard() {
    "use strict";

    const state = {
        initialized: false,
        loading: false,
        data: null,
        error: null,
        chart: null,
    };

    const monthNames = {
        1: "يناير",
        2: "فبراير",
        3: "مارس",
        4: "أبريل",
        5: "مايو",
        6: "يونيو",
        7: "يوليو",
        8: "أغسطس",
        9: "سبتمبر",
        10: "أكتوبر",
        11: "نوفمبر",
        12: "ديسمبر",
    };


    function select(selector) {
        return document.querySelector(
            selector
        );
    }


    function setText(
        selector,
        value
    ) {
        const element = (
            typeof selector === "string"
                ? select(selector)
                : selector
        );

        if (!element) {
            return;
        }

        element.textContent = (
            value === null
            || typeof value === "undefined"
            || value === ""
                ? "—"
                : String(value)
        );
    }


    function isAvailableValue(value) {
        return (
            value !== null
            && typeof value !== "undefined"
            && Number.isFinite(
                Number(value)
            )
        );
    }


    function formatInteger(value) {
        if (!isAvailableValue(value)) {
            return "بانتظار البيانات";
        }

        return new Intl.NumberFormat(
            "ar-LY",
            {
                maximumFractionDigits: 0,
            }
        ).format(
            Number(value)
        );
    }


    function formatDecimal(value) {
        if (!isAvailableValue(value)) {
            return "بانتظار البيانات";
        }

        return new Intl.NumberFormat(
            "ar-LY",
            {
                minimumFractionDigits: 0,
                maximumFractionDigits: 2,
            }
        ).format(
            Number(value)
        );
    }


    function formatPercent(value) {
        if (!isAvailableValue(value)) {
            return "بانتظار البيانات";
        }

        return `${formatDecimal(value)}%`;
    }


    function formatCurrency(value) {
        if (!isAvailableValue(value)) {
            return "بانتظار البيانات";
        }

        return `${formatDecimal(value)} د.ل`;
    }


    function escapeHtml(value) {
        const element = document.createElement(
            "div"
        );

        element.textContent = String(
            value ?? ""
        );

        return element.innerHTML;
    }


    function getApiBaseUrl() {
        const configuredBaseUrl = (
            window.DashboardConfig
            ?.api
            ?.baseUrl
        );

        return String(
            configuredBaseUrl
            || "http://127.0.0.1:8000"
        ).replace(
            /\/+$/,
            ""
        );
    }


    function getFilters() {
        return {
            month:
                select(
                    "#accommodation-monthly-filter-month"
                )?.value || "",

            branch:
                select(
                    "#accommodation-monthly-filter-branch"
                )?.value || "",

            municipality:
                select(
                    "#accommodation-monthly-filter-municipality"
                )?.value || "",

            verification_status:
                select(
                    "#accommodation-monthly-filter-verification"
                )?.value || "",
        };
    }


    function buildRequestUrl() {
        const parameters = new URLSearchParams();
        const filters = getFilters();

        Object.entries(filters).forEach(
            ([key, value]) => {
                if (value !== "") {
                    parameters.set(
                        key,
                        value
                    );
                }
            }
        );

        const queryString = parameters.toString();

        return (
            `${getApiBaseUrl()}`
            + "/api/accommodation/monthly"
            + (
                queryString
                    ? `?${queryString}`
                    : ""
            )
        );
    }


    async function requestMonthlyData() {
        const response = await fetch(
            buildRequestUrl(),
            {
                method: "GET",

                headers: {
                    Accept:
                        "application/json",
                },

                cache:
                    "no-store",
            }
        );

        let payload = null;

        try {
            payload = await response.json();
        } catch (error) {
            payload = null;
        }

        if (!response.ok) {
            throw new Error(
                payload?.detail?.message_ar
                || payload?.message_ar
                || (
                    "تعذر تحميل بيانات "
                    + "الإيواء الشهرية. "
                    + `HTTP ${response.status}`
                )
            );
        }

        if (
            !payload
            || typeof payload !== "object"
        ) {
            throw new Error(
                "استجابة بيانات الإيواء "
                + "الشهرية غير صالحة."
            );
        }

        return payload;
    }


    function resolveStatusLabel(status) {
        const labels = {
            available:
                "بيانات تشغيلية متاحة",

            no_data:
                "بانتظار البيانات التشغيلية",

            no_matching_data:
                "لا توجد نتائج مطابقة",

            error:
                "تعذر تحميل البيانات",
        };

        return (
            labels[String(status || "")]
            || "قيد المراجعة"
        );
    }


    function populateSelect(
        selector,
        items,
        allLabel,
        formatter
    ) {
        const element = select(selector);

        if (!element) {
            return;
        }

        const currentValue = element.value;

        const normalizedItems = (
            Array.isArray(items)
                ? items
                : []
        );

        element.innerHTML = "";

        const allOption = document.createElement(
            "option"
        );

        allOption.value = "";
        allOption.textContent = allLabel;

        element.appendChild(
            allOption
        );

        normalizedItems.forEach(
            (item) => {
                const option = document.createElement(
                    "option"
                );

                option.value = String(item);

                option.textContent = (
                    typeof formatter === "function"
                        ? formatter(item)
                        : String(item)
                );

                element.appendChild(
                    option
                );
            }
        );

        if (
            currentValue
            && normalizedItems
                .map(String)
                .includes(currentValue)
        ) {
            element.value = currentValue;
        }
    }


    function renderFilterOptions(options) {
        const safeOptions = (
            options
            && typeof options === "object"
                ? options
                : {}
        );

        populateSelect(
            "#accommodation-monthly-filter-month",
            safeOptions.months,
            "جميع الأشهر",
            (month) => {
                return (
                    monthNames[Number(month)]
                    || `الشهر ${month}`
                );
            }
        );

        populateSelect(
            "#accommodation-monthly-filter-branch",
            safeOptions.branches,
            "جميع الفروع"
        );

        populateSelect(
            "#accommodation-monthly-filter-municipality",
            safeOptions.municipalities,
            "جميع البلديات"
        );

        populateSelect(
            "#accommodation-monthly-filter-verification",
            safeOptions.verification_statuses,
            "جميع حالات التحقق"
        );
    }


    function indicatorValue(
        indicators,
        code
    ) {
        const indicator = (
            indicators
            && typeof indicators === "object"
                ? indicators[code]
                : null
        );

        return indicator?.value ?? null;
    }


    function renderTotals(totals) {
        const safeTotals = totals || {};

        setText(
            "#accommodation-monthly-reporting-facilities",
            formatInteger(
                safeTotals.reporting_facilities
            )
        );

        setText(
            "#accommodation-monthly-months-covered",
            formatInteger(
                safeTotals.months_covered
            )
        );

        setText(
            "#accommodation-monthly-total-guests",
            formatInteger(
                safeTotals.total_guests
            )
        );

        setText(
            "#accommodation-monthly-tourist-nights",
            formatInteger(
                safeTotals.tourist_nights
            )
        );

        setText(
            "#accommodation-monthly-room-revenue",
            formatCurrency(
                safeTotals.room_revenue_lyd
            )
        );
    }


    function renderIndicators(indicators) {
        setText(
            "#accommodation-monthly-room-occupancy",
            formatPercent(
                indicatorValue(
                    indicators,
                    "room_occupancy_rate"
                )
            )
        );

        setText(
            "#accommodation-monthly-bed-occupancy",
            formatPercent(
                indicatorValue(
                    indicators,
                    "bed_occupancy_rate"
                )
            )
        );

        setText(
            "#accommodation-monthly-average-stay",
            (
                isAvailableValue(
                    indicatorValue(
                        indicators,
                        "average_length_of_stay"
                    )
                )
                    ? (
                        `${formatDecimal(
                            indicatorValue(
                                indicators,
                                "average_length_of_stay"
                            )
                        )} ليلة`
                    )
                    : "بانتظار البيانات"
            )
        );

        setText(
            "#accommodation-monthly-adr",
            formatCurrency(
                indicatorValue(
                    indicators,
                    "average_daily_rate"
                )
            )
        );

        setText(
            "#accommodation-monthly-revpar",
            formatCurrency(
                indicatorValue(
                    indicators,
                    "revenue_per_available_room"
                )
            )
        );
    }


    function renderReadiness(readiness) {
        const safeReadiness = readiness || {};

        const value = Number(
            safeReadiness.readiness_percent
            || 0
        );

        const percentage = Math.min(
            Math.max(
                Number.isFinite(value)
                    ? value
                    : 0,
                0
            ),
            100
        );

        setText(
            "#accommodation-monthly-readiness-value",
            `${formatDecimal(percentage)}%`
        );

        setText(
            "#accommodation-monthly-available-count",
            formatInteger(
                safeReadiness.available_indicators
            )
        );

        setText(
            "#accommodation-monthly-unavailable-count",
            formatInteger(
                safeReadiness.unavailable_indicators
            )
        );

        const bar = select(
            "#accommodation-monthly-readiness-bar"
        );

        if (bar) {
            bar.style.width =
                `${percentage}%`;

            bar.setAttribute(
                "aria-valuenow",
                String(percentage)
            );
        }
    }


    function destroyChart() {
        if (
            state.chart
            && typeof state.chart.destroy
                === "function"
        ) {
            state.chart.destroy();
        }

        state.chart = null;
    }


    function renderTrendChart(trends) {
        const canvas = select(
            "#accommodation-monthly-trend-chart"
        );

        const statusElement = select(
            "#accommodation-monthly-chart-status"
        );

        if (!canvas) {
            return;
        }

        destroyChart();

        if (
            !Array.isArray(trends)
            || trends.length === 0
        ) {
            if (statusElement) {
                statusElement.textContent = (
                    "لا توجد سلسلة شهرية متاحة "
                    + "حتى الآن."
                );
            }

            return;
        }

        if (
            typeof window.Chart
            === "undefined"
        ) {
            if (statusElement) {
                statusElement.textContent = (
                    "تعذر تحميل مكتبة "
                    + "الرسوم البيانية."
                );
            }

            return;
        }

        const labels = trends.map(
            (item) => {
                return (
                    `${monthNames[item.month] || item.month}`
                    + ` ${item.year}`
                );
            }
        );

        const roomValues = trends.map(
            (item) => {
                return (
                    isAvailableValue(
                        item.room_occupancy_rate
                    )
                        ? Number(
                            item.room_occupancy_rate
                        )
                        : null
                );
            }
        );

        const bedValues = trends.map(
            (item) => {
                return (
                    isAvailableValue(
                        item.bed_occupancy_rate
                    )
                        ? Number(
                            item.bed_occupancy_rate
                        )
                        : null
                );
            }
        );

        state.chart = new window.Chart(
            canvas.getContext("2d"),
            {
                type: "line",

                data: {
                    labels,

                    datasets: [
                        {
                            label:
                                "إشغال الغرف",

                            data:
                                roomValues,

                            borderColor:
                                "#0b3a67",

                            backgroundColor:
                                "rgba(11, 58, 103, 0.12)",

                            borderWidth:
                                3,

                            tension:
                                0.32,

                            spanGaps:
                                false,
                        },
                        {
                            label:
                                "إشغال الأسرة",

                            data:
                                bedValues,

                            borderColor:
                                "#b9933f",

                            backgroundColor:
                                "rgba(185, 147, 63, 0.12)",

                            borderWidth:
                                3,

                            tension:
                                0.32,

                            spanGaps:
                                false,
                        },
                    ],
                },

                options: {
                    responsive:
                        true,

                    maintainAspectRatio:
                        false,

                    interaction: {
                        mode:
                            "index",

                        intersect:
                            false,
                    },

                    scales: {
                        y: {
                            beginAtZero:
                                true,

                            suggestedMax:
                                100,

                            ticks: {
                                callback(value) {
                                    return `${value}%`;
                                },
                            },
                        },
                    },

                    plugins: {
                        legend: {
                            position:
                                "bottom",

                            rtl:
                                true,
                        },

                        tooltip: {
                            rtl:
                                true,

                            textDirection:
                                "rtl",

                            callbacks: {
                                label(context) {
                                    return (
                                        `${context.dataset.label}: `
                                        + (
                                            context.raw === null
                                                ? "غير متاح"
                                                : `${formatDecimal(
                                                    context.raw
                                                )}%`
                                        )
                                    );
                                },
                            },
                        },
                    },
                },
            }
        );

        if (statusElement) {
            statusElement.textContent = (
                "اتجاه نسب الإشغال المحسوبة "
                + "من السجلات التشغيلية الفعلية."
            );
        }
    }


    function renderMessage(data) {
        const element = select(
            "#accommodation-monthly-message"
        );

        if (!element) {
            return;
        }

        element.dataset.status =
            data.status || "no_data";

        if (data.status === "available") {
            element.textContent = (
                `تم تحميل ${formatInteger(
                    data.records_count
                )} سجل تشغيلي ضمن نطاق التصفية.`
            );

            return;
        }

        if (
            data.status
            === "no_matching_data"
        ) {
            element.textContent = (
                "لا توجد سجلات مطابقة "
                + "للمرشحات المحددة."
            );

            return;
        }

        element.textContent = (
            "بانتظار إدخال السجلات الشهرية "
            + "الفعلية. لن تُعرض قيم إشغال "
            + "صفرية عند غياب البيانات."
        );
    }


    function render(data) {
        state.data = data;
        state.error = null;

        const statusBadge = select(
            "#accommodation-monthly-status"
        );

        if (statusBadge) {
            statusBadge.dataset.status =
                data.status || "no_data";

            statusBadge.textContent =
                resolveStatusLabel(
                    data.status
                );
        }

        setText(
            "#accommodation-monthly-year",
            data.year
        );

        setText(
            "#accommodation-monthly-records-count",
            formatInteger(
                data.records_count
            )
        );

        renderFilterOptions(
            data.filter_options
        );

        renderTotals(
            data.totals
        );

        renderIndicators(
            data.indicators
        );

        renderReadiness(
            data.readiness
        );

        renderTrendChart(
            data.trends
        );

        renderMessage(
            data
        );
    }


    function renderError(error) {
        state.error = error;

        const statusBadge = select(
            "#accommodation-monthly-status"
        );

        if (statusBadge) {
            statusBadge.dataset.status =
                "error";

            statusBadge.textContent =
                "تعذر تحميل البيانات";
        }

        const message = select(
            "#accommodation-monthly-message"
        );

        if (message) {
            message.dataset.status =
                "error";

            message.textContent = (
                error?.message
                || (
                    "تعذر الاتصال بخدمة "
                    + "الإيواء الشهرية."
                )
            );
        }

        destroyChart();

        setText(
            "#accommodation-monthly-chart-status",
            "تعذر تحميل بيانات الاتجاه."
        );
    }


    async function load() {
        if (state.loading) {
            return;
        }

        state.loading = true;

        const refreshButton = select(
            "#accommodation-monthly-refresh"
        );

        if (refreshButton) {
            refreshButton.disabled = true;
            refreshButton.textContent =
                "جاري التحديث…";
        }

        try {
            const data = await (
                requestMonthlyData()
            );

            render(data);

        } catch (error) {
            console.error(
                "[Accommodation Monthly]",
                error
            );

            renderError(error);

        } finally {
            state.loading = false;

            if (refreshButton) {
                refreshButton.disabled = false;
                refreshButton.textContent =
                    "تحديث البيانات";
            }
        }
    }


    function resetFilters() {
        [
            "#accommodation-monthly-filter-month",
            "#accommodation-monthly-filter-branch",
            "#accommodation-monthly-filter-municipality",
            "#accommodation-monthly-filter-verification",
        ].forEach(
            (selector) => {
                const element = select(
                    selector
                );

                if (element) {
                    element.value = "";
                }
            }
        );

        load();
    }


    function registerEvents() {
        const form = select(
            "#accommodation-monthly-filters"
        );

        if (form) {
            form.addEventListener(
                "submit",
                (event) => {
                    event.preventDefault();
                    load();
                }
            );
        }

        const resetButton = select(
            "#accommodation-monthly-reset"
        );

        if (resetButton) {
            resetButton.addEventListener(
                "click",
                resetFilters
            );
        }

        const refreshButton = select(
            "#accommodation-monthly-refresh"
        );

        if (refreshButton) {
            refreshButton.addEventListener(
                "click",
                load
            );
        }
    }


    function initialize() {
        if (state.initialized) {
            return;
        }

        state.initialized = true;

        registerEvents();
        load();
    }


    window.AccommodationMonthlyDashboard = {
        initialize,
        reload: load,

        getState() {
            return {
                initialized:
                    state.initialized,

                loading:
                    state.loading,

                data:
                    state.data,

                error:
                    state.error,
            };
        },
    };


    if (
        document.readyState
        === "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            initialize,
            {
                once: true,
            }
        );

    } else {
        initialize();
    }
})();

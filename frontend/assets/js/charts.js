/**
 * National Tourism Dashboard Charts
 * Libyan Tourism Information & Documentation Center
 *
 * مسؤوليات الملف:
 * - رسم توزيع السياح الدوليين حسب القارات.
 * - رسم تركيب نزلاء منشآت الإيواء.
 * - رسم ترتيب المدن حسب إجمالي النزلاء.
 * - تحديث الرسوم عند تحديث البيانات.
 * - معالجة غياب البيانات أو مكتبة Chart.js.
 */

(function initializeDashboardCharts() {
    "use strict";

    /* =====================================================
       Required configuration
    ====================================================== */

    if (!window.DashboardConfig) {
        throw new Error(
            "DashboardConfig غير متاح. "
            + "يجب تحميل config.js قبل charts.js."
        );
    }

    const config = window.DashboardConfig;
    const chartConfig = config.charts;

    const chartInstances = {
        continents: null,
        guestMix: null,
        cities: null,
    };


    /* =====================================================
       General helpers
    ====================================================== */

    /**
     * تحويل القيمة إلى رقم آمن.
     *
     * @param {*} value
     * @param {number} fallback
     * @returns {number}
     */
    function toNumber(value, fallback = 0) {
        const numericValue = Number(value);

        return Number.isFinite(numericValue)
            ? numericValue
            : fallback;
    }


    /**
     * ضمان أن القيمة قائمة.
     *
     * @param {*} value
     * @returns {Array}
     */
    function toArray(value) {
        return Array.isArray(value)
            ? value
            : [];
    }


    /**
     * تنسيق الأرقام وفق التنسيق الليبي العربي.
     *
     * @param {*} value
     * @returns {string}
     */
    function formatInteger(value) {
        return new Intl.NumberFormat(
            config.format.locale,
            config.format.integer
        ).format(
            toNumber(value, 0)
        );
    }


    /**
     * تنسيق النسب المئوية.
     *
     * @param {*} value
     * @returns {string}
     */
    function formatPercentage(value) {
        return (
            new Intl.NumberFormat(
                config.format.locale,
                config.format.percentage
            ).format(
                toNumber(value, 0)
            )
            + "%"
        );
    }


    /**
     * حساب النسبة المئوية بأمان.
     *
     * @param {number} value
     * @param {number} total
     * @returns {number}
     */
    function calculatePercentage(value, total) {
        const safeValue = toNumber(value, 0);
        const safeTotal = toNumber(total, 0);

        if (safeTotal <= 0) {
            return 0;
        }

        return Number(
            (
                safeValue
                / safeTotal
                * 100
            ).toFixed(2)
        );
    }


    /**
     * الحصول على عنصر Canvas.
     *
     * @param {string} selector
     * @returns {HTMLCanvasElement|null}
     */
    function getCanvas(selector) {
        const element = document.querySelector(
            selector
        );

        return (
            element instanceof HTMLCanvasElement
                ? element
                : null
        );
    }


    /**
     * التحقق من توفر Chart.js.
     *
     * @returns {boolean}
     */
    function isChartLibraryAvailable() {
        return (
            typeof window.Chart !== "undefined"
            && typeof window.Chart === "function"
        );
    }


    /**
     * إعداد القيم العامة لمكتبة Chart.js.
     */
    function configureChartDefaults() {
        if (!isChartLibraryAvailable()) {
            return;
        }

        window.Chart.defaults.font.family =
            chartConfig.fontFamily;

        window.Chart.defaults.color =
            chartConfig.textColor;

        window.Chart.defaults.animation.duration =
            chartConfig.animationDurationMilliseconds;

        window.Chart.defaults.responsive =
            chartConfig.responsive;

        window.Chart.defaults.maintainAspectRatio =
            chartConfig.maintainAspectRatio;
    }


    /* =====================================================
       Empty state handling
    ====================================================== */

    /**
     * حذف رسالة غياب البيانات.
     *
     * @param {HTMLCanvasElement} canvas
     */
    function clearEmptyState(canvas) {
        if (!canvas) {
            return;
        }

        canvas.hidden = false;

        const container = canvas.parentElement;

        if (!container) {
            return;
        }

        const emptyElement = container.querySelector(
            ".chart-empty-message"
        );

        if (emptyElement) {
            emptyElement.remove();
        }
    }


    /**
     * عرض رسالة بدل الرسم عند غياب البيانات.
     *
     * @param {HTMLCanvasElement|null} canvas
     * @param {string} message
     */
    function showEmptyState(canvas, message) {
        if (!canvas) {
            return;
        }

        destroyChartByCanvas(canvas);

        canvas.hidden = true;

        const container = canvas.parentElement;

        if (!container) {
            return;
        }

        const previousMessage = container.querySelector(
            ".chart-empty-message"
        );

        if (previousMessage) {
            previousMessage.remove();
        }

        const messageElement = document.createElement(
            "div"
        );

        messageElement.className =
            "chart-empty-message";

        messageElement.textContent = message;

        Object.assign(
            messageElement.style,
            {
                minHeight: "280px",
                height: "100%",
                display: "grid",
                placeItems: "center",
                padding: "24px",
                textAlign: "center",
                color: "#718094",
                fontSize: "0.9rem",
                background: "#f7f9fc",
                border: "1px dashed #c6d1dd",
                borderRadius: "12px",
            }
        );

        container.appendChild(messageElement);
    }


    /* =====================================================
       Chart lifecycle
    ====================================================== */

    /**
     * تدمير الرسم المرتبط بعنصر Canvas.
     *
     * @param {HTMLCanvasElement} canvas
     */
    function destroyChartByCanvas(canvas) {
        if (
            !canvas
            || !isChartLibraryAvailable()
        ) {
            return;
        }

        const existingChart = window.Chart.getChart(
            canvas
        );

        if (existingChart) {
            existingChart.destroy();
        }
    }


    /**
     * تدمير رسم محدد.
     *
     * @param {"continents"|"guestMix"|"cities"} name
     */
    function destroyChart(name) {
        const chart = chartInstances[name];

        if (
            chart
            && typeof chart.destroy === "function"
        ) {
            chart.destroy();
        }

        chartInstances[name] = null;
    }


    /**
     * تدمير جميع الرسوم.
     */
    function destroyAll() {
        destroyChart("continents");
        destroyChart("guestMix");
        destroyChart("cities");
    }


    /* =====================================================
       Custom Chart.js plugins
    ====================================================== */

    /**
     * إضافة نص في مركز الرسم الدائري.
     */
    const centerTextPlugin = {
        id: "lntipCenterText",

        afterDraw(chart, _arguments, options) {
            if (
                !options
                || options.display === false
            ) {
                return;
            }

            const {
                ctx,
                chartArea,
            } = chart;

            if (!chartArea) {
                return;
            }

            const centerX = (
                chartArea.left
                + chartArea.right
            ) / 2;

            const centerY = (
                chartArea.top
                + chartArea.bottom
            ) / 2;

            ctx.save();

            ctx.textAlign = "center";
            ctx.textBaseline = "middle";

            ctx.fillStyle = (
                options.color
                || chartConfig.titleColor
            );

            ctx.font = (
                `700 ${options.fontSize || 22}px `
                + chartConfig.fontFamily
            );

            ctx.fillText(
                options.text || "",
                centerX,
                centerY - 8
            );

            if (options.subtext) {
                ctx.fillStyle = (
                    options.subtextColor
                    || chartConfig.textColor
                );

                ctx.font = (
                    `500 ${options.subtextFontSize || 11}px `
                    + chartConfig.fontFamily
                );

                ctx.fillText(
                    options.subtext,
                    centerX,
                    centerY + 19
                );
            }

            ctx.restore();
        },
    };


    /**
     * رسم القيم بجانب الأعمدة.
     */
    const valueLabelsPlugin = {
        id: "lntipValueLabels",

        afterDatasetsDraw(
            chart,
            _arguments,
            options
        ) {
            if (
                !options
                || options.display === false
            ) {
                return;
            }

            const {
                ctx,
            } = chart;

            const indexAxis = (
                chart.options.indexAxis
                || "x"
            );

            ctx.save();

            ctx.fillStyle = (
                options.color
                || chartConfig.textColor
            );

            ctx.font = (
                `600 ${options.fontSize || 11}px `
                + chartConfig.fontFamily
            );

            chart.data.datasets.forEach(
                (dataset, datasetIndex) => {
                    const metadata =
                        chart.getDatasetMeta(
                            datasetIndex
                        );

                    if (metadata.hidden) {
                        return;
                    }

                    metadata.data.forEach(
                        (element, index) => {
                            const rawValue = toNumber(
                                dataset.data[index],
                                0
                            );

                            const formattedValue =
                                formatInteger(
                                    rawValue
                                );

                            const position =
                                element.tooltipPosition();

                            if (indexAxis === "y") {
                                ctx.textAlign = "right";
                                ctx.textBaseline = "middle";

                                const maximumX = (
                                    chart.chartArea.right
                                    - 4
                                );

                                ctx.fillText(
                                    formattedValue,
                                    maximumX,
                                    position.y
                                );
                            } else {
                                ctx.textAlign = "center";
                                ctx.textBaseline = "bottom";

                                ctx.fillText(
                                    formattedValue,
                                    position.x,
                                    Math.max(
                                        position.y - 7,
                                        chart.chartArea.top + 13
                                    )
                                );
                            }
                        }
                    );
                }
            );

            ctx.restore();
        },
    };


    /* =====================================================
       Common chart options
    ====================================================== */

    /**
     * إعدادات Tooltip الموحدة.
     *
     * @returns {Object}
     */
    function buildTooltipOptions() {
        return {
            rtl: true,
            textDirection: "rtl",

            backgroundColor: "rgba(6, 24, 43, 0.94)",
            titleColor: "#ffffff",
            bodyColor: "#ffffff",

            borderColor: "rgba(200, 155, 45, 0.55)",
            borderWidth: 1,

            padding: 12,
            cornerRadius: 8,

            displayColors: true,

            titleFont: {
                family: chartConfig.fontFamily,
                weight: "700",
            },

            bodyFont: {
                family: chartConfig.fontFamily,
            },
        };
    }


    /**
     * إعدادات وسيلة الإيضاح.
     *
     * @param {string} position
     * @returns {Object}
     */
    function buildLegendOptions(
        position = "bottom"
    ) {
        return {
            display: true,
            position,

            rtl: true,
            textDirection: "rtl",

            labels: {
                color: chartConfig.textColor,

                usePointStyle: true,
                pointStyle: "circle",

                padding: 18,
                boxWidth: 10,
                boxHeight: 10,

                font: {
                    family:
                        chartConfig.fontFamily,
                    size: 12,
                    weight: "600",
                },
            },
        };
    }


    /**
     * إعدادات المحور العددي.
     *
     * @returns {Object}
     */
    function buildNumericScale() {
        return {
            beginAtZero: true,

            border: {
                display: false,
            },

            grid: {
                color: chartConfig.gridColor,
                drawTicks: false,
            },

            ticks: {
                color: chartConfig.textColor,
                padding: 8,

                font: {
                    family:
                        chartConfig.fontFamily,
                    size: 11,
                },

                callback(value) {
                    return formatInteger(value);
                },
            },
        };
    }


    /**
     * إعدادات محور التصنيفات.
     *
     * @returns {Object}
     */
    function buildCategoryScale() {
        return {
            border: {
                display: false,
            },

            grid: {
                display: false,
            },

            ticks: {
                color: chartConfig.titleColor,
                padding: 8,

                font: {
                    family:
                        chartConfig.fontFamily,
                    size: 11,
                    weight: "600",
                },
            },
        };
    }


    /* =====================================================
       Continents chart
    ====================================================== */

    /**
     * رسم السياح حسب القارات.
     *
     * @param {Object} continentsData
     */
    function renderContinentsChart(
        continentsData
    ) {
        const canvas = getCanvas(
            config.ui.selectors.continentsChart
        );

        if (!canvas) {
            return;
        }

        destroyChart("continents");
        clearEmptyState(canvas);

        const items = toArray(
            continentsData?.items
        )
            .filter(
                (item) => {
                    return (
                        item
                        && toNumber(
                            item.tourists,
                            0
                        ) >= 0
                    );
                }
            )
            .sort(
                (firstItem, secondItem) => {
                    const firstRank = toNumber(
                        firstItem.market_rank,
                        999
                    );

                    const secondRank = toNumber(
                        secondItem.market_rank,
                        999
                    );

                    if (firstRank !== secondRank) {
                        return firstRank - secondRank;
                    }

                    return (
                        toNumber(
                            secondItem.tourists,
                            0
                        )
                        - toNumber(
                            firstItem.tourists,
                            0
                        )
                    );
                }
            );

        if (items.length === 0) {
            showEmptyState(
                canvas,
                config.ui.messages.emptyContinents
            );

            return;
        }

        if (!isChartLibraryAvailable()) {
            showEmptyState(
                canvas,
                "تعذر تحميل مكتبة الرسوم البيانية."
            );

            return;
        }

        const labels = items.map(
            (item) => {
                return (
                    item.name_ar
                    || item.name_en
                    || item.id
                    || "غير محدد"
                );
            }
        );

        const values = items.map(
            (item) => {
                return toNumber(
                    item.tourists,
                    0
                );
            }
        );

        const total = toNumber(
            continentsData
                ?.international_tourists_total,
            values.reduce(
                (sum, value) => sum + value,
                0
            )
        );

        chartInstances.continents =
            new window.Chart(
                canvas,
                {
                    type: "bar",

                    data: {
                        labels,

                        datasets: [
                            {
                                label:
                                    "عدد السياح الدوليين",

                                data: values,

                                backgroundColor:
                                    items.map(
                                        (_item, index) => {
                                            const colors =
                                                chartConfig
                                                    .colors
                                                    .continents;

                                            return colors[
                                                index
                                                % colors.length
                                            ];
                                        }
                                    ),

                                borderColor:
                                    items.map(
                                        (_item, index) => {
                                            const colors =
                                                chartConfig
                                                    .colors
                                                    .continents;

                                            return colors[
                                                index
                                                % colors.length
                                            ];
                                        }
                                    ),

                                borderWidth:
                                    chartConfig
                                        .defaults
                                        .borderWidth,

                                borderRadius:
                                    chartConfig
                                        .defaults
                                        .borderRadius,

                                borderSkipped: false,

                                maxBarThickness: 72,
                            },
                        ],
                    },

                    options: {
                        locale:
                            config.format.locale,

                        responsive:
                            chartConfig.responsive,

                        maintainAspectRatio:
                            chartConfig
                                .maintainAspectRatio,

                        animation: {
                            duration:
                                chartConfig
                                    .animationDurationMilliseconds,
                        },

                        interaction: {
                            mode: "index",
                            intersect: false,
                        },

                        layout: {
                            padding: {
                                top: 28,
                                right: 8,
                                bottom: 4,
                                left: 8,
                            },
                        },

                        scales: {
                            x: buildCategoryScale(),
                            y: buildNumericScale(),
                        },

                        plugins: {
                            legend: {
                                display: false,
                            },

                            tooltip: {
                                ...buildTooltipOptions(),

                                callbacks: {
                                    label(context) {
                                        const value =
                                            toNumber(
                                                context.raw,
                                                0
                                            );

                                        const share =
                                            calculatePercentage(
                                                value,
                                                total
                                            );

                                        return (
                                            ` ${formatInteger(value)} سائح`
                                            + ` — ${formatPercentage(share)}`
                                        );
                                    },
                                },
                            },

                            lntipValueLabels: {
                                display: true,
                                color:
                                    chartConfig
                                        .titleColor,
                                fontSize: 11,
                            },
                        },
                    },

                    plugins: [
                        valueLabelsPlugin,
                    ],
                }
            );
    }


    /* =====================================================
       Guest mix chart
    ====================================================== */

    /**
     * جمع النزلاء حسب الجنسية من بيانات المدن.
     *
     * @param {Array} cities
     * @returns {Object}
     */
    function aggregateGuestMix(cities) {
        return toArray(cities).reduce(
            (result, city) => {
                result.libyans += toNumber(
                    city?.libyans,
                    0
                );

                result.arabs += toNumber(
                    city?.arabs,
                    0
                );

                result.foreigners += toNumber(
                    city?.foreigners,
                    0
                );

                return result;
            },
            {
                libyans: 0,
                arabs: 0,
                foreigners: 0,
            }
        );
    }


    /**
     * رسم توزيع نزلاء الإيواء.
     *
     * @param {Object} dashboardData
     * @param {Object} summary
     */
    function renderGuestMixChart(
        dashboardData,
        summary = {}
    ) {
        const canvas = getCanvas(
            config.ui.selectors.guestMixChart
        );

        if (!canvas) {
            return;
        }

        destroyChart("guestMix");
        clearEmptyState(canvas);

        const cities = toArray(
            dashboardData?.cities?.top_items
        );

        const guestMix = aggregateGuestMix(
            cities
        );

        if (
            guestMix.libyans === 0
            && guestMix.arabs === 0
            && guestMix.foreigners === 0
        ) {
            guestMix.libyans = toNumber(
                summary.libyans,
                0
            );

            guestMix.arabs = toNumber(
                summary.arabs,
                0
            );

            guestMix.foreigners = toNumber(
                summary.foreigners,
                0
            );
        }

        const values = [
            guestMix.libyans,
            guestMix.arabs,
            guestMix.foreigners,
        ];

        const total = values.reduce(
            (sum, value) => sum + value,
            0
        );

        if (total <= 0) {
            showEmptyState(
                canvas,
                "لا توجد بيانات متاحة عن تركيب النزلاء."
            );

            return;
        }

        if (!isChartLibraryAvailable()) {
            showEmptyState(
                canvas,
                "تعذر تحميل مكتبة الرسوم البيانية."
            );

            return;
        }

        chartInstances.guestMix =
            new window.Chart(
                canvas,
                {
                    type: "doughnut",

                    data: {
                        labels: [
                            "ليبيون",
                            "عرب",
                            "أجانب",
                        ],

                        datasets: [
                            {
                                data: values,

                                backgroundColor: [
                                    chartConfig
                                        .colors
                                        .libyans,

                                    chartConfig
                                        .colors
                                        .arabs,

                                    chartConfig
                                        .colors
                                        .foreigners,
                                ],

                                borderColor: "#ffffff",
                                borderWidth: 4,

                                hoverBorderColor:
                                    "#ffffff",

                                hoverBorderWidth: 5,

                                spacing: 2,
                            },
                        ],
                    },

                    options: {
                        locale:
                            config.format.locale,

                        responsive:
                            chartConfig.responsive,

                        maintainAspectRatio:
                            chartConfig
                                .maintainAspectRatio,

                        cutout: "68%",

                        animation: {
                            duration:
                                chartConfig
                                    .animationDurationMilliseconds,
                        },

                        layout: {
                            padding: {
                                top: 8,
                                right: 8,
                                bottom: 8,
                                left: 8,
                            },
                        },

                        plugins: {
                            legend:
                                buildLegendOptions(
                                    "bottom"
                                ),

                            tooltip: {
                                ...buildTooltipOptions(),

                                callbacks: {
                                    label(context) {
                                        const value =
                                            toNumber(
                                                context.raw,
                                                0
                                            );

                                        const share =
                                            calculatePercentage(
                                                value,
                                                total
                                            );

                                        return (
                                            ` ${context.label}: `
                                            + `${formatInteger(value)}`
                                            + ` — ${formatPercentage(share)}`
                                        );
                                    },
                                },
                            },

                            lntipCenterText: {
                                display: true,

                                text:
                                    formatInteger(total),

                                subtext:
                                    "إجمالي النزلاء",

                                color:
                                    chartConfig
                                        .titleColor,

                                subtextColor:
                                    chartConfig
                                        .textColor,

                                fontSize: 22,
                                subtextFontSize: 11,
                            },
                        },
                    },

                    plugins: [
                        centerTextPlugin,
                    ],
                }
            );
    }


    /* =====================================================
       Cities chart
    ====================================================== */

    /**
     * رسم ترتيب المدن.
     *
     * @param {Object} citiesData
     */
    function renderCitiesChart(
        citiesData
    ) {
        const canvas = getCanvas(
            config.ui.selectors.citiesChart
        );

        if (!canvas) {
            return;
        }

        destroyChart("cities");
        clearEmptyState(canvas);

        const items = toArray(
            citiesData?.top_items
            || citiesData?.items
        )
            .filter(Boolean)
            .sort(
                (firstCity, secondCity) => {
                    const firstRank = toNumber(
                        firstCity.national_rank,
                        999
                    );

                    const secondRank = toNumber(
                        secondCity.national_rank,
                        999
                    );

                    if (firstRank !== secondRank) {
                        return firstRank - secondRank;
                    }

                    return (
                        toNumber(
                            secondCity.total_guests,
                            0
                        )
                        - toNumber(
                            firstCity.total_guests,
                            0
                        )
                    );
                }
            );

        if (items.length === 0) {
            showEmptyState(
                canvas,
                config.ui.messages.emptyCities
            );

            return;
        }

        if (!isChartLibraryAvailable()) {
            showEmptyState(
                canvas,
                "تعذر تحميل مكتبة الرسوم البيانية."
            );

            return;
        }

        const labels = items.map(
            (city) => {
                return (
                    city.name_ar
                    || city.name_en
                    || city.id
                    || "غير محدد"
                );
            }
        );

        const values = items.map(
            (city) => {
                return toNumber(
                    city.total_guests
                    ?? city.calculated_total_guests,
                    0
                );
            }
        );

        const colors =
            chartConfig.colors.cities;

        chartInstances.cities =
            new window.Chart(
                canvas,
                {
                    type: "bar",

                    data: {
                        labels,

                        datasets: [
                            {
                                label:
                                    "إجمالي النزلاء",

                                data: values,

                                backgroundColor:
                                    items.map(
                                        (_city, index) => {
                                            return colors[
                                                index
                                                % colors.length
                                            ];
                                        }
                                    ),

                                borderColor:
                                    items.map(
                                        (_city, index) => {
                                            return colors[
                                                index
                                                % colors.length
                                            ];
                                        }
                                    ),

                                borderWidth:
                                    chartConfig
                                        .defaults
                                        .borderWidth,

                                borderRadius:
                                    chartConfig
                                        .defaults
                                        .borderRadius,

                                borderSkipped: false,

                                maxBarThickness: 32,
                            },
                        ],
                    },

                    options: {
                        locale:
                            config.format.locale,

                        indexAxis: "y",

                        responsive:
                            chartConfig.responsive,

                        maintainAspectRatio:
                            chartConfig
                                .maintainAspectRatio,

                        animation: {
                            duration:
                                chartConfig
                                    .animationDurationMilliseconds,
                        },

                        interaction: {
                            mode: "nearest",
                            axis: "y",
                            intersect: false,
                        },

                        layout: {
                            padding: {
                                top: 4,
                                right: 8,
                                bottom: 4,
                                left: 68,
                            },
                        },

                        scales: {
                            x: buildNumericScale(),
                            y: buildCategoryScale(),
                        },

                        plugins: {
                            legend: {
                                display: false,
                            },

                            tooltip: {
                                ...buildTooltipOptions(),

                                callbacks: {
                                    label(context) {
                                        const city =
                                            items[
                                                context
                                                    .dataIndex
                                            ];

                                        const guests =
                                            toNumber(
                                                context.raw,
                                                0
                                            );

                                        const share =
                                            toNumber(
                                                city
                                                    ?.share_percent,
                                                0
                                            );

                                        return [
                                            ` إجمالي النزلاء: ${formatInteger(guests)}`,
                                            ` الحصة الوطنية: ${formatPercentage(share)}`,
                                        ];
                                    },

                                    afterBody(contextItems) {
                                        const dataIndex =
                                            contextItems[
                                                0
                                            ]?.dataIndex;

                                        const city =
                                            items[
                                                dataIndex
                                            ];

                                        if (!city) {
                                            return [];
                                        }

                                        return [
                                            `ليبيون: ${formatInteger(city.libyans)}`,
                                            `عرب: ${formatInteger(city.arabs)}`,
                                            `أجانب: ${formatInteger(city.foreigners)}`,
                                        ];
                                    },
                                },
                            },

                            lntipValueLabels: {
                                display: true,
                                color:
                                    chartConfig
                                        .titleColor,
                                fontSize: 10,
                            },
                        },
                    },

                    plugins: [
                        valueLabelsPlugin,
                    ],
                }
            );
    }


    /* =====================================================
       Complete dashboard rendering
    ====================================================== */

    /**
     * رسم جميع مخططات Dashboard.
     *
     * تستدعيها dashboard.js بعد وصول البيانات.
     *
     * @param {Object} payload
     */
    function renderAll({
        dashboard,
        summary = {},
    } = {}) {
        if (
            !dashboard
            || typeof dashboard !== "object"
        ) {
            console.warn(
                "[LNTIP Charts] "
                + "بيانات Dashboard غير متاحة."
            );

            return;
        }

        configureChartDefaults();

        renderContinentsChart(
            dashboard.continents
        );

        renderGuestMixChart(
            dashboard,
            summary
        );

        renderCitiesChart(
            dashboard.cities
        );
    }


    /**
     * إعادة ضبط أحجام الرسوم.
     */
    function resizeAll() {
        Object.values(
            chartInstances
        ).forEach(
            (chart) => {
                if (
                    chart
                    && typeof chart.resize
                        === "function"
                ) {
                    chart.resize();
                }
            }
        );
    }


    /**
     * إعادة رسم المخططات من آخر بيانات Dashboard.
     */
    function refreshFromDashboardState() {
        const dashboardState =
            window.DashboardApp
                ?.getState?.();

        const bundle =
            dashboardState?.bundle;

        if (!bundle?.dashboard) {
            return;
        }

        renderAll({
            dashboard:
                bundle.dashboard,

            summary:
                bundle.summary || {},
        });
    }


    /* =====================================================
       Public interface
    ====================================================== */

    const DashboardCharts = {
        version: "1.0.0",

        renderAll,

        renderContinentsChart,
        renderGuestMixChart,
        renderCitiesChart,

        destroyAll,
        resizeAll,
        refreshFromDashboardState,

        isAvailable:
            isChartLibraryAvailable,

        getInstances() {
            return {
                ...chartInstances,
            };
        },
    };

    Object.freeze(
        DashboardCharts
    );

    Object.defineProperty(
        window,
        "DashboardCharts",
        {
            value: DashboardCharts,
            writable: false,
            enumerable: true,
            configurable: false,
        }
    );


    /* =====================================================
       Window events
    ====================================================== */

    let resizeTimeoutId = null;

    window.addEventListener(
        "resize",
        () => {
            window.clearTimeout(
                resizeTimeoutId
            );

            resizeTimeoutId =
                window.setTimeout(
                    resizeAll,
                    180
                );
        }
    );


    /* =====================================================
       Development log
    ====================================================== */

    if (config.app.debug) {
        console.info(
            "[LNTIP Charts] Module ready.",
            {
                chartJsAvailable:
                    isChartLibraryAvailable(),
            }
        );
    }
})();
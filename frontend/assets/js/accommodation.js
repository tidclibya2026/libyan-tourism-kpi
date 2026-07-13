/**
 * Accommodation Dashboard Module
 * محور الإيواء والإشغال الفندقي
 */

(function initializeAccommodationModule() {
    "use strict";

    const state = {
        initialized: false,
        loading: false,
        data: null,
        error: null,
        chart: null,
    };

    const indicatorCodes = [
        "average_guests_per_facility",
        "average_rooms_per_facility",
        "average_beds_per_facility",
        "average_beds_per_room",
        "average_length_of_stay",
        "room_occupancy_rate",
        "bed_occupancy_rate",
        "average_daily_rate",
        "revenue_per_available_room",
    ];

    const missingInputLabels = {
        tourist_nights:
            "الليالي السياحية",

        occupied_room_nights:
            "ليالي الغرف المباعة",

        available_room_nights:
            "ليالي الغرف المتاحة",

        occupied_bed_nights:
            "ليالي الأسرة المشغولة",

        available_bed_nights:
            "ليالي الأسرة المتاحة",

        room_revenue_lyd:
            "إيرادات الغرف",

        total_guests:
            "إجمالي النزلاء",
    };


    function select(selector) {
        return document.querySelector(
            selector
        );
    }


    function setText(selector, value) {
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


    function toNumber(value, fallback = 0) {
        const numericValue = Number(value);

        return Number.isFinite(
            numericValue
        )
            ? numericValue
            : fallback;
    }


    function formatInteger(value) {
        return new Intl.NumberFormat(
            "ar-LY",
            {
                maximumFractionDigits: 0,
            }
        ).format(
            toNumber(value)
        );
    }


    function formatDecimal(value) {
        return new Intl.NumberFormat(
            "ar-LY",
            {
                minimumFractionDigits: 0,
                maximumFractionDigits: 2,
            }
        ).format(
            toNumber(value)
        );
    }


    function formatPercent(value) {
        return (
            `${formatDecimal(value)}%`
        );
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

        const fallbackBaseUrl = (
            "http://127.0.0.1:8000"
        );

        return String(
            configuredBaseUrl
            || fallbackBaseUrl
        ).replace(
            /\/+$/,
            ""
        );
    }


    async function requestAccommodation() {
        const url = (
            `${getApiBaseUrl()}`
            + "/api/accommodation"
        );

        const response = await fetch(
            url,
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
            const message = (
                payload?.detail?.message_ar
                || payload?.message_ar
                || payload?.message
                || (
                    "تعذر تحميل بيانات الإيواء. "
                    + `HTTP ${response.status}`
                )
            );

            throw new Error(message);
        }

        if (
            !payload
            || typeof payload !== "object"
        ) {
            throw new Error(
                "استجابة خدمة الإيواء غير صالحة."
            );
        }

        return payload;
    }


    function getIndicator(
        indicators,
        code
    ) {
        if (
            !indicators
            || typeof indicators !== "object"
        ) {
            return null;
        }

        return indicators[code] || null;
    }


    function resolveStatusText(status) {
        const normalizedStatus = String(
            status || ""
        ).toLowerCase();

        const labels = {
            complete:
                "البيانات التشغيلية مكتملة",

            available_with_operational_gaps:
                "متاح مع فجوات تشغيلية",

            unavailable:
                "البيانات غير متاحة",

            error:
                "تعذر تحميل البيانات",
        };

        return (
            labels[normalizedStatus]
            || "قيد المراجعة"
        );
    }


    function resolveIndicatorValue(
        indicator
    ) {
        if (
            !indicator
            || indicator.value === null
            || typeof indicator.value
                === "undefined"
        ) {
            return "غير متاح";
        }

        const unit = String(
            indicator.unit || ""
        );

        if (unit === "percent") {
            return formatPercent(
                indicator.value
            );
        }

        if (
            unit === "lyd_per_room_night"
            || unit
                === "lyd_per_available_room"
        ) {
            return (
                `${formatDecimal(
                    indicator.value
                )} د.ل`
            );
        }

        return formatDecimal(
            indicator.value
        );
    }


    function renderInventory(inventory) {
        const values = {
            "#accommodation-hotels":
                inventory.hotels,

            "#accommodation-hotel-apartments":
                inventory.hotel_apartments,

            "#accommodation-facilities":
                inventory.hotels_and_apartments,

            "#accommodation-villages":
                inventory.tourist_villages,

            "#accommodation-chalets":
                inventory.chalets,

            "#accommodation-rooms":
                inventory.reported_rooms,

            "#accommodation-hotel-beds":
                inventory.reported_hotel_beds,

            "#accommodation-chalet-beds":
                inventory.reported_chalet_beds,
        };

        Object.entries(values).forEach(
            ([selector, value]) => {
                setText(
                    selector,
                    formatInteger(value)
                );
            }
        );
    }


    function renderGuests(
        guests,
        indicators
    ) {
        setText(
            "#accommodation-total-guests",
            formatInteger(
                guests.total_guests
            )
        );

        setText(
            "#accommodation-libyan-guests",
            formatInteger(
                guests.libyan_guests
            )
        );

        setText(
            "#accommodation-arab-guests",
            formatInteger(
                guests.arab_guests
            )
        );

        setText(
            "#accommodation-foreign-guests",
            formatInteger(
                guests.foreign_guests
            )
        );

        const shares = {
            "#accommodation-libyan-share":
                "libyan_guest_share",

            "#accommodation-arab-share":
                "arab_guest_share",

            "#accommodation-foreign-share":
                "foreign_guest_share",
        };

        Object.entries(shares).forEach(
            ([selector, code]) => {
                const indicator = getIndicator(
                    indicators,
                    code
                );

                const value = indicator?.value;

                setText(
                    selector,
                    (
                        value !== null
                        && typeof value
                            !== "undefined"
                    )
                        ? formatPercent(value)
                        : "—"
                );
            }
        );

        setText(
            "#kpi-accommodation-guests",
            formatInteger(
                guests.total_guests
            )
        );
    }


    function renderReadiness(readiness) {
        const percentage = Math.min(
            Math.max(
                toNumber(
                    readiness
                        .readiness_percent
                ),
                0
            ),
            100
        );

        setText(
            "#accommodation-readiness-value",
            formatPercent(percentage)
        );

        setText(
            "#accommodation-available-count",
            formatInteger(
                readiness
                    .available_indicators
            )
        );

        setText(
            "#accommodation-unavailable-count",
            formatInteger(
                readiness
                    .unavailable_indicators
            )
        );

        const progressBar = select(
            "#accommodation-readiness-bar"
        );

        if (progressBar) {
            progressBar.style.width = (
                `${percentage}%`
            );

            progressBar.setAttribute(
                "aria-valuenow",
                String(percentage)
            );
        }
    }


    function renderVerification(guests) {
        const officialTotal = toNumber(
            guests.total_guests
        );

        const calculatedTotal = (
            toNumber(
                guests.libyan_guests
            )
            + toNumber(
                guests.arab_guests
            )
            + toNumber(
                guests.foreign_guests
            )
        );

        const difference = (
            officialTotal
            - calculatedTotal
        );

        const matched = (
            difference === 0
        );

        setText(
            "#accommodation-official-total",
            formatInteger(
                officialTotal
            )
        );

        setText(
            "#accommodation-calculated-total",
            formatInteger(
                calculatedTotal
            )
        );

        setText(
            "#accommodation-total-difference",
            formatInteger(
                difference
            )
        );

        setText(
            "#accommodation-data-source",
            guests.source_file
            || "ملف الإيواء الوطني 2025"
        );

        const statusElement = select(
            "#accommodation-verification-status"
        );

        const noteElement = select(
            "#accommodation-verification-note"
        );

        if (statusElement) {
            statusElement.classList.remove(
                "is-success",
                "is-warning",
                "is-danger"
            );

            if (matched) {
                statusElement.textContent =
                    "متطابق";

                statusElement.classList.add(
                    "is-success"
                );
            } else {
                statusElement.textContent =
                    "توجد فروقات";

                statusElement.classList.add(
                    "is-warning"
                );
            }
        }

        if (noteElement) {
            noteElement.classList.remove(
                "is-success",
                "is-warning",
                "is-danger"
            );

            if (matched) {
                noteElement.textContent = (
                    "تمت مطابقة الإجمالي الرسمي "
                    + "مع مجموع النزلاء الليبيين "
                    + "والعرب والأجانب دون فروقات."
                );

                noteElement.classList.add(
                    "is-success"
                );
            } else {
                noteElement.textContent = (
                    "توجد فروقات بين الإجمالي "
                    + "الرسمي ومجموع الجنسيات "
                    + "بقيمة "
                    + formatInteger(
                        Math.abs(difference)
                    )
                    + " نزيل."
                );

                noteElement.classList.add(
                    "is-warning"
                );
            }
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


    function renderGuestChart(guests) {
        const canvas = select(
            "#accommodation-guest-chart"
        );

        const statusElement = select(
            "#accommodation-chart-status"
        );

        if (!canvas) {
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

        const values = [
            toNumber(
                guests.libyan_guests
            ),

            toNumber(
                guests.arab_guests
            ),

            toNumber(
                guests.foreign_guests
            ),
        ];

        const total = values.reduce(
            (sum, value) => {
                return sum + value;
            },
            0
        );

        destroyChart();

        state.chart = new window.Chart(
            canvas.getContext("2d"),
            {
                type:
                    "doughnut",

                data: {
                    labels: [
                        "النزلاء الليبيون",
                        "النزلاء العرب",
                        "النزلاء الأجانب",
                    ],

                    datasets: [
                        {
                            label:
                                "عدد النزلاء",

                            data:
                                values,

                            backgroundColor: [
                                "#0b3a67",
                                "#b9933f",
                                "#2d7b66",
                            ],

                            borderColor:
                                "#ffffff",

                            borderWidth:
                                3,

                            hoverOffset:
                                8,
                        },
                    ],
                },

                options: {
                    responsive:
                        true,

                    maintainAspectRatio:
                        false,

                    cutout:
                        "62%",

                    plugins: {
                        legend: {
                            position:
                                "bottom",

                            rtl:
                                true,

                            labels: {
                                usePointStyle:
                                    true,

                                padding:
                                    17,
                            },
                        },

                        tooltip: {
                            rtl:
                                true,

                            textDirection:
                                "rtl",

                            callbacks: {
                                label(context) {
                                    const value = (
                                        toNumber(
                                            context.raw
                                        )
                                    );

                                    const share = (
                                        total > 0
                                            ? (
                                                value
                                                / total
                                                * 100
                                            )
                                            : 0
                                    );

                                    return (
                                        `${context.label}: `
                                        + `${formatInteger(value)} `
                                        + `(${formatPercent(share)})`
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
                "يعتمد المخطط على الأعداد "
                + "الرسمية للنزلاء حسب الجنسية."
            );
        }
    }


    function renderIndicators(indicators) {
        const container = select(
            "#accommodation-operational-grid"
        );

        if (!container) {
            return;
        }

        container.innerHTML = "";

        indicatorCodes.forEach(
            (code) => {
                const indicator = getIndicator(
                    indicators,
                    code
                );

                if (!indicator) {
                    return;
                }

                const status = String(
                    indicator.status
                    || "unavailable"
                );

                const available = (
                    status === "available"
                );

                const missingInputs = (
                    Array.isArray(
                        indicator.missing_inputs
                    )
                        ? indicator.missing_inputs
                        : []
                );

                const missingHtml = (
                    missingInputs.length > 0
                        ? `
                            <div class="accommodation-missing-inputs">
                                ${missingInputs
                                    .map((input) => {
                                        return `
                                            <span>
                                                ${escapeHtml(
                                                    missingInputLabels[
                                                        input
                                                    ]
                                                    || input
                                                )}
                                            </span>
                                        `;
                                    })
                                    .join("")}
                            </div>
                        `
                        : ""
                );

                const card = (
                    document.createElement(
                        "article"
                    )
                );

                card.className = (
                    "accommodation-indicator-card"
                );

                card.dataset.status =
                    status;

                card.innerHTML = `
                    <div class="accommodation-indicator-card__header">
                        <h4>
                            ${escapeHtml(
                                indicator.name_ar
                                || code
                            )}
                        </h4>

                        <span class="accommodation-indicator-card__status">
                            ${
                                available
                                    ? "متاح"
                                    : "ينتظر البيانات"
                            }
                        </span>
                    </div>

                    <strong class="accommodation-indicator-card__value">
                        ${escapeHtml(
                            resolveIndicatorValue(
                                indicator
                            )
                        )}
                    </strong>

                    <p class="accommodation-indicator-card__note">
                        ${escapeHtml(
                            indicator.note_ar
                            || (
                                available
                                    ? (
                                        "قيمة محسوبة "
                                        + "من البيانات الرسمية."
                                    )
                                    : (
                                        "يتطلب مدخلات "
                                        + "تشغيلية فعلية."
                                    )
                            )
                        )}
                    </p>

                    ${missingHtml}
                `;

                container.appendChild(
                    card
                );
            }
        );
    }


    function normalizeQualityFlag(
        flag,
        index
    ) {
        if (typeof flag === "string") {
            return {
                code:
                    `QUALITY_${index + 1}`,

                severity:
                    "warning",

                message:
                    flag,
            };
        }

        if (
            flag
            && typeof flag === "object"
        ) {
            return {
                code:
                    flag.code
                    || `QUALITY_${index + 1}`,

                severity:
                    flag.severity
                    || flag.status
                    || "warning",

                message:
                    flag.message_ar
                    || flag.message
                    || flag.note_ar
                    || "ملاحظة جودة بيانات.",
            };
        }

        return null;
    }


    function renderQualityFlags(flags) {
        const container = select(
            "#accommodation-quality-list"
        );

        if (!container) {
            return;
        }

        const normalizedFlags = (
            Array.isArray(flags)
                ? flags
                    .map(
                        (flag, index) => {
                            return (
                                normalizeQualityFlag(
                                    flag,
                                    index
                                )
                            );
                        }
                    )
                    .filter(Boolean)
                : []
        );

        if (
            normalizedFlags.length === 0
        ) {
            container.innerHTML = `
                <li
                    class="accommodation-quality-item"
                    data-severity="info"
                >
                    لا توجد ملاحظات جودة مسجلة.
                </li>
            `;

            return;
        }

        container.innerHTML = (
            normalizedFlags
                .map((flag) => {
                    return `
                        <li
                            class="accommodation-quality-item"
                            data-severity="${escapeHtml(
                                flag.severity
                            )}"
                        >
                            <div>
                                <strong>
                                    ${escapeHtml(
                                        flag.code
                                    )}
                                </strong>

                                <div>
                                    ${escapeHtml(
                                        flag.message
                                    )}
                                </div>
                            </div>
                        </li>
                    `;
                })
                .join("")
        );
    }


    function render(data) {
        state.data = data;
        state.error = null;

        const statusBadge = select(
            "#accommodation-status"
        );

        if (statusBadge) {
            statusBadge.dataset.status = (
                data.status
                || "warning"
            );

            statusBadge.textContent = (
                resolveStatusText(
                    data.status
                )
            );
        }

        setText(
            "#accommodation-year",
            data.year
        );

        renderInventory(
            data.inventory || {}
        );

        renderGuests(
            data.guests || {},
            data.indicators || {}
        );

        renderReadiness(
            data.readiness || {}
        );

        renderVerification(
            data.guests || {}
        );

        renderGuestChart(
            data.guests || {}
        );

        renderIndicators(
            data.indicators || {}
        );

        renderQualityFlags(
            data.quality_flags || []
        );
    }


    function renderError(error) {
        state.error = error;

        const statusBadge = select(
            "#accommodation-status"
        );

        if (statusBadge) {
            statusBadge.dataset.status =
                "error";

            statusBadge.textContent =
                "تعذر تحميل البيانات";
        }

        const indicatorContainer = select(
            "#accommodation-operational-grid"
        );

        if (indicatorContainer) {
            indicatorContainer.innerHTML = `
                <div class="accommodation-inline-error">
                    ${escapeHtml(
                        error?.message
                        || (
                            "تعذر الاتصال "
                            + "بخدمة الإيواء."
                        )
                    )}
                </div>
            `;
        }

        setText(
            "#accommodation-chart-status",
            "تعذر تحميل بيانات المخطط."
        );

        const verificationStatus = select(
            "#accommodation-verification-status"
        );

        if (verificationStatus) {
            verificationStatus.textContent =
                "تعذر الفحص";

            verificationStatus.classList.remove(
                "is-success",
                "is-warning"
            );

            verificationStatus.classList.add(
                "is-danger"
            );
        }
    }


    async function load() {
        if (state.loading) {
            return;
        }

        state.loading = true;

        try {
            const data = await (
                requestAccommodation()
            );

            render(data);

        } catch (error) {
            console.error(
                "[Accommodation Module]",
                error
            );

            renderError(error);

        } finally {
            state.loading = false;
        }
    }


    function registerEvents() {
        const refreshButton = select(
            "#refresh-button"
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


    const AccommodationDashboard = {
        initialize,

        reload:
            load,

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


    window.AccommodationDashboard = (
        AccommodationDashboard
    );


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

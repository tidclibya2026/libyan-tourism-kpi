/**
 * National Tourism Dashboard Configuration
 * Libyan Tourism Information & Documentation Center
 *
 * الملف المركزي لإعدادات الواجهة الأمامية:
 * - بيانات التطبيق.
 * - عنوان الخادم الخلفي.
 * - مسارات API.
 * - إعدادات الرسوم البيانية.
 * - إعدادات الخريطة.
 * - إعدادات التنسيق والواجهة.
 */

(function initializeDashboardConfiguration() {
    "use strict";

    /* =====================================================
       Internal helpers
    ====================================================== */

    /**
     * تجميد الكائنات بصورة متكررة لمنع تعديل
     * إعدادات النظام أثناء التشغيل.
     *
     * @param {Object} target
     * @returns {Object}
     */
    function deepFreeze(target) {
        if (
            target === null
            || typeof target !== "object"
            || Object.isFrozen(target)
        ) {
            return target;
        }

        Object.getOwnPropertyNames(target).forEach((propertyName) => {
            const propertyValue = target[propertyName];

            if (
                propertyValue !== null
                && (
                    typeof propertyValue === "object"
                    || typeof propertyValue === "function"
                )
            ) {
                deepFreeze(propertyValue);
            }
        });

        return Object.freeze(target);
    }


    /**
     * حذف الشرطة المائلة الأخيرة من الرابط.
     *
     * @param {string} value
     * @returns {string}
     */
    function removeTrailingSlash(value) {
        return String(value || "")
            .trim()
            .replace(/\/+$/, "");
    }


    /**
     * التحقق من أن القيمة تمثل رابط HTTP صالحًا.
     *
     * @param {string} value
     * @returns {boolean}
     */
    function isValidHttpUrl(value) {
        try {
            const parsedUrl = new URL(value);

            return (
                parsedUrl.protocol === "http:"
                || parsedUrl.protocol === "https:"
            );
        } catch (error) {
            return false;
        }
    }


    /**
     * قراءة قيمة من Query String.
     *
     * مثال:
     * ?api=http://127.0.0.1:8000
     *
     * @param {string} name
     * @returns {string|null}
     */
    function getQueryParameter(name) {
        const searchParams = new URLSearchParams(
            window.location.search
        );

        const value = searchParams.get(name);

        return value ? value.trim() : null;
    }


    /**
     * قراءة عنوان API المحفوظ محليًا.
     *
     * @returns {string|null}
     */
    function getStoredApiBaseUrl() {
        try {
            const storedValue = window.localStorage.getItem(
                "lntip_api_base_url"
            );

            if (
                storedValue
                && isValidHttpUrl(storedValue)
            ) {
                return removeTrailingSlash(storedValue);
            }
        } catch (error) {
            console.warn(
                "تعذر قراءة عنوان API من Local Storage.",
                error
            );
        }

        return null;
    }


    /**
     * تحديد عنوان Backend تلقائيًا.
     *
     * ترتيب الأولوية:
     * 1. المتغير window.LNTIP_API_BASE_URL.
     * 2. معامل الرابط ?api=.
     * 3. القيمة المحفوظة في Local Storage.
     * 4. الخادم المحلي أثناء التطوير.
     * 5. نفس نطاق الواجهة في بيئة الإنتاج.
     *
     * @returns {string}
     */
    function resolveApiBaseUrl() {
        const globalOverride = removeTrailingSlash(
            window.LNTIP_API_BASE_URL || ""
        );

        if (
            globalOverride
            && isValidHttpUrl(globalOverride)
        ) {
            return globalOverride;
        }

        const queryOverride = removeTrailingSlash(
            getQueryParameter("api") || ""
        );

        if (
            queryOverride
            && isValidHttpUrl(queryOverride)
        ) {
            return queryOverride;
        }

        const storedOverride = getStoredApiBaseUrl();

        if (storedOverride) {
            return storedOverride;
        }

        const hostname = window.location.hostname.toLowerCase();

        const localHosts = new Set([
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "::1",
        ]);

        if (
            localHosts.has(hostname)
            || window.location.protocol === "file:"
        ) {
            return "http://127.0.0.1:8000";
        }

        return removeTrailingSlash(window.location.origin);
    }


    /**
     * إنشاء رابط API كامل.
     *
     * @param {string} path
     * @returns {string}
     */
    function buildApiUrl(path) {
        const normalizedPath = String(path || "")
            .trim()
            .replace(/^\/+/, "");

        return `${API_BASE_URL}/${normalizedPath}`;
    }


    /**
     * تحويل قيمة إلى عدد صحيح آمن.
     *
     * @param {*} value
     * @param {number} fallback
     * @returns {number}
     */
    function toSafeInteger(value, fallback = 0) {
        const parsedValue = Number.parseInt(value, 10);

        return Number.isFinite(parsedValue)
            ? parsedValue
            : fallback;
    }


    /* =====================================================
       Runtime values
    ====================================================== */

    const API_BASE_URL = resolveApiBaseUrl();

    const REFERENCE_YEAR = toSafeInteger(
        getQueryParameter("year"),
        2025
    );

    const TOP_CITIES_LIMIT = Math.min(
        Math.max(
            toSafeInteger(
                getQueryParameter("top_cities"),
                10
            ),
            1
        ),
        20
    );

    const DEBUG_MODE = (
        getQueryParameter("debug") === "true"
        || window.location.hostname === "localhost"
        || window.location.hostname === "127.0.0.1"
    );


    /* =====================================================
       Application configuration
    ====================================================== */

    const DashboardConfig = {
        app: {
            id: "libyan-national-tourism-dashboard",
            shortName: "LNTIP",
            nameAr: "المنصة الوطنية الذكية للمؤشرات السياحية الليبية",
            nameEn: "Libyan National Tourism Intelligence Platform",

            dashboardNameAr: "لوحة المؤشرات السياحية الوطنية",
            dashboardNameEn: "National Tourism Dashboard",

            organizationAr: "مركز المعلومات والتوثيق السياحي",
            organizationEn:
                "Tourism Information and Documentation Center",

            ministryAr: "وزارة السياحة والصناعات التقليدية",
            countryAr: "دولة ليبيا",

            sloganAr: "من المعلومة إلى القرار",

            standard: "LTKS",
            version: "1.0.0",
            referenceYear: REFERENCE_YEAR,

            language: "ar",
            direction: "rtl",
            locale: "ar-LY",
            timeZone: "Africa/Tripoli",

            debug: DEBUG_MODE,
        },


        api: {
            baseUrl: API_BASE_URL,

            timeoutMilliseconds: 15000,
            retryAttempts: 2,
            retryDelayMilliseconds: 900,

            defaultHeaders: {
                Accept: "application/json",
                "Content-Type": "application/json",
            },

            endpoints: {
                home: buildApiUrl(""),

                health: buildApiUrl("api/health"),
                readiness: buildApiUrl("api/ready"),

                legacyKpis: buildApiUrl("api/kpis"),
                summary: buildApiUrl("api/summary"),

                nationalKpis: buildApiUrl(
                    "api/kpis/national"
                ),

                cities: buildApiUrl(
                    "api/kpis/cities"
                ),

                continents: buildApiUrl(
                    "api/kpis/continents"
                ),

                metadata: buildApiUrl(
                    "api/metadata"
                ),

                dashboard(topCities = TOP_CITIES_LIMIT) {
                    const safeLimit = Math.min(
                        Math.max(
                            toSafeInteger(topCities, 5),
                            1
                        ),
                        20
                    );

                    return buildApiUrl(
                        `api/kpis/dashboard`
                        + `?top_cities=${safeLimit}`
                    );
                },

                indicator(code) {
                    const safeCode = encodeURIComponent(
                        String(code || "").trim()
                    );

                    return buildApiUrl(
                        `api/kpis/indicator/${safeCode}`
                    );
                },

                city(cityId) {
                    const safeCityId = encodeURIComponent(
                        String(cityId || "").trim()
                    );

                    return buildApiUrl(
                        `api/kpis/cities/${safeCityId}`
                    );
                },
            },
        },


        dashboard: {
            topCitiesLimit: TOP_CITIES_LIMIT,

            refreshIntervalMilliseconds: 0,

            loadingMinimumDurationMilliseconds: 450,

            numberAnimationDurationMilliseconds: 850,

            sections: {
                overview: "overview",
                markets: "markets",
                cities: "cities",
                map: "map-section",
                dataQuality: "data-quality",
            },

            primaryIndicators: [
                {
                    code: "international_tourists",
                    elementId: "kpi-international-tourists",
                    fallbackValue: 0,
                },
                {
                    code: "accommodation_guests",
                    elementId: "kpi-accommodation-guests",
                    fallbackCodes: [
                        "hotel_guests",
                    ],
                    fallbackValue: 0,
                },
                {
                    code: "heritage_visitors",
                    elementId: "kpi-heritage-visitors",
                    fallbackValue: 0,
                },
                {
                    code: "air_passengers",
                    elementId: "kpi-air-passengers",
                    fallbackValue: 0,
                },
                {
                    code: "tourism_companies",
                    elementId: "kpi-tourism-companies",
                    fallbackValue: 0,
                },
                {
                    code: "flights_count",
                    elementId: "kpi-flights",
                    fallbackCodes: [
                        "flights",
                    ],
                    fallbackValue: 0,
                },
            ],
        },


        format: {
            locale: "ar-LY",

            integer: {
                maximumFractionDigits: 0,
            },

            decimal: {
                minimumFractionDigits: 0,
                maximumFractionDigits: 2,
            },

            percentage: {
                minimumFractionDigits: 0,
                maximumFractionDigits: 2,
            },

            currency: {
                style: "currency",
                currency: "LYD",
                currencyDisplay: "symbol",
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
            },

            compactNumber: {
                notation: "compact",
                compactDisplay: "short",
                maximumFractionDigits: 1,
            },

            date: {
                year: "numeric",
                month: "long",
                day: "numeric",
            },

            dateTime: {
                year: "numeric",
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
                hour12: false,
                timeZone: "Africa/Tripoli",
            },
        },


        charts: {
            animationDurationMilliseconds: 800,

            responsive: true,
            maintainAspectRatio: false,

            fontFamily:
                "'Segoe UI', Tahoma, Arial, sans-serif",

            textColor: "#526274",
            titleColor: "#0a2440",
            gridColor: "rgba(10, 36, 64, 0.08)",

            colors: {
                primary: "#174b7e",
                primaryLight: "#5593c7",
                primarySoft: "#c6dced",

                gold: "#c89b2d",
                goldLight: "#ecd384",

                success: "#2a9d70",
                warning: "#d99618",
                danger: "#d94b57",
                info: "#3692c1",

                libyans: "#174b7e",
                arabs: "#c89b2d",
                foreigners: "#2a9d70",

                continents: [
                    "#174b7e",
                    "#c89b2d",
                    "#2a9d70",
                    "#3692c1",
                    "#945f06",
                ],

                cities: [
                    "#10365d",
                    "#174b7e",
                    "#1d5f9e",
                    "#2877bd",
                    "#5593c7",
                    "#8bb8dd",
                    "#c89b2d",
                    "#ddb94f",
                    "#2a9d70",
                    "#3692c1",
                ],
            },

            defaults: {
                borderWidth: 2,
                borderRadius: 7,
                hoverBorderWidth: 3,
            },
        },


        map: {
            containerId: "tourism-map",

            defaultCenter: [
                27.0,
                17.0,
            ],

            defaultZoom: 5,
            minimumZoom: 4,
            maximumZoom: 15,

            tileLayer: {
                url:
                    "https://{s}.tile.openstreetmap.org/"
                    + "{z}/{x}/{y}.png",

                attribution:
                    "&copy; OpenStreetMap contributors",

                maximumZoom: 19,
            },

            marker: {
                minimumRadius: 7,
                maximumRadius: 30,

                fillColor: "#174b7e",
                strokeColor: "#ffffff",

                fillOpacity: 0.78,
                strokeOpacity: 1,
                strokeWeight: 2,
            },

            popup: {
                maximumWidth: 290,
                minimumWidth: 200,
            },
        },


        ui: {
            selectors: {
                loadingScreen: "#loading-screen",

                appStatus: "#app-status",
                appStatusText: "#app-status-text",

                errorBanner: "#error-banner",
                errorMessage: "#error-message",
                errorRetryButton: "#error-retry-button",

                refreshButton: "#refresh-button",
                printButton: "#print-button",
                dataYear: "#data-year",

                calculatedIndicatorsCount:
                    "#calculated-indicators-count",

                unavailableIndicatorsCount:
                    "#unavailable-indicators-count",

                reconciliationStatus:
                    "#reconciliation-status",

                executiveReferenceYear:
                    "#executive-reference-year",

                lastUpdate:
                    "#last-update",

                citiesTableBody:
                    "#cities-table-body",

                continentsChart:
                    "#continents-chart",

                guestMixChart:
                    "#guest-mix-chart",

                citiesChart:
                    "#cities-chart",

                qualitySystemStatus:
                    "#quality-system-status",

                qualityErrorsCount:
                    "#quality-errors-count",

                qualityWarningsCount:
                    "#quality-warnings-count",

                qualityCitiesMatch:
                    "#quality-cities-match",

                qualityContinentsMatch:
                    "#quality-continents-match",
            },

            statusText: {
                loading: "جاري الاتصال",
                online: "متصل بالخادم",
                healthy: "النظام يعمل",
                ready: "البيانات جاهزة",
                warning: "يعمل مع تحذيرات",
                offline: "الخادم غير متصل",
                error: "حدث خطأ",
            },

            messages: {
                loading:
                    "جاري تحميل بيانات المؤشرات السياحية.",

                loadFailed:
                    "تعذر تحميل بيانات لوحة المؤشرات.",

                apiUnavailable:
                    "تعذر الاتصال بالخادم الخلفي. "
                    + "تأكد من تشغيل FastAPI على المنفذ 8000.",

                invalidResponse:
                    "استجاب الخادم، لكن البيانات المستلمة "
                    + "ليست بالشكل المتوقع.",

                emptyCities:
                    "لا توجد بيانات مدن متاحة حاليًا.",

                emptyContinents:
                    "لا توجد بيانات أسواق قارية متاحة حاليًا.",

                refreshSuccess:
                    "تم تحديث بيانات لوحة المؤشرات.",

                printTitle:
                    "التقرير التنفيذي للمؤشرات السياحية الوطنية",
            },

            classes: {
                hidden: "is-hidden",
                active: "is-active",
                loading: "is-loading",
                skeleton: "is-skeleton",

                successText: "text-success",
                warningText: "text-warning",
                dangerText: "text-danger",
                mutedText: "text-muted",
            },
        },


        storage: {
            apiBaseUrl: "lntip_api_base_url",
            selectedYear: "lntip_selected_year",
            dashboardPreferences: "lntip_dashboard_preferences",
            lastSuccessfulUpdate:
                "lntip_last_successful_update",
        },


        development: {
            frontendUrl: "http://127.0.0.1:5500",
            backendUrl: "http://127.0.0.1:8000",
            swaggerUrl: `${API_BASE_URL}/docs`,
            openApiUrl: `${API_BASE_URL}/openapi.json`,
        },
    };


    /* =====================================================
       Publish configuration
    ====================================================== */

    deepFreeze(DashboardConfig);

    Object.defineProperty(
        window,
        "DashboardConfig",
        {
            value: DashboardConfig,
            writable: false,
            enumerable: true,
            configurable: false,
        }
    );


    /* =====================================================
       Development logging
    ====================================================== */

    if (DashboardConfig.app.debug) {
        console.groupCollapsed(
            "%cLNTIP Dashboard Configuration",
            "color:#174b7e;font-weight:bold;"
        );

        console.info(
            "API Base URL:",
            DashboardConfig.api.baseUrl
        );

        console.info(
            "Reference year:",
            DashboardConfig.app.referenceYear
        );

        console.info(
            "Top cities limit:",
            DashboardConfig.dashboard.topCitiesLimit
        );

        console.info(
            "Environment:",
            window.location.hostname
        );

        console.groupEnd();
    }
})();
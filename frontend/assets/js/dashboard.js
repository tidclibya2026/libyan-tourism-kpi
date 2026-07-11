/**
 * National Tourism Dashboard Controller
 * Libyan Tourism Information & Documentation Center
 *
 * مسؤوليات الملف:
 * - تحميل البيانات من FastAPI.
 * - إغلاق شاشة التحميل.
 * - تعبئة بطاقات المؤشرات.
 * - تعبئة جدول المدن.
 * - عرض حالة النظام وجودة البيانات.
 * - تشغيل الرسوم والخريطة عند توفر ملفاتها.
 */

(function initializeDashboardController() {
    "use strict";

    /* =====================================================
       Required modules
    ====================================================== */

    if (!window.DashboardConfig) {
        throw new Error(
            "DashboardConfig غير متاح. "
            + "يجب تحميل config.js قبل dashboard.js."
        );
    }

    const config = window.DashboardConfig;

    const state = {
        initialized: false,
        loading: false,
        bundle: null,
        lastError: null,
        loadedAt: null,
    };


    /* =====================================================
       DOM helpers
    ====================================================== */

    function select(selector) {
        if (!selector) {
            return null;
        }

        return document.querySelector(selector);
    }


    function setText(target, value) {
        const element = (
            typeof target === "string"
                ? select(target)
                : target
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


    function setHidden(target, hidden) {
        const element = (
            typeof target === "string"
                ? select(target)
                : target
        );

        if (!element) {
            return;
        }

        element.hidden = Boolean(hidden);
    }


    function toNumber(value, fallback = 0) {
        const numberValue = Number(value);

        return Number.isFinite(numberValue)
            ? numberValue
            : fallback;
    }


    function formatInteger(value) {
        return new Intl.NumberFormat(
            config.format.locale,
            config.format.integer
        ).format(
            toNumber(value, 0)
        );
    }


    function formatDecimal(value) {
        return new Intl.NumberFormat(
            config.format.locale,
            config.format.decimal
        ).format(
            toNumber(value, 0)
        );
    }


    function formatPercentage(value) {
        const numericValue = toNumber(
            value,
            0
        );

        return `${formatDecimal(numericValue)}%`;
    }


    function formatDateTime(value) {
        if (!value) {
            return "—";
        }

        const dateValue = new Date(value);

        if (
            Number.isNaN(
                dateValue.getTime()
            )
        ) {
            return "—";
        }

        return new Intl.DateTimeFormat(
            config.format.locale,
            config.format.dateTime
        ).format(dateValue);
    }


    /* =====================================================
       Loading screen
    ====================================================== */

    function showLoading() {
        const loadingScreen = select(
            config.ui.selectors.loadingScreen
        );

        state.loading = true;

        document.body.classList.add(
            config.ui.classes.loading
        );

        if (loadingScreen) {
            loadingScreen.hidden = false;

            loadingScreen.classList.remove(
                config.ui.classes.hidden
            );
        }
    }


    function hideLoading() {
        const loadingScreen = select(
            config.ui.selectors.loadingScreen
        );

        state.loading = false;

        document.body.classList.remove(
            config.ui.classes.loading
        );

        if (!loadingScreen) {
            return;
        }

        loadingScreen.classList.add(
            config.ui.classes.hidden
        );

        window.setTimeout(
            () => {
                loadingScreen.hidden = true;
            },
            320
        );
    }


    /* =====================================================
       Application status
    ====================================================== */

    function setApplicationStatus(
        status,
        customText = null
    ) {
        const statusElement = select(
            config.ui.selectors.appStatus
        );

        const statusTextElement = select(
            config.ui.selectors.appStatusText
        );

        const normalizedStatus = (
            status || "loading"
        );

        if (statusElement) {
            statusElement.dataset.status =
                normalizedStatus;
        }

        const statusText = (
            customText
            || config.ui.statusText[
                normalizedStatus
            ]
            || config.ui.statusText.loading
        );

        setText(
            statusTextElement,
            statusText
        );
    }


    /* =====================================================
       Error handling
    ====================================================== */

    function showError(error) {
        const errorBanner = select(
            config.ui.selectors.errorBanner
        );

        const errorMessage = select(
            config.ui.selectors.errorMessage
        );

        state.lastError = error;

        const message = (
            error?.message
            || config.ui.messages.loadFailed
        );

        setText(
            errorMessage,
            message
        );

        if (errorBanner) {
            errorBanner.hidden = false;
        }

        setApplicationStatus(
            "error"
        );

        console.error(
            "[LNTIP Dashboard]",
            error
        );
    }


    function clearError() {
        const errorBanner = select(
            config.ui.selectors.errorBanner
        );

        state.lastError = null;

        if (errorBanner) {
            errorBanner.hidden = true;
        }
    }


    /* =====================================================
       Indicator helpers
    ====================================================== */

    function buildIndicatorMap(
        dashboardData
    ) {
        const indicatorMap = new Map();

        const national = (
            dashboardData?.national
            || {}
        );

        const allIndicators = [
            ...(
                Array.isArray(
                    national.indicators
                )
                    ? national.indicators
                    : []
            ),
            ...(
                Array.isArray(
                    national.unavailable_indicators
                )
                    ? national.unavailable_indicators
                    : []
            ),
        ];

        allIndicators.forEach(
            (indicator) => {
                if (
                    indicator
                    && indicator.code
                ) {
                    indicatorMap.set(
                        indicator.code,
                        indicator
                    );
                }
            }
        );

        return indicatorMap;
    }


    function getIndicatorValue(
        indicatorMap,
        summary,
        indicatorDefinition
    ) {
        const candidateCodes = [
            indicatorDefinition.code,
            ...(
                indicatorDefinition
                    .fallbackCodes
                || []
            ),
        ];

        for (
            const code of candidateCodes
        ) {
            const indicator = indicatorMap.get(
                code
            );

            if (
                indicator
                && indicator.value !== null
                && typeof indicator.value
                    !== "undefined"
            ) {
                return indicator.value;
            }

            if (
                summary
                && summary[code] !== null
                && typeof summary[code]
                    !== "undefined"
            ) {
                return summary[code];
            }
        }

        return (
            indicatorDefinition.fallbackValue
            ?? 0
        );
    }


    /* =====================================================
       Primary KPI cards
    ====================================================== */

    function renderPrimaryIndicators(
        dashboardData,
        summary
    ) {
        const indicatorMap = buildIndicatorMap(
            dashboardData
        );

        config.dashboard.primaryIndicators.forEach(
            (definition) => {
                const target = document.getElementById(
                    definition.elementId
                );

                if (!target) {
                    return;
                }

                const value = getIndicatorValue(
                    indicatorMap,
                    summary,
                    definition
                );

                setText(
                    target,
                    formatInteger(value)
                );
            }
        );
    }


    /* =====================================================
       Executive strip
    ====================================================== */

    function renderExecutiveStrip(
        dashboardData,
        loadedAt
    ) {
        const national = (
            dashboardData?.national
            || {}
        );

        const calculatedIndicators = (
            Array.isArray(
                national.indicators
            )
                ? national.indicators
                : []
        );

        const unavailableIndicators = (
            Array.isArray(
                national.unavailable_indicators
            )
                ? national.unavailable_indicators
                : []
        );

        setText(
            config.ui.selectors
                .executiveReferenceYear,
            dashboardData?.reference_year
            || config.app.referenceYear
        );

        setText(
            config.ui.selectors
                .calculatedIndicatorsCount,
            formatInteger(
                calculatedIndicators.length
            )
        );

        setText(
            config.ui.selectors
                .unavailableIndicatorsCount,
            formatInteger(
                unavailableIndicators.length
            )
        );

        const reconciliationStatus =
            resolveReconciliationStatus(
                national.reconciliation
            );

        setText(
            config.ui.selectors
                .reconciliationStatus,
            reconciliationStatus.text
        );

        const reconciliationElement = select(
            config.ui.selectors
                .reconciliationStatus
        );

        if (reconciliationElement) {
            reconciliationElement.classList.remove(
                config.ui.classes.successText,
                config.ui.classes.warningText,
                config.ui.classes.dangerText
            );

            reconciliationElement.classList.add(
                reconciliationStatus.className
            );
        }

        setText(
            config.ui.selectors.lastUpdate,
            formatDateTime(loadedAt)
        );
    }


    function collectDifferences(value) {
        const differences = [];

        if (Array.isArray(value)) {
            value.forEach(
                (item) => {
                    differences.push(
                        ...collectDifferences(item)
                    );
                }
            );

            return differences;
        }

        if (
            value
            && typeof value === "object"
        ) {
            Object.entries(value).forEach(
                ([key, item]) => {
                    if (
                        key === "difference"
                        && Number.isFinite(
                            Number(item)
                        )
                    ) {
                        differences.push(
                            Number(item)
                        );
                    } else {
                        differences.push(
                            ...collectDifferences(
                                item
                            )
                        );
                    }
                }
            );
        }

        return differences;
    }


    function resolveReconciliationStatus(
        reconciliation
    ) {
        if (
            !reconciliation
            || typeof reconciliation
                !== "object"
        ) {
            return {
                text: "غير متاح",
                className:
                    config.ui.classes.mutedText,
            };
        }

        const directStatus = String(
            reconciliation.status
            || ""
        ).toLowerCase();

        if (
            [
                "matched",
                "valid",
                "success",
                "passed",
                "reconciled",
            ].includes(directStatus)
        ) {
            return {
                text: "متطابق",
                className:
                    config.ui.classes.successText,
            };
        }

        const differences = collectDifferences(
            reconciliation
        );

        if (differences.length === 0) {
            return {
                text: "تم الفحص",
                className:
                    config.ui.classes.successText,
            };
        }

        const allMatched = differences.every(
            (difference) => {
                return Math.abs(difference) < 0.001;
            }
        );

        return allMatched
            ? {
                text: "متطابق",
                className:
                    config.ui.classes.successText,
            }
            : {
                text: "توجد فروقات",
                className:
                    config.ui.classes.warningText,
            };
    }


    /* =====================================================
       Cities table
    ====================================================== */

    function renderCitiesTable(
        dashboardData
    ) {
        const tableBody = select(
            config.ui.selectors
                .citiesTableBody
        );

        if (!tableBody) {
            return;
        }

        const cities = (
            dashboardData?.cities
                ?.top_items
        );

        if (
            !Array.isArray(cities)
            || cities.length === 0
        ) {
            tableBody.innerHTML = `
                <tr>
                    <td
                        colspan="7"
                        class="table-empty-state"
                    >
                        ${config.ui.messages.emptyCities}
                    </td>
                </tr>
            `;

            return;
        }

        tableBody.innerHTML = "";

        cities.forEach(
            (city, index) => {
                const row = document.createElement(
                    "tr"
                );

                const rank = (
                    city.national_rank
                    || index + 1
                );

                const share = (
                    city.share_percent
                    ?? 0
                );

                row.innerHTML = `
                    <td>
                        ${formatInteger(rank)}
                    </td>

                    <td>
                        ${escapeHtml(
                            city.name_ar
                            || city.name_en
                            || city.id
                            || "—"
                        )}
                    </td>

                    <td>
                        ${formatInteger(
                            city.total_guests
                            ?? city.calculated_total_guests
                            ?? 0
                        )}
                    </td>

                    <td>
                        ${formatInteger(
                            city.libyans
                            ?? 0
                        )}
                    </td>

                    <td>
                        ${formatInteger(
                            city.arabs
                            ?? 0
                        )}
                    </td>

                    <td>
                        ${formatInteger(
                            city.foreigners
                            ?? 0
                        )}
                    </td>

                    <td>
                        ${formatPercentage(
                            share
                        )}
                    </td>
                `;

                tableBody.appendChild(row);
            }
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


    /* =====================================================
       Data quality
    ====================================================== */

    function renderDataQuality(
        dashboardData,
        health,
        readiness
    ) {
        const healthStatus = String(
            health?.status
            || (
                dashboardData
                    ? "healthy"
                    : "error"
            )
        ).toLowerCase();

        const validation = (
            readiness?.validation
            || readiness?.data
                ?.validation
            || {}
        );

        const errorsCount = toNumber(
            validation.errors_count
            ?? readiness?.errors_count,
            0
        );

        const warningsCount = toNumber(
            validation.warnings_count
            ?? readiness?.warnings_count,
            0
        );

        setText(
            config.ui.selectors
                .qualitySystemStatus,
            healthStatus.includes("healthy")
                ? "يعمل بصورة سليمة"
                : "يعمل مع ملاحظات"
        );

        setText(
            config.ui.selectors
                .qualityErrorsCount,
            formatInteger(errorsCount)
        );

        setText(
            config.ui.selectors
                .qualityWarningsCount,
            formatInteger(warningsCount)
        );

        const reconciliation = (
            dashboardData?.national
                ?.reconciliation
            || {}
        );

        const reconciliationText =
            resolveReconciliationStatus(
                reconciliation
            ).text;

        setText(
            config.ui.selectors
                .qualityCitiesMatch,
            reconciliationText
        );

        setText(
            config.ui.selectors
                .qualityContinentsMatch,
            reconciliationText
        );

        applyQualityCardStatus(
            config.ui.selectors
                .qualitySystemStatus,
            healthStatus.includes("healthy")
                ? "success"
                : "warning"
        );

        applyQualityCardStatus(
            config.ui.selectors
                .qualityErrorsCount,
            errorsCount === 0
                ? "success"
                : "error"
        );

        applyQualityCardStatus(
            config.ui.selectors
                .qualityWarningsCount,
            warningsCount === 0
                ? "success"
                : "warning"
        );
    }


    function applyQualityCardStatus(
        selector,
        status
    ) {
        const element = select(selector);

        const card = element?.closest(
            ".quality-card"
        );

        if (card) {
            card.dataset.status = status;
        }
    }


    /* =====================================================
       Optional chart and map modules
    ====================================================== */

    function renderOptionalVisuals(
        dashboardData,
        summary
    ) {
        if (
            window.DashboardCharts
            && typeof window.DashboardCharts
                .renderAll === "function"
        ) {
            try {
                window.DashboardCharts.renderAll({
                    dashboard: dashboardData,
                    summary,
                });
            } catch (error) {
                console.warn(
                    "تعذر رسم المخططات.",
                    error
                );
            }
        }

        if (
            window.DashboardMap
            && typeof window.DashboardMap
                .render === "function"
        ) {
            try {
                window.DashboardMap.render(
                    dashboardData?.cities
                        ?.top_items
                    || []
                );
            } catch (error) {
                console.warn(
                    "تعذر رسم الخريطة.",
                    error
                );
            }
        }
    }


    /* =====================================================
       Main data rendering
    ====================================================== */

    function renderDashboard(bundle) {
        const dashboardData = bundle.dashboard;
        const summary = bundle.summary || {};
        const health = bundle.health || {};
        const readiness = bundle.readiness || {};

        renderPrimaryIndicators(
            dashboardData,
            summary
        );

        renderExecutiveStrip(
            dashboardData,
            bundle.loadedAt
        );

        renderCitiesTable(
            dashboardData
        );

        renderDataQuality(
            dashboardData,
            health,
            readiness
        );

        renderOptionalVisuals(
            dashboardData,
            summary
        );

        const healthStatus = String(
            health.status || "healthy"
        ).toLowerCase();

        if (
            healthStatus.includes("warning")
            || bundle.partial
        ) {
            setApplicationStatus(
                "warning"
            );
        } else {
            setApplicationStatus(
                "online"
            );
        }
    }


    /* =====================================================
       Data loading
    ====================================================== */

    async function loadDashboard() {
        if (state.loading) {
            return;
        }

        if (!window.DashboardAPI) {
            showError(
                new Error(
                    "ملف api.js غير محمل أو فارغ."
                )
            );

            hideLoading();
            return;
        }

        const startedAt = performance.now();

        showLoading();
        clearError();

        setApplicationStatus(
            "loading"
        );

        try {
            const bundle = await (
                window.DashboardAPI
                    .getDashboardBundle({
                        topCities:
                            config.dashboard
                                .topCitiesLimit,
                        includeSummary: true,
                        includeHealth: true,
                        includeReadiness: true,
                    })
            );

            state.bundle = bundle;
            state.loadedAt = bundle.loadedAt;

            renderDashboard(bundle);

            try {
                window.localStorage.setItem(
                    config.storage
                        .lastSuccessfulUpdate,
                    bundle.loadedAt
                );
            } catch (storageError) {
                console.warn(
                    "تعذر حفظ وقت آخر تحديث.",
                    storageError
                );
            }

        } catch (error) {
            showError(error);

        } finally {
            const elapsed = (
                performance.now() - startedAt
            );

            const minimumDuration = (
                config.dashboard
                    .loadingMinimumDurationMilliseconds
                || 450
            );

            const remainingDuration = Math.max(
                minimumDuration - elapsed,
                0
            );

            window.setTimeout(
                hideLoading,
                remainingDuration
            );
        }
    }


    /* =====================================================
       Events
    ====================================================== */

    function registerEvents() {
        const refreshButton = select(
            config.ui.selectors.refreshButton
        );

        const retryButton = select(
            config.ui.selectors
                .errorRetryButton
        );

        const printButton = select(
            config.ui.selectors.printButton
        );

        if (refreshButton) {
            refreshButton.addEventListener(
                "click",
                loadDashboard
            );
        }

        if (retryButton) {
            retryButton.addEventListener(
                "click",
                loadDashboard
            );
        }

        if (printButton) {
            printButton.addEventListener(
                "click",
                () => {
                    window.print();
                }
            );
        }

        document.querySelectorAll(
            ".top-navigation__link"
        ).forEach(
            (link) => {
                link.addEventListener(
                    "click",
                    () => {
                        document.querySelectorAll(
                            ".top-navigation__link"
                        ).forEach(
                            (item) => {
                                item.classList.remove(
                                    config.ui.classes
                                        .active
                                );
                            }
                        );

                        link.classList.add(
                            config.ui.classes.active
                        );
                    }
                );
            }
        );
    }


    /* =====================================================
       Initialization
    ====================================================== */

    async function initialize() {
        if (state.initialized) {
            return;
        }

        state.initialized = true;

        registerEvents();

        await loadDashboard();
    }


    const DashboardApp = {
        initialize,
        reload: loadDashboard,

        getState() {
            return {
                ...state,
            };
        },
    };

    Object.freeze(DashboardApp);

    Object.defineProperty(
        window,
        "DashboardApp",
        {
            value: DashboardApp,
            writable: false,
            enumerable: true,
            configurable: false,
        }
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
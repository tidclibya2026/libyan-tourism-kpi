/**
 * National Tourism Dashboard API Client
 * Libyan Tourism Information & Documentation Center
 *
 * مسؤوليات الملف:
 * - الاتصال بخادم FastAPI.
 * - تطبيق مهلة زمنية على الطلبات.
 * - إعادة المحاولة عند الأخطاء المؤقتة.
 * - توحيد معالجة الأخطاء.
 * - توفير دوال جاهزة لجميع مسارات المنصة.
 */

(function initializeDashboardApi() {
    "use strict";

    /* =====================================================
       Configuration validation
    ====================================================== */

    if (!window.DashboardConfig) {
        throw new Error(
            "DashboardConfig is not available. "
            + "Load config.js before api.js."
        );
    }

    const config = window.DashboardConfig;
    const apiConfig = config.api;


    /* =====================================================
       Custom API error
    ====================================================== */

    class DashboardApiError extends Error {
        /**
         * @param {string} message
         * @param {Object} options
         */
        constructor(
            message,
            {
                status = 0,
                statusText = "",
                url = "",
                method = "GET",
                payload = null,
                cause = null,
                retryable = false,
                code = "API_ERROR",
            } = {}
        ) {
            super(message);

            this.name = "DashboardApiError";
            this.status = status;
            this.statusText = statusText;
            this.url = url;
            this.method = method;
            this.payload = payload;
            this.cause = cause;
            this.retryable = retryable;
            this.code = code;
            this.timestamp = new Date().toISOString();
        }

        /**
         * تحويل الخطأ إلى كائن قابل للعرض أو التسجيل.
         *
         * @returns {Object}
         */
        toJSON() {
            return {
                name: this.name,
                message: this.message,
                code: this.code,
                status: this.status,
                statusText: this.statusText,
                url: this.url,
                method: this.method,
                retryable: this.retryable,
                timestamp: this.timestamp,
                payload: this.payload,
            };
        }
    }


    /* =====================================================
       Internal helpers
    ====================================================== */

    /**
     * الانتظار لعدد محدد من المللي ثانية.
     *
     * @param {number} milliseconds
     * @returns {Promise<void>}
     */
    function sleep(milliseconds) {
        return new Promise((resolve) => {
            window.setTimeout(resolve, milliseconds);
        });
    }


    /**
     * التحقق من أن القيمة كائن عادي.
     *
     * @param {*} value
     * @returns {boolean}
     */
    function isPlainObject(value) {
        return (
            value !== null
            && typeof value === "object"
            && !Array.isArray(value)
        );
    }


    /**
     * التحقق من أن الاستجابة JSON صالحة.
     *
     * @param {*} payload
     * @param {string} endpointName
     * @returns {*}
     */
    function validateJsonPayload(
        payload,
        endpointName = "API"
    ) {
        if (
            payload === null
            || typeof payload === "undefined"
        ) {
            throw new DashboardApiError(
                `استجابة ${endpointName} فارغة.`,
                {
                    code: "EMPTY_RESPONSE",
                    retryable: false,
                }
            );
        }

        if (
            typeof payload !== "object"
        ) {
            throw new DashboardApiError(
                `استجابة ${endpointName} ليست JSON صالحًا.`,
                {
                    code: "INVALID_RESPONSE",
                    payload,
                    retryable: false,
                }
            );
        }

        return payload;
    }


    /**
     * استخراج رسالة خطأ مفهومة من استجابة Backend.
     *
     * @param {*} payload
     * @param {string} fallbackMessage
     * @returns {string}
     */
    function extractErrorMessage(
        payload,
        fallbackMessage
    ) {
        if (!payload) {
            return fallbackMessage;
        }

        if (typeof payload === "string") {
            return payload;
        }

        if (typeof payload.message_ar === "string") {
            return payload.message_ar;
        }

        if (typeof payload.message === "string") {
            return payload.message;
        }

        if (typeof payload.detail === "string") {
            return payload.detail;
        }

        if (isPlainObject(payload.detail)) {
            if (
                typeof payload.detail.message_ar
                === "string"
            ) {
                return payload.detail.message_ar;
            }

            if (
                typeof payload.detail.message
                === "string"
            ) {
                return payload.detail.message;
            }
        }

        if (Array.isArray(payload.detail)) {
            const validationMessages = payload.detail
                .map((item) => {
                    if (
                        item
                        && typeof item.msg === "string"
                    ) {
                        return item.msg;
                    }

                    return null;
                })
                .filter(Boolean);

            if (validationMessages.length > 0) {
                return validationMessages.join("، ");
            }
        }

        return fallbackMessage;
    }


    /**
     * تحديد ما إذا كان رمز HTTP يسمح بإعادة المحاولة.
     *
     * @param {number} statusCode
     * @returns {boolean}
     */
    function isRetryableStatus(statusCode) {
        return (
            statusCode === 408
            || statusCode === 425
            || statusCode === 429
            || statusCode === 500
            || statusCode === 502
            || statusCode === 503
            || statusCode === 504
        );
    }


    /**
     * التحقق من أن الطلب يمكن إعادة محاولته.
     *
     * @param {string} method
     * @returns {boolean}
     */
    function isRetryableMethod(method) {
        return [
            "GET",
            "HEAD",
            "OPTIONS",
        ].includes(
            String(method || "GET").toUpperCase()
        );
    }


    /**
     * إنشاء إعدادات Headers.
     *
     * @param {HeadersInit|undefined} customHeaders
     * @returns {Headers}
     */
    function buildHeaders(customHeaders) {
        const headers = new Headers(
            apiConfig.defaultHeaders || {}
        );

        if (customHeaders) {
            const incomingHeaders = new Headers(
                customHeaders
            );

            incomingHeaders.forEach(
                (value, key) => {
                    headers.set(key, value);
                }
            );
        }

        return headers;
    }


    /**
     * حساب زمن الانتظار قبل إعادة المحاولة.
     *
     * @param {number} attempt
     * @returns {number}
     */
    function getRetryDelay(attempt) {
        const baseDelay = Number(
            apiConfig.retryDelayMilliseconds
            || 900
        );

        const exponentialDelay = (
            baseDelay
            * Math.pow(2, attempt)
        );

        const randomJitter = Math.floor(
            Math.random() * 250
        );

        return exponentialDelay + randomJitter;
    }


    /**
     * تحويل الاستجابة إلى JSON مع معالجة الاستجابة الفارغة.
     *
     * @param {Response} response
     * @returns {Promise<*>}
     */
    async function parseResponsePayload(response) {
        if (
            response.status === 204
            || response.status === 205
        ) {
            return {};
        }

        const contentType = (
            response.headers.get("content-type")
            || ""
        ).toLowerCase();

        if (
            contentType.includes(
                "application/json"
            )
        ) {
            try {
                return await response.json();
            } catch (error) {
                throw new DashboardApiError(
                    "تعذر قراءة استجابة JSON من الخادم.",
                    {
                        status: response.status,
                        statusText: response.statusText,
                        url: response.url,
                        code: "JSON_PARSE_ERROR",
                        cause: error,
                        retryable: false,
                    }
                );
            }
        }

        const textPayload = await response.text();

        if (!textPayload.trim()) {
            return {};
        }

        try {
            return JSON.parse(textPayload);
        } catch (error) {
            return {
                message: textPayload,
            };
        }
    }


    /**
     * تسجيل معلومات التطوير فقط.
     *
     * @param  {...any} values
     */
    function debugLog(...values) {
        if (config.app.debug) {
            console.info(
                "[LNTIP API]",
                ...values
            );
        }
    }


    /**
     * تسجيل تحذير التطوير.
     *
     * @param  {...any} values
     */
    function debugWarn(...values) {
        if (config.app.debug) {
            console.warn(
                "[LNTIP API]",
                ...values
            );
        }
    }


    /* =====================================================
       Core request function
    ====================================================== */

    /**
     * تنفيذ طلب HTTP موحد.
     *
     * @param {string} url
     * @param {Object} options
     * @returns {Promise<*>}
     */
    async function request(
        url,
        {
            method = "GET",
            headers,
            body,
            timeoutMilliseconds =
                apiConfig.timeoutMilliseconds,
            retryAttempts =
                apiConfig.retryAttempts,
            validate = true,
            endpointName = "API",
            signal = null,
        } = {}
    ) {
        const normalizedMethod = String(
            method || "GET"
        ).toUpperCase();

        const maximumAttempts = (
            isRetryableMethod(normalizedMethod)
            ? Math.max(
                Number(retryAttempts || 0),
                0
            )
            : 0
        );

        let lastError = null;

        for (
            let attempt = 0;
            attempt <= maximumAttempts;
            attempt += 1
        ) {
            const abortController = new AbortController();

            let externalAbortHandler = null;

            if (signal) {
                if (signal.aborted) {
                    abortController.abort(
                        signal.reason
                    );
                } else {
                    externalAbortHandler = () => {
                        abortController.abort(
                            signal.reason
                        );
                    };

                    signal.addEventListener(
                        "abort",
                        externalAbortHandler,
                        {
                            once: true,
                        }
                    );
                }
            }

            const timeoutId = window.setTimeout(
                () => {
                    abortController.abort(
                        new DOMException(
                            "Request timed out.",
                            "TimeoutError"
                        )
                    );
                },
                Number(timeoutMilliseconds)
            );

            const requestOptions = {
                method: normalizedMethod,
                headers: buildHeaders(headers),
                signal: abortController.signal,
                cache: "no-store",
                credentials: "same-origin",
            };

            if (
                typeof body !== "undefined"
                && body !== null
            ) {
                requestOptions.body = (
                    typeof body === "string"
                    || body instanceof FormData
                    || body instanceof Blob
                    ? body
                    : JSON.stringify(body)
                );

                if (
                    body instanceof FormData
                ) {
                    requestOptions.headers.delete(
                        "Content-Type"
                    );
                }
            }

            const startedAt = performance.now();

            try {
                debugLog(
                    `${normalizedMethod} ${url}`,
                    {
                        attempt:
                            attempt + 1,
                    }
                );

                const response = await fetch(
                    url,
                    requestOptions
                );

                const payload = await parseResponsePayload(
                    response
                );

                const elapsedMilliseconds = Math.round(
                    performance.now() - startedAt
                );

                debugLog(
                    `${response.status} ${url}`,
                    {
                        elapsedMilliseconds,
                    }
                );

                if (!response.ok) {
                    const fallbackMessage = (
                        `فشل الطلب برمز `
                        + `${response.status}.`
                    );

                    const message = extractErrorMessage(
                        payload,
                        fallbackMessage
                    );

                    const retryable = (
                        isRetryableMethod(
                            normalizedMethod
                        )
                        && isRetryableStatus(
                            response.status
                        )
                    );

                    throw new DashboardApiError(
                        message,
                        {
                            status:
                                response.status,
                            statusText:
                                response.statusText,
                            url,
                            method:
                                normalizedMethod,
                            payload,
                            retryable,
                            code:
                                "HTTP_ERROR",
                        }
                    );
                }

                return validate
                    ? validateJsonPayload(
                        payload,
                        endpointName
                    )
                    : payload;

            } catch (error) {
                if (
                    error instanceof DashboardApiError
                ) {
                    lastError = error;
                } else if (
                    error
                    && error.name === "AbortError"
                ) {
                    const timeoutError = (
                        !signal
                        || !signal.aborted
                    );

                    lastError = new DashboardApiError(
                        timeoutError
                            ? "انتهت مهلة الاتصال بالخادم."
                            : "تم إلغاء الطلب.",
                        {
                            status: 0,
                            url,
                            method:
                                normalizedMethod,
                            cause: error,
                            retryable:
                                timeoutError,
                            code:
                                timeoutError
                                    ? "REQUEST_TIMEOUT"
                                    : "REQUEST_ABORTED",
                        }
                    );
                } else {
                    lastError = new DashboardApiError(
                        config.ui.messages
                            .apiUnavailable,
                        {
                            status: 0,
                            url,
                            method:
                                normalizedMethod,
                            cause: error,
                            retryable: true,
                            code:
                                "NETWORK_ERROR",
                        }
                    );
                }

                const canRetry = (
                    attempt < maximumAttempts
                    && lastError.retryable
                );

                debugWarn(
                    lastError.message,
                    {
                        attempt:
                            attempt + 1,
                        canRetry,
                        error:
                            lastError.toJSON(),
                    }
                );

                if (!canRetry) {
                    throw lastError;
                }

                await sleep(
                    getRetryDelay(attempt)
                );

            } finally {
                window.clearTimeout(timeoutId);

                if (
                    signal
                    && externalAbortHandler
                ) {
                    signal.removeEventListener(
                        "abort",
                        externalAbortHandler
                    );
                }
            }
        }

        throw (
            lastError
            || new DashboardApiError(
                "تعذر تنفيذ الطلب.",
                {
                    url,
                    method:
                        normalizedMethod,
                }
            )
        );
    }


    /* =====================================================
       API endpoint functions
    ====================================================== */

    /**
     * بطاقة تعريف التطبيق.
     *
     * @returns {Promise<Object>}
     */
    function getHome() {
        return request(
            apiConfig.endpoints.home,
            {
                endpointName:
                    "بطاقة التطبيق",
            }
        );
    }


    /**
     * فحص صحة النظام.
     *
     * @returns {Promise<Object>}
     */
    function getHealth() {
        return request(
            apiConfig.endpoints.health,
            {
                endpointName:
                    "فحص صحة النظام",
            }
        );
    }


    /**
     * فحص جاهزية البيانات.
     *
     * @returns {Promise<Object>}
     */
    function getReadiness() {
        return request(
            apiConfig.endpoints.readiness,
            {
                endpointName:
                    "فحص جاهزية البيانات",
            }
        );
    }


    /**
     * البيانات القديمة المتوافقة.
     *
     * @returns {Promise<Object>}
     */
    function getLegacyKpis() {
        return request(
            apiConfig.endpoints.legacyKpis,
            {
                endpointName:
                    "البيانات السياحية الأساسية",
            }
        );
    }


    /**
     * الملخص الوطني.
     *
     * @returns {Promise<Object>}
     */
    function getSummary() {
        return request(
            apiConfig.endpoints.summary,
            {
                endpointName:
                    "الملخص الوطني",
            }
        );
    }


    /**
     * المؤشرات الوطنية الكاملة.
     *
     * @returns {Promise<Object>}
     */
    function getNationalKpis() {
        return request(
            apiConfig.endpoints.nationalKpis,
            {
                endpointName:
                    "المؤشرات الوطنية",
            }
        );
    }


    /**
     * حساب مؤشر واحد.
     *
     * @param {string} code
     * @returns {Promise<Object>}
     */
    function getIndicator(code) {
        const normalizedCode = String(
            code || ""
        ).trim();

        if (!normalizedCode) {
            return Promise.reject(
                new DashboardApiError(
                    "رمز المؤشر مطلوب.",
                    {
                        code:
                            "INVALID_INDICATOR_CODE",
                        retryable: false,
                    }
                )
            );
        }

        return request(
            apiConfig.endpoints.indicator(
                normalizedCode
            ),
            {
                endpointName:
                    `المؤشر ${normalizedCode}`,
            }
        );
    }


    /**
     * مؤشرات جميع المدن.
     *
     * @returns {Promise<Object>}
     */
    function getCities() {
        return request(
            apiConfig.endpoints.cities,
            {
                endpointName:
                    "مؤشرات المدن",
            }
        );
    }


    /**
     * مؤشرات مدينة واحدة.
     *
     * @param {string} cityId
     * @returns {Promise<Object>}
     */
    function getCity(cityId) {
        const normalizedCityId = String(
            cityId || ""
        ).trim();

        if (!normalizedCityId) {
            return Promise.reject(
                new DashboardApiError(
                    "معرف المدينة مطلوب.",
                    {
                        code:
                            "INVALID_CITY_ID",
                        retryable: false,
                    }
                )
            );
        }

        return request(
            apiConfig.endpoints.city(
                normalizedCityId
            ),
            {
                endpointName:
                    `المدينة ${normalizedCityId}`,
            }
        );
    }


    /**
     * توزيع القارات.
     *
     * @returns {Promise<Object>}
     */
    function getContinents() {
        return request(
            apiConfig.endpoints.continents,
            {
                endpointName:
                    "الأسواق حسب القارات",
            }
        );
    }


    /**
     * سجل المؤشرات والمصادر.
     *
     * @returns {Promise<Object>}
     */
    function getMetadata() {
        return request(
            apiConfig.endpoints.metadata,
            {
                endpointName:
                    "بيانات التعريف",
            }
        );
    }


    /**
     * حزمة Dashboard الأساسية.
     *
     * @param {number} topCities
     * @returns {Promise<Object>}
     */
    function getDashboard(
        topCities = config.dashboard
            .topCitiesLimit
    ) {
        return request(
            apiConfig.endpoints.dashboard(
                topCities
            ),
            {
                endpointName:
                    "حزمة لوحة المؤشرات",
            }
        );
    }


    /**
     * تحميل الحزمة التنفيذية الكاملة.
     *
     * تجمع:
     * - Dashboard
     * - Summary
     * - Health
     * - Readiness
     *
     * @param {Object} options
     * @returns {Promise<Object>}
     */
    async function getDashboardBundle({
        topCities = config.dashboard
            .topCitiesLimit,
        includeSummary = true,
        includeHealth = true,
        includeReadiness = true,
    } = {}) {
        const requestEntries = [
            [
                "dashboard",
                getDashboard(topCities),
            ],
        ];

        if (includeSummary) {
            requestEntries.push([
                "summary",
                getSummary(),
            ]);
        }

        if (includeHealth) {
            requestEntries.push([
                "health",
                getHealth(),
            ]);
        }

        if (includeReadiness) {
            requestEntries.push([
                "readiness",
                getReadiness(),
            ]);
        }

        const settledResults = await Promise.allSettled(
            requestEntries.map(
                ([, promise]) => promise
            )
        );

        const bundle = {};
        const errors = {};

        settledResults.forEach(
            (result, index) => {
                const key = requestEntries[
                    index
                ][0];

                if (
                    result.status
                    === "fulfilled"
                ) {
                    bundle[key] = result.value;
                } else {
                    errors[key] = (
                        result.reason
                        instanceof DashboardApiError
                        ? result.reason.toJSON()
                        : {
                            message:
                                String(
                                    result.reason
                                ),
                        }
                    );
                }
            }
        );

        if (!bundle.dashboard) {
            const primaryError = errors.dashboard;

            throw new DashboardApiError(
                primaryError?.message
                || config.ui.messages
                    .loadFailed,
                {
                    status:
                        primaryError?.status
                        || 0,
                    payload: errors,
                    retryable: true,
                    code:
                        "DASHBOARD_BUNDLE_FAILED",
                }
            );
        }

        return {
            ...bundle,
            errors,
            loadedAt:
                new Date().toISOString(),
            partial:
                Object.keys(errors).length > 0,
        };
    }


    /* =====================================================
       API base URL storage helpers
    ====================================================== */

    /**
     * حفظ عنوان API لاستخدامه عند إعادة تحميل الصفحة.
     *
     * يتطلب Reload لأن DashboardConfig مجمد.
     *
     * @param {string} baseUrl
     * @returns {boolean}
     */
    function saveApiBaseUrl(baseUrl) {
        const normalizedUrl = String(
            baseUrl || ""
        )
            .trim()
            .replace(/\/+$/, "");

        try {
            const parsedUrl = new URL(
                normalizedUrl
            );

            if (
                ![
                    "http:",
                    "https:",
                ].includes(
                    parsedUrl.protocol
                )
            ) {
                return false;
            }

            window.localStorage.setItem(
                config.storage.apiBaseUrl,
                normalizedUrl
            );

            return true;

        } catch (error) {
            return false;
        }
    }


    /**
     * حذف عنوان API المحفوظ.
     */
    function clearStoredApiBaseUrl() {
        try {
            window.localStorage.removeItem(
                config.storage.apiBaseUrl
            );
        } catch (error) {
            debugWarn(
                "تعذر حذف عنوان API المحفوظ.",
                error
            );
        }
    }


    /* =====================================================
       Public API
    ====================================================== */

    const DashboardAPI = {
        version: "1.0.0",

        baseUrl: apiConfig.baseUrl,

        DashboardApiError,

        request,

        getHome,
        getHealth,
        getReadiness,

        getLegacyKpis,
        getSummary,
        getNationalKpis,
        getIndicator,

        getCities,
        getCity,
        getContinents,

        getMetadata,

        getDashboard,
        getDashboardBundle,

        saveApiBaseUrl,
        clearStoredApiBaseUrl,
    };

    Object.freeze(DashboardAPI);

    Object.defineProperty(
        window,
        "DashboardAPI",
        {
            value: DashboardAPI,
            writable: false,
            enumerable: true,
            configurable: false,
        }
    );


    /* =====================================================
       Development logging
    ====================================================== */

    if (config.app.debug) {
        console.info(
            "[LNTIP API] Client ready:",
            DashboardAPI.baseUrl
        );
    }
})();
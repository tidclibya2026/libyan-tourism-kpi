/**
 * National Tourism Dashboard Map
 * Libyan Tourism Information & Documentation Center
 *
 * مسؤوليات الملف:
 * - إنشاء خريطة Leaflet التفاعلية.
 * - عرض المدن والفروع السياحية.
 * - تمثيل إجمالي النزلاء بحجم العلامة.
 * - عرض بيانات المدينة في نافذة منبثقة.
 * - تحديث الخريطة عند تحديث بيانات Dashboard.
 * - التعامل مع نقص الإحداثيات أو تعذر تحميل Leaflet.
 */

(function initializeDashboardMap() {
    "use strict";

    /* =====================================================
       Required configuration
    ====================================================== */

    if (!window.DashboardConfig) {
        throw new Error(
            "DashboardConfig غير متاح. "
            + "يجب تحميل config.js قبل map.js."
        );
    }

    const config = window.DashboardConfig;
    const mapConfig = config.map;

    const state = {
        map: null,
        tileLayer: null,
        markersLayer: null,
        legendControl: null,
        currentCities: [],
        initialized: false,
    };


    /* =====================================================
       Fallback geographic coordinates
    ====================================================== */

    /**
     * إحداثيات تقريبية لمراكز الفروع والمدن.
     *
     * تستخدم فقط عندما لا تتوافر lat وlng
     * داخل بيانات المدينة القادمة من Backend.
     */
    const fallbackLocations = [
        {
            keys: [
                "tripoli",
                "طرابلس",
            ],
            lat: 32.8872,
            lng: 13.1913,
        },
        {
            keys: [
                "benghazi",
                "بنغازي",
            ],
            lat: 32.1167,
            lng: 20.0667,
        },
        {
            keys: [
                "almurqub",
                "al-murqub",
                "murqub",
                "المرقب",
                "الخمس",
            ],
            lat: 32.6486,
            lng: 14.2619,
        },
        {
            keys: [
                "middle",
                "central",
                "misrata",
                "الوسطى",
                "المنطقة الوسطى",
                "مصراتة",
            ],
            lat: 32.3754,
            lng: 15.0925,
        },
        {
            keys: [
                "green_mountain",
                "green-mountain",
                "green mountain",
                "الجبل الأخضر",
                "البيضاء",
            ],
            lat: 32.7627,
            lng: 21.7551,
        },
        {
            keys: [
                "albutnan",
                "al-butnan",
                "butnan",
                "البطنان",
                "طبرق",
            ],
            lat: 32.0836,
            lng: 23.9764,
        },
        {
            keys: [
                "western",
                "west",
                "الغربية",
                "المنطقة الغربية",
                "الزاوية",
            ],
            lat: 32.7522,
            lng: 12.7278,
        },
        {
            keys: [
                "jabal_nafusa",
                "jabal-nafusa",
                "nafusa",
                "جبل نفوسة",
                "الجبل الغربي",
                "غريان",
            ],
            lat: 32.1722,
            lng: 13.0203,
        },
        {
            keys: [
                "sabha",
                "sebha",
                "سبها",
                "الجنوبية",
                "الجنوب",
            ],
            lat: 27.0377,
            lng: 14.4283,
        },
        {
            keys: [
                "ghat",
                "غات",
                "الجنوب الغربي",
            ],
            lat: 24.9647,
            lng: 10.1728,
        },
        {
            keys: [
                "derna",
                "درنة",
            ],
            lat: 32.7670,
            lng: 22.6367,
        },
        {
            keys: [
                "ajdabiya",
                "اجدابيا",
                "أجدابيا",
            ],
            lat: 30.7554,
            lng: 20.2263,
        },
    ];


    /* =====================================================
       General helpers
    ====================================================== */

    /**
     * تحويل القيمة إلى رقم صالح.
     *
     * @param {*} value
     * @param {number|null} fallback
     * @returns {number|null}
     */
    function toNumber(
        value,
        fallback = 0
    ) {
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
     * تنسيق رقم صحيح.
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
     * تنسيق نسبة مئوية.
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
     * تنظيف النص قبل عرضه داخل HTML.
     *
     * @param {*} value
     * @returns {string}
     */
    function escapeHtml(value) {
        const element = document.createElement(
            "div"
        );

        element.textContent = String(
            value ?? ""
        );

        return element.innerHTML;
    }


    /**
     * تطبيع النص للمقارنة.
     *
     * @param {*} value
     * @returns {string}
     */
    function normalizeText(value) {
        return String(value || "")
            .trim()
            .toLowerCase()
            .replace(/[_-]+/g, " ")
            .replace(/\s+/g, " ");
    }


    /**
     * التحقق من توفر مكتبة Leaflet.
     *
     * @returns {boolean}
     */
    function isLeafletAvailable() {
        return (
            typeof window.L !== "undefined"
            && typeof window.L.map === "function"
        );
    }


    /**
     * الحصول على عنصر الخريطة.
     *
     * @returns {HTMLElement|null}
     */
    function getMapContainer() {
        return document.getElementById(
            mapConfig.containerId
        );
    }


    /**
     * تسجيل رسالة أثناء التطوير.
     *
     * @param  {...any} values
     */
    function debugLog(...values) {
        if (config.app.debug) {
            console.info(
                "[LNTIP Map]",
                ...values
            );
        }
    }


    /**
     * تسجيل تحذير أثناء التطوير.
     *
     * @param  {...any} values
     */
    function debugWarn(...values) {
        if (config.app.debug) {
            console.warn(
                "[LNTIP Map]",
                ...values
            );
        }
    }


    /* =====================================================
       Coordinate handling
    ====================================================== */

    /**
     * التحقق من صحة الإحداثيات.
     *
     * @param {*} lat
     * @param {*} lng
     * @returns {boolean}
     */
    function areValidCoordinates(
        lat,
        lng
    ) {
        const latitude = toNumber(
            lat,
            null
        );

        const longitude = toNumber(
            lng,
            null
        );

        return (
            latitude !== null
            && longitude !== null
            && latitude >= -90
            && latitude <= 90
            && longitude >= -180
            && longitude <= 180
        );
    }


    /**
     * البحث عن إحداثيات احتياطية.
     *
     * @param {Object} city
     * @returns {{lat:number, lng:number}|null}
     */
    function findFallbackCoordinates(city) {
        const candidateText = normalizeText(
            [
                city?.id,
                city?.name_ar,
                city?.name_en,
            ]
                .filter(Boolean)
                .join(" ")
        );

        if (!candidateText) {
            return null;
        }

        const location = fallbackLocations.find(
            (item) => {
                return item.keys.some(
                    (key) => {
                        return candidateText.includes(
                            normalizeText(key)
                        );
                    }
                );
            }
        );

        if (!location) {
            return null;
        }

        return {
            lat: location.lat,
            lng: location.lng,
        };
    }


    /**
     * استخراج إحداثيات المدينة.
     *
     * الأولوية:
     * 1. lat وlng من Backend.
     * 2. latitude وlongitude.
     * 3. الإحداثيات الاحتياطية.
     *
     * @param {Object} city
     * @returns {{lat:number, lng:number, source:string}|null}
     */
    function resolveCityCoordinates(city) {
        const directLatitude = (
            city?.lat
            ?? city?.latitude
        );

        const directLongitude = (
            city?.lng
            ?? city?.lon
            ?? city?.longitude
        );

        if (
            areValidCoordinates(
                directLatitude,
                directLongitude
            )
        ) {
            return {
                lat: Number(directLatitude),
                lng: Number(directLongitude),
                source: "data",
            };
        }

        const fallback = findFallbackCoordinates(
            city
        );

        if (fallback) {
            return {
                ...fallback,
                source: "fallback",
            };
        }

        return null;
    }


    /* =====================================================
       Map lifecycle
    ====================================================== */

    /**
     * عرض رسالة داخل منطقة الخريطة.
     *
     * @param {string} message
     */
    function showMapMessage(message) {
        const container = getMapContainer();

        if (!container) {
            return;
        }

        destroyMap();

        container.innerHTML = "";

        const messageElement = document.createElement(
            "div"
        );

        messageElement.className =
            "map-empty-message";

        messageElement.textContent = message;

        Object.assign(
            messageElement.style,
            {
                width: "100%",
                minHeight: "520px",
                display: "grid",
                placeItems: "center",
                padding: "30px",
                textAlign: "center",
                color: "#718094",
                background:
                    "linear-gradient(145deg, #e9f2f9, #eef3f8)",
                fontSize: "0.95rem",
            }
        );

        container.appendChild(
            messageElement
        );
    }


    /**
     * تنظيف محتوى عنصر الخريطة.
     */
    function clearMapContainer() {
        const container = getMapContainer();

        if (!container) {
            return;
        }

        container.innerHTML = "";
    }


    /**
     * إنشاء الخريطة للمرة الأولى.
     *
     * @returns {Object|null}
     */
    function createMap() {
        const container = getMapContainer();

        if (!container) {
            debugWarn(
                "عنصر الخريطة غير موجود."
            );

            return null;
        }

        if (!isLeafletAvailable()) {
            showMapMessage(
                "تعذر تحميل مكتبة الخريطة التفاعلية."
            );

            return null;
        }

        if (state.map) {
            return state.map;
        }

        clearMapContainer();

        state.map = window.L.map(
            container,
            {
                center:
                    mapConfig.defaultCenter,

                zoom:
                    mapConfig.defaultZoom,

                minZoom:
                    mapConfig.minimumZoom,

                maxZoom:
                    mapConfig.maximumZoom,

                zoomControl: true,
                attributionControl: true,

                scrollWheelZoom: true,
                doubleClickZoom: true,
                keyboard: true,
            }
        );

        state.tileLayer = window.L.tileLayer(
            mapConfig.tileLayer.url,
            {
                attribution:
                    mapConfig
                        .tileLayer
                        .attribution,

                maxZoom:
                    mapConfig
                        .tileLayer
                        .maximumZoom,

                detectRetina: true,
            }
        );

        state.tileLayer.addTo(
            state.map
        );

        state.markersLayer =
            window.L.layerGroup()
                .addTo(state.map);

        createLegend();

        state.initialized = true;

        window.setTimeout(
            () => {
                state.map?.invalidateSize();
            },
            120
        );

        return state.map;
    }


    /**
     * حذف الخريطة بالكامل.
     */
    function destroyMap() {
        if (state.map) {
            state.map.remove();
        }

        state.map = null;
        state.tileLayer = null;
        state.markersLayer = null;
        state.legendControl = null;
        state.initialized = false;
    }


    /**
     * حذف العلامات الحالية.
     */
    function clearMarkers() {
        if (state.markersLayer) {
            state.markersLayer.clearLayers();
        }
    }


    /* =====================================================
       Marker styling
    ====================================================== */

    /**
     * استخراج إجمالي النزلاء.
     *
     * @param {Object} city
     * @returns {number}
     */
    function getCityTotal(city) {
        return toNumber(
            city?.total_guests
            ?? city?.calculated_total_guests,
            0
        );
    }


    /**
     * حساب نصف قطر العلامة بصورة نسبية.
     *
     * @param {number} value
     * @param {number} maximumValue
     * @returns {number}
     */
    function calculateMarkerRadius(
        value,
        maximumValue
    ) {
        const minimumRadius = toNumber(
            mapConfig.marker.minimumRadius,
            7
        );

        const maximumRadius = toNumber(
            mapConfig.marker.maximumRadius,
            30
        );

        const safeValue = Math.max(
            toNumber(value, 0),
            0
        );

        const safeMaximum = Math.max(
            toNumber(maximumValue, 0),
            1
        );

        const normalizedValue = Math.sqrt(
            safeValue / safeMaximum
        );

        return (
            minimumRadius
            + normalizedValue
            * (
                maximumRadius
                - minimumRadius
            )
        );
    }


    /**
     * اختيار لون العلامة حسب ترتيب المدينة.
     *
     * @param {Object} city
     * @returns {string}
     */
    function getMarkerColor(city) {
        const rank = toNumber(
            city?.national_rank,
            999
        );

        if (rank === 1) {
            return config.charts.colors.gold;
        }

        if (rank <= 3) {
            return config.charts.colors.primary;
        }

        if (rank <= 6) {
            return config.charts.colors.info;
        }

        return config.charts.colors.success;
    }


    /* =====================================================
       Popup content
    ====================================================== */

    /**
     * إنشاء محتوى النافذة المنبثقة.
     *
     * @param {Object} city
     * @param {Object} coordinates
     * @returns {string}
     */
    function buildPopupContent(
        city,
        coordinates
    ) {
        const cityName = escapeHtml(
            city?.name_ar
            || city?.name_en
            || city?.id
            || "مدينة غير محددة"
        );

        const totalGuests = getCityTotal(
            city
        );

        const rank = toNumber(
            city?.national_rank,
            0
        );

        const share = toNumber(
            city?.share_percent,
            0
        );

        const fallbackNotice = (
            coordinates.source === "fallback"
                ? `
                    <p
                        style="
                            margin:8px 0 0;
                            padding-top:7px;
                            border-top:1px solid #e1e7ed;
                            font-size:0.68rem;
                            color:#945f06;
                        "
                    >
                        الموقع المعروض تقريبي لمركز الفرع.
                    </p>
                `
                : ""
        );

        return `
            <div
                class="map-popup"
                dir="rtl"
            >
                <p class="map-popup__title">
                    ${cityName}
                </p>

                <p
                    style="
                        margin:0 0 4px;
                        font-size:0.72rem;
                        color:#718094;
                    "
                >
                    الترتيب الوطني:
                    <strong>
                        ${rank > 0
                            ? formatInteger(rank)
                            : "—"}
                    </strong>
                </p>

                <div class="map-popup__value">
                    ${formatInteger(totalGuests)}
                </div>

                <p
                    style="
                        margin:0 0 10px;
                        font-size:0.72rem;
                        color:#718094;
                    "
                >
                    إجمالي النزلاء
                </p>

                <div
                    style="
                        display:grid;
                        grid-template-columns:1fr 1fr;
                        gap:5px 10px;
                        padding-top:8px;
                        border-top:1px solid #e1e7ed;
                        font-size:0.72rem;
                    "
                >
                    <span>
                        ليبيون
                    </span>

                    <strong>
                        ${formatInteger(
                            city?.libyans
                            ?? 0
                        )}
                    </strong>

                    <span>
                        عرب
                    </span>

                    <strong>
                        ${formatInteger(
                            city?.arabs
                            ?? 0
                        )}
                    </strong>

                    <span>
                        أجانب
                    </span>

                    <strong>
                        ${formatInteger(
                            city?.foreigners
                            ?? 0
                        )}
                    </strong>

                    <span>
                        الحصة الوطنية
                    </span>

                    <strong>
                        ${formatPercentage(
                            share
                        )}
                    </strong>
                </div>

                ${fallbackNotice}
            </div>
        `;
    }


    /* =====================================================
       Legend
    ====================================================== */

    /**
     * إنشاء مفتاح الخريطة.
     */
    function createLegend() {
        if (
            !state.map
            || !isLeafletAvailable()
        ) {
            return;
        }

        if (state.legendControl) {
            state.legendControl.remove();
        }

        state.legendControl = window.L.control({
            position: "bottomleft",
        });

        state.legendControl.onAdd = function onAddLegend() {
            const container = window.L.DomUtil.create(
                "div",
                "lntip-map-legend"
            );

            Object.assign(
                container.style,
                {
                    direction: "rtl",
                    minWidth: "180px",
                    padding: "10px 12px",
                    color: "#152435",
                    background:
                        "rgba(255,255,255,0.94)",
                    border:
                        "1px solid rgba(10,36,64,0.15)",
                    borderRadius: "10px",
                    boxShadow:
                        "0 7px 20px rgba(10,36,64,0.14)",
                    fontFamily:
                        config.charts.fontFamily,
                    fontSize: "11px",
                    lineHeight: "1.7",
                }
            );

            container.innerHTML = `
                <strong
                    style="
                        display:block;
                        margin-bottom:5px;
                        color:#0a2440;
                    "
                >
                    دلالة العلامات
                </strong>

                <div>
                    <span
                        style="
                            display:inline-block;
                            width:11px;
                            height:11px;
                            margin-left:6px;
                            background:${config.charts.colors.gold};
                            border-radius:50%;
                        "
                    ></span>

                    المدينة الأولى
                </div>

                <div>
                    <span
                        style="
                            display:inline-block;
                            width:11px;
                            height:11px;
                            margin-left:6px;
                            background:${config.charts.colors.primary};
                            border-radius:50%;
                        "
                    ></span>

                    المراكز الأعلى أداءً
                </div>

                <div>
                    <span
                        style="
                            display:inline-block;
                            width:11px;
                            height:11px;
                            margin-left:6px;
                            background:${config.charts.colors.info};
                            border-radius:50%;
                        "
                    ></span>

                    المراكز المتوسطة
                </div>

                <div
                    style="
                        margin-top:5px;
                        padding-top:5px;
                        border-top:1px solid #e1e7ed;
                        color:#718094;
                    "
                >
                    حجم الدائرة يعكس عدد النزلاء.
                </div>
            `;

            window.L.DomEvent.disableClickPropagation(
                container
            );

            return container;
        };

        state.legendControl.addTo(
            state.map
        );
    }


    /* =====================================================
       Map rendering
    ====================================================== */

    /**
     * تحويل قائمة المدن إلى مدن قابلة للرسم.
     *
     * @param {Array} cities
     * @returns {Array}
     */
    function prepareMappableCities(cities) {
        return toArray(cities)
            .map(
                (city) => {
                    const coordinates =
                        resolveCityCoordinates(
                            city
                        );

                    if (!coordinates) {
                        debugWarn(
                            "لا توجد إحداثيات للمدينة:",
                            city
                        );

                        return null;
                    }

                    return {
                        city,
                        coordinates,
                    };
                }
            )
            .filter(Boolean);
    }


    /**
     * رسم المدن على الخريطة.
     *
     * @param {Array} cities
     */
    function render(cities = []) {
        state.currentCities = toArray(
            cities
        );

        if (!isLeafletAvailable()) {
            showMapMessage(
                "تعذر تحميل مكتبة Leaflet. "
                + "تحقق من اتصال الإنترنت ثم أعد تحميل الصفحة."
            );

            return;
        }

        const map = createMap();

        if (!map) {
            return;
        }

        clearMarkers();

        const mappableCities =
            prepareMappableCities(
                state.currentCities
            );

        if (mappableCities.length === 0) {
            showMapMessage(
                "لا توجد إحداثيات جغرافية متاحة "
                + "للمدن والفروع السياحية."
            );

            return;
        }

        const maximumGuests = Math.max(
            ...mappableCities.map(
                ({ city }) => {
                    return getCityTotal(city);
                }
            ),
            1
        );

        const bounds = [];

        mappableCities.forEach(
            ({
                city,
                coordinates,
            }) => {
                const totalGuests =
                    getCityTotal(city);

                const radius =
                    calculateMarkerRadius(
                        totalGuests,
                        maximumGuests
                    );

                const markerColor =
                    getMarkerColor(city);

                const marker =
                    window.L.circleMarker(
                        [
                            coordinates.lat,
                            coordinates.lng,
                        ],
                        {
                            radius,

                            color:
                                mapConfig
                                    .marker
                                    .strokeColor,

                            weight:
                                mapConfig
                                    .marker
                                    .strokeWeight,

                            opacity:
                                mapConfig
                                    .marker
                                    .strokeOpacity,

                            fillColor:
                                markerColor,

                            fillOpacity:
                                mapConfig
                                    .marker
                                    .fillOpacity,

                            bubblingMouseEvents: true,
                        }
                    );

                marker.bindPopup(
                    buildPopupContent(
                        city,
                        coordinates
                    ),
                    {
                        maxWidth:
                            mapConfig
                                .popup
                                .maximumWidth,

                        minWidth:
                            mapConfig
                                .popup
                                .minimumWidth,

                        autoPan: true,
                        closeButton: true,
                    }
                );

                marker.bindTooltip(
                    `
                        <strong>
                            ${escapeHtml(
                                city?.name_ar
                                || city?.name_en
                                || city?.id
                                || "مدينة"
                            )}
                        </strong>
                        <br>
                        ${formatInteger(totalGuests)}
                        نزيل
                    `,
                    {
                        direction: "top",
                        offset: [0, -8],
                        opacity: 0.94,
                        sticky: true,
                    }
                );

                marker.addTo(
                    state.markersLayer
                );

                bounds.push([
                    coordinates.lat,
                    coordinates.lng,
                ]);
            }
        );

        if (bounds.length === 1) {
            map.setView(
                bounds[0],
                8
            );
        } else {
            map.fitBounds(
                window.L.latLngBounds(
                    bounds
                ),
                {
                    padding: [34, 34],
                    maxZoom: 7,
                }
            );
        }

        window.setTimeout(
            () => {
                map.invalidateSize();
            },
            160
        );

        debugLog(
            "تم رسم المدن:",
            mappableCities.length
        );
    }


    /**
     * إعادة الرسم باستخدام آخر بيانات.
     */
    function refresh() {
        render(
            state.currentCities
        );
    }


    /**
     * إعادة ضبط حجم الخريطة.
     */
    function invalidateSize() {
        if (!state.map) {
            return;
        }

        state.map.invalidateSize({
            animate: false,
        });
    }


    /**
     * إعادة الخريطة إلى نطاق جميع المدن.
     */
    function fitToCities() {
        if (
            !state.map
            || !state.markersLayer
        ) {
            return;
        }

        const markerLayers =
            state.markersLayer.getLayers();

        if (markerLayers.length === 0) {
            return;
        }

        const featureGroup =
            window.L.featureGroup(
                markerLayers
            );

        state.map.fitBounds(
            featureGroup.getBounds(),
            {
                padding: [34, 34],
                maxZoom: 7,
            }
        );
    }


    /**
     * فتح نافذة مدينة باستخدام معرفها.
     *
     * @param {string} cityId
     * @returns {boolean}
     */
    function focusCity(cityId) {
        if (
            !state.map
            || !state.markersLayer
        ) {
            return false;
        }

        const normalizedCityId =
            normalizeText(cityId);

        let matchedMarker = null;

        state.markersLayer.eachLayer(
            (layer) => {
                const popupContent =
                    layer.getPopup?.()
                        ?.getContent?.();

                if (
                    popupContent
                    && normalizeText(
                        popupContent
                    ).includes(
                        normalizedCityId
                    )
                ) {
                    matchedMarker = layer;
                }
            }
        );

        if (!matchedMarker) {
            return false;
        }

        state.map.setView(
            matchedMarker.getLatLng(),
            8,
            {
                animate: true,
            }
        );

        matchedMarker.openPopup();

        return true;
    }


    /* =====================================================
       Dashboard integration
    ====================================================== */

    /**
     * إعادة الرسم من حالة Dashboard الحالية.
     */
    function refreshFromDashboardState() {
        const dashboardState =
            window.DashboardApp
                ?.getState?.();

        const cities =
            dashboardState
                ?.bundle
                ?.dashboard
                ?.cities
                ?.top_items;

        if (!Array.isArray(cities)) {
            return;
        }

        render(cities);
    }


    /* =====================================================
       Public interface
    ====================================================== */

    const DashboardMap = {
        version: "1.0.0",

        render,
        refresh,
        destroy: destroyMap,

        invalidateSize,
        fitToCities,
        focusCity,

        refreshFromDashboardState,

        isAvailable:
            isLeafletAvailable,

        getState() {
            return {
                initialized:
                    state.initialized,

                citiesCount:
                    state.currentCities.length,

                mapAvailable:
                    Boolean(state.map),
            };
        },
    };

    Object.freeze(
        DashboardMap
    );

    Object.defineProperty(
        window,
        "DashboardMap",
        {
            value: DashboardMap,
            writable: false,
            enumerable: true,
            configurable: false,
        }
    );


    /* =====================================================
       Window events
    ====================================================== */

    let resizeTimer = null;

    window.addEventListener(
        "resize",
        () => {
            window.clearTimeout(
                resizeTimer
            );

            resizeTimer =
                window.setTimeout(
                    invalidateSize,
                    180
                );
        }
    );

    window.addEventListener(
        "beforeprint",
        () => {
            window.setTimeout(
                invalidateSize,
                100
            );
        }
    );


    /* =====================================================
       Development log
    ====================================================== */

    if (config.app.debug) {
        console.info(
            "[LNTIP Map] Module ready.",
            {
                leafletAvailable:
                    isLeafletAvailable(),
            }
        );
    }
})();
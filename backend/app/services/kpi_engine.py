"""
National Tourism KPI Engine.

محرك المؤشرات السياحية للمنصة الوطنية الذكية للمؤشرات السياحية الليبية.

المسؤوليات الحالية:
- تنفيذ العمليات الحسابية الإحصائية المشتركة بأمان.
- المحافظة على التوافق مع Routers الحالية.
- حساب المؤشرات الوطنية القابلة للاشتقاق من بيانات 2025.
- حساب حصص المدن والقارات وترتيبها.
- ربط نتائج الحساب بتعريفات السجل الوطني للمؤشرات.
- إظهار المؤشرات غير القابلة للحساب بدل اختلاق قيم لها.

مبدأ أمني ومنهجي مهم:
لا يتم استخدام eval لتنفيذ المعادلات النصية الموجودة في سجل المؤشرات.
كل معادلة قابلة للتنفيذ تُبرمج صراحة وتُختبر قبل اعتمادها.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from math import isfinite
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo

from app.services.data_service import (
    get_indicator,
    load_cities,
    load_continents,
    load_national_kpis,
)

JsonObject = dict[str, Any]
Numeric = int | float | Decimal

DEFAULT_ROUNDING = 2
DEFAULT_TIMEZONE = "Africa/Tripoli"


class KPIEngineError(ValueError):
    """خطأ موحد عند تعذر حساب مؤشر بسبب مدخلات غير صالحة."""


def _is_numeric(value: Any) -> bool:
    """التحقق من أن القيمة رقم حقيقي صالح، مع استبعاد Boolean وNaN وInfinity."""
    if isinstance(value, bool):
        return False

    if isinstance(value, Decimal):
        return value.is_finite()

    if isinstance(value, (int, float)):
        return isfinite(float(value))

    return False


def _to_decimal(
    value: Any,
    *,
    field_name: str = "value",
    default: Numeric | None = None,
) -> Decimal:
    """تحويل قيمة رقمية إلى Decimal مع رسالة خطأ واضحة."""
    if value is None and default is not None:
        value = default

    if not _is_numeric(value):
        raise KPIEngineError(
            f"القيمة {field_name} يجب أن تكون رقمًا صالحًا، والقيمة الحالية: {value!r}"
        )

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise KPIEngineError(
            f"تعذر تحويل {field_name} إلى قيمة رقمية: {value!r}"
        ) from exc


def _quantize(value: Decimal, rounding: int = DEFAULT_ROUNDING) -> Decimal:
    """تقريب Decimal وفق عدد المنازل المحدد بطريقة مالية مستقرة."""
    if rounding < 0:
        raise KPIEngineError("عدد المنازل العشرية لا يمكن أن يكون سالبًا.")

    quantum = Decimal("1") if rounding == 0 else Decimal("1").scaleb(-rounding)
    return value.quantize(quantum, rounding=ROUND_HALF_UP)


def _json_number(
    value: Decimal,
    *,
    rounding: int = DEFAULT_ROUNDING,
    prefer_integer: bool = False,
) -> int | float:
    """تحويل Decimal إلى رقم قابل للتسلسل بصيغة JSON."""
    rounded = _quantize(value, rounding)

    if prefer_integer or rounded == rounded.to_integral_value():
        return int(rounded)

    return float(rounded)


def _numeric_or_default(
    value: Any,
    *,
    field_name: str,
    default: Numeric = 0,
) -> Decimal:
    """قراءة قيمة رقمية اختيارية مع استخدام قيمة افتراضية عند غيابها."""
    return _to_decimal(
        default if value is None else value,
        field_name=field_name,
    )


def safe_sum(
    values: Iterable[Any],
    *,
    field_name: str = "values",
    rounding: int = DEFAULT_ROUNDING,
    prefer_integer: bool = False,
) -> int | float:
    """جمع قيم رقمية بعد التحقق منها."""
    total = Decimal("0")

    for index, value in enumerate(values):
        total += _to_decimal(
            value,
            field_name=f"{field_name}[{index}]",
        )

    return _json_number(
        total,
        rounding=rounding,
        prefer_integer=prefer_integer,
    )


def safe_divide(
    numerator: Any,
    denominator: Any,
    *,
    multiplier: Numeric = 1,
    rounding: int = DEFAULT_ROUNDING,
    zero_value: int | float | None = None,
) -> int | float | None:
    """
    قسمة آمنة تمنع القسمة على صفر.

    تعيد zero_value عند كون المقام صفرًا. القيمة الافتراضية None تتفق مع
    سياسة return_null المعتمدة في سجل المؤشرات.
    """
    numerator_decimal = _to_decimal(
        numerator,
        field_name="numerator",
    )
    denominator_decimal = _to_decimal(
        denominator,
        field_name="denominator",
    )
    multiplier_decimal = _to_decimal(
        multiplier,
        field_name="multiplier",
    )

    if denominator_decimal == 0:
        return zero_value

    result = (numerator_decimal / denominator_decimal) * multiplier_decimal
    return _json_number(result, rounding=rounding)


def percent(
    part: Any,
    total: Any,
    rounding: int = DEFAULT_ROUNDING,
) -> float:
    """
    حساب النسبة المئوية مع المحافظة على توافق الواجهات القديمة.

    عند المقام صفرًا تعاد 0.0 للواجهات الحالية. أما الحسابات الرسمية داخل
    calculate_national_kpis فتستخدم safe_divide مباشرة وتعيد None.
    """
    result = safe_divide(
        part,
        total,
        multiplier=100,
        rounding=rounding,
        zero_value=0.0,
    )
    return float(result or 0.0)


def ratio(
    numerator: Any,
    denominator: Any,
    rounding: int = DEFAULT_ROUNDING,
) -> int | float | None:
    """حساب نسبة عددية دون تحويلها إلى نسبة مئوية."""
    return safe_divide(
        numerator,
        denominator,
        multiplier=1,
        rounding=rounding,
        zero_value=None,
    )


def growth_rate(
    current_value: Any,
    previous_value: Any,
    rounding: int = DEFAULT_ROUNDING,
) -> int | float | None:
    """حساب معدل النمو بين فترتين كنسبة مئوية."""
    current = _to_decimal(current_value, field_name="current_value")
    previous = _to_decimal(previous_value, field_name="previous_value")

    if previous == 0:
        return None

    result = ((current - previous) / previous) * Decimal("100")
    return _json_number(result, rounding=rounding)


def compound_annual_growth_rate(
    start_value: Any,
    end_value: Any,
    years: int,
    rounding: int = DEFAULT_ROUNDING,
) -> int | float | None:
    """حساب معدل النمو السنوي المركب CAGR."""
    start = _to_decimal(start_value, field_name="start_value")
    end = _to_decimal(end_value, field_name="end_value")

    if years <= 0:
        raise KPIEngineError("عدد السنوات لحساب CAGR يجب أن يكون أكبر من صفر.")

    if start <= 0 or end < 0:
        return None

    result = ((float(end / start) ** (1 / years)) - 1) * 100
    return _json_number(Decimal(str(result)), rounding=rounding)


def growth_forecast(value: Any, rate: float, years: int) -> int | float:
    """
    توقع بسيط بالنمو المركب، مع المحافظة على التوافق مع forecast.py الحالي.

    هذه الدالة أداة سيناريو أولية وليست نموذجًا إحصائيًا رسميًا. لا تعتمد
    النتائج رسميًا قبل توفير سلسلة زمنية واختبار النموذج.
    """
    base_value = _to_decimal(value, field_name="value")
    rate_decimal = _to_decimal(rate, field_name="rate")

    if years < 0:
        raise KPIEngineError("عدد سنوات التنبؤ لا يمكن أن يكون سالبًا.")

    if rate_decimal <= Decimal("-1"):
        raise KPIEngineError("معدل النمو يجب أن يكون أكبر من -100%.")

    forecast = base_value * ((Decimal("1") + rate_decimal) ** years)
    prefer_integer = isinstance(value, int) and not isinstance(value, bool)

    return _json_number(
        forecast,
        rounding=0 if prefer_integer else DEFAULT_ROUNDING,
        prefer_integer=prefer_integer,
    )


def weighted_score(
    components: Mapping[str, Any],
    weights: Mapping[str, Any],
    *,
    rounding: int = DEFAULT_ROUNDING,
) -> int | float:
    """
    حساب مؤشر مركب موزون.

    يجب أن تتطابق أسماء المكونات مع أسماء الأوزان وأن يكون مجموع الأوزان
    أكبر من صفر. يتم تطبيع النتيجة على مجموع الأوزان الفعلي.
    """
    missing_components = sorted(set(weights) - set(components))
    if missing_components:
        raise KPIEngineError(
            "مكونات مفقودة للمؤشر المركب: " + ", ".join(missing_components)
        )

    weighted_total = Decimal("0")
    weights_total = Decimal("0")

    for key, weight_value in weights.items():
        component = _to_decimal(
            components[key],
            field_name=f"components.{key}",
        )
        weight = _to_decimal(
            weight_value,
            field_name=f"weights.{key}",
        )

        if weight < 0:
            raise KPIEngineError("أوزان المؤشر المركب لا يمكن أن تكون سالبة.")

        weighted_total += component * weight
        weights_total += weight

    if weights_total == 0:
        raise KPIEngineError("مجموع أوزان المؤشر المركب يساوي صفرًا.")

    return _json_number(
        weighted_total / weights_total,
        rounding=rounding,
    )


def _object_items(payload: JsonObject, field: str = "items") -> list[JsonObject]:
    """إرجاع قائمة آمنة تحتوي فقط على كائنات JSON."""
    items = payload.get(field, [])

    if not isinstance(items, list):
        raise KPIEngineError(f"الحقل {field} يجب أن يكون قائمة.")

    return [item for item in items if isinstance(item, dict)]


def _guest_components(record: Mapping[str, Any]) -> tuple[Decimal, Decimal, Decimal]:
    """قراءة مكونات النزلاء الثلاثة من سجل مدينة."""
    libyans = _numeric_or_default(
        record.get("libyans"),
        field_name="libyans",
    )
    arabs = _numeric_or_default(
        record.get("arabs"),
        field_name="arabs",
    )
    foreigners = _numeric_or_default(
        record.get("foreigners"),
        field_name="foreigners",
    )

    return libyans, arabs, foreigners


def city_metrics(city: JsonObject, national_total: Any) -> JsonObject:
    """
    حساب مؤشرات مدينة واحدة مع المحافظة على التوافق مع cities.py الحالي.
    """
    result = deepcopy(city)
    libyans, arabs, foreigners = _guest_components(city)
    calculated_total = libyans + arabs + foreigners

    declared_total = _numeric_or_default(
        city.get("total_guests"),
        field_name="total_guests",
        default=calculated_total,
    )

    total = declared_total
    warnings: list[str] = []

    if declared_total != calculated_total:
        warnings.append("guest_components_do_not_match_declared_total")

    result.update(
        {
            "total_guests": _json_number(total, rounding=0, prefer_integer=True),
            "calculated_total_guests": _json_number(
                calculated_total,
                rounding=0,
                prefer_integer=True,
            ),
            "share_percent": percent(total, national_total),
            "domestic_share_percent": percent(libyans, total),
            "arab_share_percent": percent(arabs, total),
            "foreign_share_percent": percent(foreigners, total),
            "calculation_warnings": warnings,
        }
    )

    return result


def continent_metrics(continent: JsonObject, international_total: Any) -> JsonObject:
    """حساب الحصة السوقية لقارة واحدة من إجمالي السياح الدوليين."""
    result = deepcopy(continent)
    tourists = _numeric_or_default(
        continent.get("tourists"),
        field_name="tourists",
    )

    result["tourists"] = _json_number(
        tourists,
        rounding=0,
        prefer_integer=True,
    )
    result["market_share_percent"] = percent(tourists, international_total)

    return result


def _indicator_result(
    code: str,
    *,
    value: Any,
    reference_year: int,
    calculation_status: str,
    calculation_method: str,
    inputs: JsonObject | None = None,
    notes: list[str] | None = None,
) -> JsonObject:
    """توحيد شكل نتيجة المؤشر وربطها بتعريف السجل الوطني."""
    definition = get_indicator(code=code) or {}
    calculation = definition.get("calculation", {})

    if not isinstance(calculation, dict):
        calculation = {}

    return {
        "indicator_id": definition.get("indicator_id"),
        "code": code,
        "name_ar": definition.get("name_ar", code),
        "name_en": definition.get("name_en", code),
        "category": definition.get("category"),
        "indicator_type": definition.get("indicator_type"),
        "measurement_unit": definition.get("measurement_unit"),
        "reference_year": reference_year,
        "value": value,
        "calculation_status": calculation_status,
        "calculation_method": calculation_method,
        "registered_formula": calculation.get("formula"),
        "inputs": inputs or {},
        "data_source_ids": definition.get("data_source_ids", []),
        "quality": definition.get("quality", {}),
        "publication": definition.get("publication", {}),
        "notes": notes or [],
    }


def _unavailable_indicator(
    code: str,
    *,
    reference_year: int,
    missing_inputs: list[str],
    note: str,
) -> JsonObject:
    """إنشاء نتيجة موحدة لمؤشر لا تتوفر مدخلاته بعد."""
    return _indicator_result(
        code,
        value=None,
        reference_year=reference_year,
        calculation_status="unavailable",
        calculation_method="not_calculated",
        inputs={"missing_inputs": missing_inputs},
        notes=[note],
    )


def calculate_city_kpis(city_id: str | None = None) -> JsonObject:
    """حساب مؤشرات جميع المدن أو مدينة محددة مع الترتيب الوطني."""
    payload = load_cities()
    cities = _object_items(payload)
    reference_year = int(payload.get("year", 0) or 0)

    national_total = sum(
        _numeric_or_default(
            city.get("total_guests"),
            field_name=f"cities.{city.get('id', 'unknown')}.total_guests",
        )
        for city in cities
    )

    calculated = [city_metrics(city, national_total) for city in cities]
    calculated.sort(
        key=lambda item: item.get("total_guests", 0),
        reverse=True,
    )

    for rank, item in enumerate(calculated, start=1):
        item["national_rank"] = rank

    if city_id is not None:
        normalized_id = city_id.strip().casefold()
        matched = next(
            (
                item
                for item in calculated
                if str(item.get("id", "")).casefold() == normalized_id
            ),
            None,
        )

        if matched is None:
            raise KPIEngineError(f"المدينة غير موجودة: {city_id}")

        return {
            "year": reference_year,
            "national_total_guests": _json_number(
                national_total,
                rounding=0,
                prefer_integer=True,
            ),
            "city": matched,
        }

    return {
        "year": reference_year,
        "national_total_guests": _json_number(
            national_total,
            rounding=0,
            prefer_integer=True,
        ),
        "cities_count": len(calculated),
        "items": calculated,
    }


def calculate_continent_kpis() -> JsonObject:
    """حساب توزيع السياح الدوليين والحصة السوقية حسب القارة."""
    payload = load_continents()
    continents = _object_items(payload)
    reference_year = int(payload.get("year", 0) or 0)

    calculated_total = sum(
        _numeric_or_default(
            item.get("tourists"),
            field_name=f"continents.{item.get('id', 'unknown')}.tourists",
        )
        for item in continents
    )

    items = [continent_metrics(item, calculated_total) for item in continents]
    items.sort(
        key=lambda item: item.get("tourists", 0),
        reverse=True,
    )

    for rank, item in enumerate(items, start=1):
        item["market_rank"] = rank

    return {
        "year": reference_year,
        "international_tourists_total": _json_number(
            calculated_total,
            rounding=0,
            prefer_integer=True,
        ),
        "continents_count": len(items),
        "items": items,
    }


def calculate_national_kpis() -> JsonObject:
    """
    حساب المؤشرات الوطنية المتاحة حاليًا من ملفات النواة.

    لا يحسب المحرك أي مؤشر لا تتوفر له مدخلات صحيحة. هذه السياسة تمنع
    تحويل التقديرات أو الافتراضات إلى أرقام رسمية دون سند إحصائي.
    """
    national = load_national_kpis()
    cities_payload = load_cities()
    continents_payload = load_continents()

    reference_year = int(national.get("year", 0) or 0)
    cities = _object_items(cities_payload)
    continents = _object_items(continents_payload)

    libyans_total = Decimal("0")
    arabs_total = Decimal("0")
    foreigners_total = Decimal("0")

    for city in cities:
        libyans, arabs, foreigners = _guest_components(city)
        libyans_total += libyans
        arabs_total += arabs
        foreigners_total += foreigners

    calculated_guest_total = libyans_total + arabs_total + foreigners_total

    international_tourists = _numeric_or_default(
        national.get("international_tourists"),
        field_name="international_tourists",
    )
    flights = _numeric_or_default(
        national.get("flights"),
        field_name="flights",
    )
    air_passengers = _numeric_or_default(
        national.get("air_passengers"),
        field_name="air_passengers",
    )

    direct_mapping = {
        "international_tourists": "international_tourists",
        "tourism_trips": "tourism_trips",
        "accommodation_guests": "hotel_guests",
        "hotels_count": "hotels",
        "hotel_apartments_count": "hotel_apartments",
        "tourist_villages_count": "tourist_villages",
        "rooms_count": "hotel_rooms",
        "beds_count": "hotel_beds",
        "tourism_companies_count": "tourism_companies",
        "handicrafts_count": "handicrafts",
        "restaurants_cafes_count": "restaurants_cafes",
        "flights_count": "flights",
        "air_passengers": "air_passengers",
        "heritage_visitors": "heritage_visitors",
    }

    indicators: list[JsonObject] = []

    for code, source_field in direct_mapping.items():
        raw_value = national.get(source_field)

        if raw_value is None:
            indicators.append(
                _unavailable_indicator(
                    code,
                    reference_year=reference_year,
                    missing_inputs=[source_field],
                    note="الحقل المطلوب غير متوفر في ملف المؤشرات الوطنية.",
                )
            )
            continue

        value_decimal = _to_decimal(raw_value, field_name=source_field)
        value = _json_number(
            value_decimal,
            rounding=0,
            prefer_integer=True,
        )

        indicators.append(
            _indicator_result(
                code,
                value=value,
                reference_year=reference_year,
                calculation_status="source_value",
                calculation_method="direct",
                inputs={source_field: value},
            )
        )

    derived_indicators = [
        _indicator_result(
            "domestic_guest_share",
            value=safe_divide(
                libyans_total,
                calculated_guest_total,
                multiplier=100,
                zero_value=None,
            ),
            reference_year=reference_year,
            calculation_status="calculated",
            calculation_method="ratio",
            inputs={
                "libyan_guests": _json_number(
                    libyans_total,
                    rounding=0,
                    prefer_integer=True,
                ),
                "accommodation_guests": _json_number(
                    calculated_guest_total,
                    rounding=0,
                    prefer_integer=True,
                ),
            },
        ),
        _indicator_result(
            "arab_guest_share",
            value=safe_divide(
                arabs_total,
                calculated_guest_total,
                multiplier=100,
                zero_value=None,
            ),
            reference_year=reference_year,
            calculation_status="calculated",
            calculation_method="ratio",
            inputs={
                "arab_guests": _json_number(
                    arabs_total,
                    rounding=0,
                    prefer_integer=True,
                ),
                "accommodation_guests": _json_number(
                    calculated_guest_total,
                    rounding=0,
                    prefer_integer=True,
                ),
            },
        ),
        _indicator_result(
            "foreign_guest_share",
            value=safe_divide(
                foreigners_total,
                calculated_guest_total,
                multiplier=100,
                zero_value=None,
            ),
            reference_year=reference_year,
            calculation_status="calculated",
            calculation_method="ratio",
            inputs={
                "foreign_guests": _json_number(
                    foreigners_total,
                    rounding=0,
                    prefer_integer=True,
                ),
                "accommodation_guests": _json_number(
                    calculated_guest_total,
                    rounding=0,
                    prefer_integer=True,
                ),
            },
        ),
        _indicator_result(
            "passengers_per_flight",
            value=safe_divide(
                air_passengers,
                flights,
                multiplier=1,
                zero_value=None,
            ),
            reference_year=reference_year,
            calculation_status="calculated",
            calculation_method="ratio",
            inputs={
                "air_passengers": _json_number(
                    air_passengers,
                    rounding=0,
                    prefer_integer=True,
                ),
                "flights_count": _json_number(
                    flights,
                    rounding=0,
                    prefer_integer=True,
                ),
            },
        ),
    ]
    indicators.extend(derived_indicators)

    continent_total = sum(
        _numeric_or_default(
            item.get("tourists"),
            field_name=f"continents.{item.get('id', 'unknown')}.tourists",
        )
        for item in continents
    )
    continent_shares = [
        continent_metrics(item, continent_total)
        for item in continents
    ]
    continent_shares.sort(
        key=lambda item: item.get("tourists", 0),
        reverse=True,
    )

    indicators.append(
        _indicator_result(
            "continent_market_share",
            value=continent_shares,
            reference_year=reference_year,
            calculation_status="calculated",
            calculation_method="ratio_by_dimension",
            inputs={
                "international_tourists": _json_number(
                    continent_total,
                    rounding=0,
                    prefer_integer=True,
                )
            },
        )
    )

    unavailable = [
        _unavailable_indicator(
            "annual_tourism_growth_rate",
            reference_year=reference_year,
            missing_inputs=["previous_year_value"],
            note="يحتاج المؤشر إلى سنة سابقة متجانسة منهجيًا.",
        ),
        _unavailable_indicator(
            "company_renewal_rate",
            reference_year=reference_year,
            missing_inputs=["companies_due_for_renewal"],
            note=(
                "لا يجوز استخدام إجمالي الشركات كمقام؛ المطلوب عدد الشركات "
                "المستحقة للتجديد فقط."
            ),
        ),
        _unavailable_indicator(
            "room_occupancy_rate",
            reference_year=reference_year,
            missing_inputs=[
                "occupied_room_nights",
                "available_room_nights",
            ],
            note="يحتاج المؤشر إلى بيانات تشغيل شهرية من منشآت الإيواء.",
        ),
        _unavailable_indicator(
            "tourist_nights",
            reference_year=reference_year,
            missing_inputs=["tourist_nights"],
            note="عدد الليالي السياحية غير متوفر في ملفات النواة الحالية.",
        ),
        _unavailable_indicator(
            "average_length_of_stay",
            reference_year=reference_year,
            missing_inputs=["tourist_nights"],
            note="لا يحسب متوسط الإقامة دون عدد الليالي السياحية.",
        ),
        _unavailable_indicator(
            "average_daily_rate",
            reference_year=reference_year,
            missing_inputs=["room_revenue_lyd", "occupied_room_nights"],
            note="بيانات إيرادات الغرف وليالي الغرف المباعة غير متوفرة.",
        ),
        _unavailable_indicator(
            "revenue_per_available_room",
            reference_year=reference_year,
            missing_inputs=["room_revenue_lyd", "available_room_nights"],
            note="بيانات إيرادات الغرف وليالي الغرف المتاحة غير متوفرة.",
        ),
        _unavailable_indicator(
            "tourism_gdp_share",
            reference_year=reference_year,
            missing_inputs=[
                "tourism_direct_gva",
                "gross_domestic_product",
            ],
            note="يتطلب المؤشر بيانات الحسابات القومية أو حساب السياحة الفرعي.",
        ),
    ]

    national_guest_value = national.get("hotel_guests")
    national_guest_decimal = (
        _to_decimal(national_guest_value, field_name="hotel_guests")
        if national_guest_value is not None
        else None
    )

    reconciliation = {
        "accommodation_guests": {
            "national_file_value": (
                _json_number(
                    national_guest_decimal,
                    rounding=0,
                    prefer_integer=True,
                )
                if national_guest_decimal is not None
                else None
            ),
            "cities_calculated_value": _json_number(
                calculated_guest_total,
                rounding=0,
                prefer_integer=True,
            ),
            "difference": (
                _json_number(
                    national_guest_decimal - calculated_guest_total,
                    rounding=0,
                    prefer_integer=True,
                )
                if national_guest_decimal is not None
                else None
            ),
        },
        "international_tourists": {
            "national_file_value": _json_number(
                international_tourists,
                rounding=0,
                prefer_integer=True,
            ),
            "continents_calculated_value": _json_number(
                continent_total,
                rounding=0,
                prefer_integer=True,
            ),
            "difference": _json_number(
                international_tourists - continent_total,
                rounding=0,
                prefer_integer=True,
            ),
        },
    }

    supplementary_metrics = {
        "hotels_and_apartments": national.get("hotels_and_apartments"),
        "chalets": national.get("chalets"),
        "renewed_companies": national.get("renewed_companies"),
        "summer_revenue_lyd": national.get("summer_revenue_lyd"),
    }

    return {
        "engine": {
            "name": "National Tourism KPI Engine",
            "version": "1.0.0",
            "standard": "LTKS",
            "calculated_at": datetime.now(
                ZoneInfo(DEFAULT_TIMEZONE)
            ).isoformat(),
        },
        "reference_year": reference_year,
        "status": "calculated",
        "calculated_indicators_count": len(indicators),
        "unavailable_indicators_count": len(unavailable),
        "indicators": indicators,
        "unavailable_indicators": unavailable,
        "reconciliation": reconciliation,
        "supplementary_metrics": supplementary_metrics,
    }


def calculate_indicator(code: str) -> JsonObject:
    """حساب مؤشر واحد بالرمز البرمجي من البيانات الحالية."""
    normalized_code = code.strip()
    if not normalized_code:
        raise KPIEngineError("رمز المؤشر مطلوب.")

    snapshot = calculate_national_kpis()

    for item in snapshot["indicators"]:
        if item.get("code") == normalized_code:
            return item

    for item in snapshot["unavailable_indicators"]:
        if item.get("code") == normalized_code:
            return item

    definition = get_indicator(code=normalized_code)
    if definition:
        return _unavailable_indicator(
            normalized_code,
            reference_year=snapshot["reference_year"],
            missing_inputs=["implementation_not_added"],
            note="تعريف المؤشر موجود، لكن معادلته التنفيذية لم تضاف بعد إلى المحرك.",
        )

    raise KPIEngineError(f"رمز المؤشر غير مسجل: {normalized_code}")


def calculate_dashboard_snapshot(top_cities: int = 5) -> JsonObject:
    """تجميع لقطة جاهزة للاستخدام لاحقًا في أول لوحة مؤشرات وطنية."""
    if top_cities < 1 or top_cities > 50:
        raise KPIEngineError("top_cities يجب أن يكون بين 1 و50.")

    national = calculate_national_kpis()
    cities = calculate_city_kpis()
    continents = calculate_continent_kpis()

    return {
        "engine": national["engine"],
        "reference_year": national["reference_year"],
        "national": {
            "indicators": national["indicators"],
            "unavailable_indicators": national["unavailable_indicators"],
            "reconciliation": national["reconciliation"],
            "supplementary_metrics": national["supplementary_metrics"],
        },
        "cities": {
            "national_total_guests": cities["national_total_guests"],
            "cities_count": cities["cities_count"],
            "top_items": cities["items"][:top_cities],
        },
        "continents": continents,
    }

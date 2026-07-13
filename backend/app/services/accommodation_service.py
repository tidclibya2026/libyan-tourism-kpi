"""
Accommodation analytics service for the
Libyan National Tourism Intelligence Platform.

مسؤوليات هذه الطبقة:
- تحميل بيانات الإيواء المعتمدة.
- حساب مؤشرات الطاقة الإيوائية المتاحة.
- حساب توزيع النزلاء حسب الجنسية.
- حساب مؤشرات التشغيل عند توافر مدخلاتها.
- منع إنتاج إشغال أو إيرادات تقديرية عند غياب البيانات.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any
from zoneinfo import ZoneInfo

from app.services.data_service import load_accommodation


JsonObject = dict[str, Any]

DEFAULT_TIMEZONE = "Africa/Tripoli"
DEFAULT_ROUNDING = 2


class AccommodationServiceError(ValueError):
    """
    خطأ موحد عند تعذر حساب مؤشرات الإيواء.
    """


def _is_number(value: Any) -> bool:
    """
    التحقق من أن القيمة رقمية، مع استبعاد Boolean.
    """
    return (
        isinstance(value, (int, float, Decimal))
        and not isinstance(value, bool)
    )


def _to_decimal(
    value: Any,
    *,
    field_name: str,
    allow_none: bool = False,
) -> Decimal | None:
    """
    تحويل قيمة إلى Decimal بصورة آمنة.
    """
    if value is None:
        if allow_none:
            return None

        raise AccommodationServiceError(
            f"القيمة المطلوبة غير متوفرة: {field_name}"
        )

    if not _is_number(value):
        raise AccommodationServiceError(
            f"القيمة {field_name} يجب أن تكون رقمية: {value!r}"
        )

    try:
        decimal_value = Decimal(str(value))

    except (InvalidOperation, ValueError) as exc:
        raise AccommodationServiceError(
            f"تعذر تحويل {field_name} إلى رقم."
        ) from exc

    if not decimal_value.is_finite():
        raise AccommodationServiceError(
            f"القيمة {field_name} ليست رقمًا منتهيًا."
        )

    return decimal_value


def _json_number(
    value: Decimal,
    *,
    rounding: int = DEFAULT_ROUNDING,
    prefer_integer: bool = False,
) -> int | float:
    """
    تحويل Decimal إلى قيمة صالحة لـJSON.
    """
    if rounding < 0:
        raise AccommodationServiceError(
            "عدد المنازل العشرية لا يمكن أن يكون سالبًا."
        )

    quantum = (
        Decimal("1")
        if rounding == 0
        else Decimal("1").scaleb(-rounding)
    )

    rounded = value.quantize(
        quantum,
        rounding=ROUND_HALF_UP,
    )

    if (
        prefer_integer
        or rounded == rounded.to_integral_value()
    ):
        return int(rounded)

    return float(rounded)


def _safe_divide(
    numerator: Any,
    denominator: Any,
    *,
    multiplier: int | float = 1,
    rounding: int = DEFAULT_ROUNDING,
) -> int | float | None:
    """
    قسمة آمنة تعيد None عند غياب المدخلات أو كون المقام صفرًا.
    """
    numerator_decimal = _to_decimal(
        numerator,
        field_name="numerator",
        allow_none=True,
    )

    denominator_decimal = _to_decimal(
        denominator,
        field_name="denominator",
        allow_none=True,
    )

    if (
        numerator_decimal is None
        or denominator_decimal is None
        or denominator_decimal == 0
    ):
        return None

    multiplier_decimal = _to_decimal(
        multiplier,
        field_name="multiplier",
    )

    assert multiplier_decimal is not None

    result = (
        numerator_decimal
        / denominator_decimal
    ) * multiplier_decimal

    return _json_number(
        result,
        rounding=rounding,
    )


def _require_mapping(
    payload: JsonObject,
    field: str,
) -> JsonObject:
    """
    قراءة كائن فرعي إلزامي.
    """
    value = payload.get(field)

    if not isinstance(value, dict):
        raise AccommodationServiceError(
            f"الحقل {field} يجب أن يكون كائن JSON."
        )

    return value


def _require_list(
    payload: JsonObject,
    field: str,
) -> list[Any]:
    """
    قراءة قائمة إلزامية.
    """
    value = payload.get(field)

    if not isinstance(value, list):
        raise AccommodationServiceError(
            f"الحقل {field} يجب أن يكون قائمة."
        )

    return value


def _missing_inputs(
    inputs: JsonObject,
) -> list[str]:
    """
    تحديد المدخلات غير المتوافرة.
    """
    return [
        name
        for name, value in inputs.items()
        if value is None
    ]


def _available_indicator(
    *,
    code: str,
    name_ar: str,
    value: int | float,
    unit: str,
    calculation_method: str,
    inputs: JsonObject,
    note_ar: str | None = None,
    quality_status: str = "calculated",
) -> JsonObject:
    """
    إنشاء نتيجة مؤشر متاح.
    """
    result: JsonObject = {
        "code": code,
        "name_ar": name_ar,
        "value": value,
        "unit": unit,
        "status": "available",
        "quality_status": quality_status,
        "calculation_method": calculation_method,
        "inputs": inputs,
        "missing_inputs": [],
    }

    if note_ar:
        result["note_ar"] = note_ar

    return result


def _unavailable_indicator(
    *,
    code: str,
    name_ar: str,
    unit: str,
    inputs: JsonObject,
    note_ar: str,
) -> JsonObject:
    """
    إنشاء نتيجة مؤشر غير متاح.
    """
    return {
        "code": code,
        "name_ar": name_ar,
        "value": None,
        "unit": unit,
        "status": "unavailable",
        "quality_status": "missing_operational_inputs",
        "calculation_method": "not_calculated",
        "inputs": inputs,
        "missing_inputs": _missing_inputs(inputs),
        "note_ar": note_ar,
    }


def _ratio_indicator(
    *,
    code: str,
    name_ar: str,
    numerator_name: str,
    numerator_value: Any,
    denominator_name: str,
    denominator_value: Any,
    unit: str,
    multiplier: int | float = 1,
    rounding: int = DEFAULT_ROUNDING,
    note_ar: str | None = None,
    quality_status: str = "calculated",
) -> JsonObject:
    """
    إنشاء مؤشر نسبة متاح أو غير متاح حسب المدخلات.
    """
    inputs = {
        numerator_name: numerator_value,
        denominator_name: denominator_value,
    }

    value = _safe_divide(
        numerator_value,
        denominator_value,
        multiplier=multiplier,
        rounding=rounding,
    )

    if value is None:
        return _unavailable_indicator(
            code=code,
            name_ar=name_ar,
            unit=unit,
            inputs=inputs,
            note_ar=(
                note_ar
                or "تعذر حساب المؤشر لعدم اكتمال المدخلات."
            ),
        )

    return _available_indicator(
        code=code,
        name_ar=name_ar,
        value=value,
        unit=unit,
        calculation_method="ratio",
        inputs=inputs,
        note_ar=note_ar,
        quality_status=quality_status,
    )


def calculate_accommodation_metrics() -> JsonObject:
    """
    حساب مؤشرات الإيواء المتاحة من ملف accommodation_2025.json.

    لا يتم احتساب:
    - الإشغال.
    - متوسط الإقامة.
    - متوسط سعر الغرفة ADR.
    - العائد على الغرفة المتاحة RevPAR.

    إلا عند توافر المدخلات التشغيلية الفعلية.
    """
    payload = load_accommodation()

    inventory = _require_mapping(
        payload,
        "inventory",
    )

    guests = _require_mapping(
        payload,
        "guests_reference",
    )

    operational = _require_mapping(
        payload,
        "operational_inputs",
    )

    quality_flags = _require_list(
        payload,
        "quality_flags",
    )

    hotels = inventory.get("hotels")
    apartments = inventory.get(
        "hotel_apartments"
    )
    hotels_and_apartments = inventory.get(
        "hotels_and_apartments"
    )
    tourist_villages = inventory.get(
        "tourist_villages"
    )
    chalets = inventory.get("chalets")
    rooms = inventory.get(
        "reported_rooms"
    )
    hotel_beds = inventory.get(
        "reported_hotel_beds"
    )
    chalet_beds = inventory.get(
        "reported_chalet_beds"
    )

    total_guests = guests.get(
        "total_guests"
    )
    libyan_guests = guests.get(
        "libyan_guests"
    )
    arab_guests = guests.get(
        "arab_guests"
    )
    foreign_guests = guests.get(
        "foreign_guests"
    )

    indicators: dict[str, JsonObject] = {}

    indicators[
        "average_guests_per_facility"
    ] = _ratio_indicator(
        code="average_guests_per_facility",
        name_ar="متوسط النزلاء لكل فندق أو شقة فندقية",
        numerator_name="total_guests",
        numerator_value=total_guests,
        denominator_name="hotels_and_apartments",
        denominator_value=hotels_and_apartments,
        unit="guest_per_facility",
        rounding=2,
    )

    indicators[
        "average_rooms_per_facility"
    ] = _ratio_indicator(
        code="average_rooms_per_facility",
        name_ar="متوسط الغرف لكل فندق أو شقة فندقية",
        numerator_name="reported_rooms",
        numerator_value=rooms,
        denominator_name="hotels_and_apartments",
        denominator_value=hotels_and_apartments,
        unit="room_per_facility",
        rounding=2,
    )

    indicators[
        "average_beds_per_facility"
    ] = _ratio_indicator(
        code="average_beds_per_facility",
        name_ar="متوسط الأسرة لكل فندق أو شقة فندقية",
        numerator_name="reported_hotel_beds",
        numerator_value=hotel_beds,
        denominator_name="hotels_and_apartments",
        denominator_value=hotels_and_apartments,
        unit="bed_per_facility",
        rounding=2,
        quality_status="calculated_with_definition_review",
        note_ar=(
            "يحتاج تعريف نطاق الأسرة إلى مراجعة للتأكد "
            "من المنشآت المشمولة."
        ),
    )

    indicators[
        "average_beds_per_room"
    ] = _ratio_indicator(
        code="average_beds_per_room",
        name_ar="متوسط الأسرة لكل غرفة",
        numerator_name="reported_hotel_beds",
        numerator_value=hotel_beds,
        denominator_name="reported_rooms",
        denominator_value=rooms,
        unit="bed_per_room",
        rounding=2,
        quality_status="calculated_with_definition_review",
        note_ar=(
            "النتيجة تحتاج تفسيرًا منهجيًا ومراجعة "
            "تعريف الغرف والأسرة."
        ),
    )

    indicators[
        "libyan_guest_share"
    ] = _ratio_indicator(
        code="libyan_guest_share",
        name_ar="حصة النزلاء الليبيين",
        numerator_name="libyan_guests",
        numerator_value=libyan_guests,
        denominator_name="total_guests",
        denominator_value=total_guests,
        unit="percent",
        multiplier=100,
        rounding=2,
    )

    indicators[
        "arab_guest_share"
    ] = _ratio_indicator(
        code="arab_guest_share",
        name_ar="حصة النزلاء العرب",
        numerator_name="arab_guests",
        numerator_value=arab_guests,
        denominator_name="total_guests",
        denominator_value=total_guests,
        unit="percent",
        multiplier=100,
        rounding=2,
    )

    indicators[
        "foreign_guest_share"
    ] = _ratio_indicator(
        code="foreign_guest_share",
        name_ar="حصة النزلاء الأجانب",
        numerator_name="foreign_guests",
        numerator_value=foreign_guests,
        denominator_name="total_guests",
        denominator_value=total_guests,
        unit="percent",
        multiplier=100,
        rounding=2,
    )

    tourist_nights = operational.get(
        "tourist_nights"
    )

    occupied_room_nights = operational.get(
        "occupied_room_nights"
    )

    available_room_nights = operational.get(
        "available_room_nights"
    )

    occupied_bed_nights = operational.get(
        "occupied_bed_nights"
    )

    available_bed_nights = operational.get(
        "available_bed_nights"
    )

    room_revenue_lyd = operational.get(
        "room_revenue_lyd"
    )

    indicators[
        "average_length_of_stay"
    ] = _ratio_indicator(
        code="average_length_of_stay",
        name_ar="متوسط مدة الإقامة",
        numerator_name="tourist_nights",
        numerator_value=tourist_nights,
        denominator_name="total_guests",
        denominator_value=total_guests,
        unit="night",
        rounding=2,
        note_ar=(
            "يحتاج المؤشر إلى عدد الليالي السياحية "
            "الفعلية المسجلة."
        ),
    )

    indicators[
        "room_occupancy_rate"
    ] = _ratio_indicator(
        code="room_occupancy_rate",
        name_ar="معدل إشغال الغرف",
        numerator_name="occupied_room_nights",
        numerator_value=occupied_room_nights,
        denominator_name="available_room_nights",
        denominator_value=available_room_nights,
        unit="percent",
        multiplier=100,
        rounding=2,
        note_ar=(
            "لا يتم تقدير الإشغال من عدد النزلاء؛ "
            "يلزم عدد ليالي الغرف المباعة والمتاحة."
        ),
    )

    indicators[
        "bed_occupancy_rate"
    ] = _ratio_indicator(
        code="bed_occupancy_rate",
        name_ar="معدل إشغال الأسرة",
        numerator_name="occupied_bed_nights",
        numerator_value=occupied_bed_nights,
        denominator_name="available_bed_nights",
        denominator_value=available_bed_nights,
        unit="percent",
        multiplier=100,
        rounding=2,
        note_ar=(
            "يلزم عدد ليالي الأسرة المشغولة "
            "والمتاحة فعليًا."
        ),
    )

    indicators[
        "average_daily_rate"
    ] = _ratio_indicator(
        code="average_daily_rate",
        name_ar="متوسط سعر الغرفة المباعة ADR",
        numerator_name="room_revenue_lyd",
        numerator_value=room_revenue_lyd,
        denominator_name="occupied_room_nights",
        denominator_value=occupied_room_nights,
        unit="lyd_per_room_night",
        rounding=2,
        note_ar=(
            "يلزم إيراد الغرف الفعلي وعدد ليالي "
            "الغرف المباعة."
        ),
    )

    indicators[
        "revenue_per_available_room"
    ] = _ratio_indicator(
        code="revenue_per_available_room",
        name_ar="العائد لكل غرفة متاحة RevPAR",
        numerator_name="room_revenue_lyd",
        numerator_value=room_revenue_lyd,
        denominator_name="available_room_nights",
        denominator_value=available_room_nights,
        unit="lyd_per_available_room",
        rounding=2,
        note_ar=(
            "يلزم إيراد الغرف الفعلي وعدد ليالي "
            "الغرف المتاحة."
        ),
    )

    available_count = sum(
        1
        for indicator in indicators.values()
        if indicator["status"] == "available"
    )

    unavailable_count = sum(
        1
        for indicator in indicators.values()
        if indicator["status"] == "unavailable"
    )

    total_indicators = len(indicators)

    readiness_percent = _safe_divide(
        available_count,
        total_indicators,
        multiplier=100,
        rounding=2,
    )

    if unavailable_count == 0:
        module_status = "complete"
    elif available_count == 0:
        module_status = "unavailable"
    else:
        module_status = "available_with_operational_gaps"

    return {
        "schema_version": "1.0.0",
        "module": "accommodation",
        "module_name_ar": "الإيواء والإشغال الفندقي",
        "year": payload.get("year"),
        "generated_at": datetime.now(
            ZoneInfo(DEFAULT_TIMEZONE)
        ).isoformat(),
        "status": module_status,

        "inventory": {
            "hotels": hotels,
            "hotel_apartments": apartments,
            "hotels_and_apartments": (
                hotels_and_apartments
            ),
            "tourist_villages": tourist_villages,
            "chalets": chalets,
            "reported_rooms": rooms,
            "reported_hotel_beds": hotel_beds,
            "reported_chalet_beds": chalet_beds,
        },

        "guests": {
            "total_guests": total_guests,
            "libyan_guests": libyan_guests,
            "arab_guests": arab_guests,
            "foreign_guests": foreign_guests,
            "reconciliation_status": guests.get(
                "reconciliation_status"
            ),
            "source_file": guests.get(
                "source_file"
            ),
        },

        "indicators": indicators,

        "readiness": {
            "total_indicators": total_indicators,
            "available_indicators": available_count,
            "unavailable_indicators": unavailable_count,
            "readiness_percent": readiness_percent,
            "operational_data_complete": (
                unavailable_count == 0
            ),
        },

        "quality_flags": quality_flags,

        "methodology": payload.get(
            "methodology",
            {},
        ),
    }


def get_accommodation_indicator(
    code: str,
) -> JsonObject:
    """
    إرجاع مؤشر إيواء واحد باستخدام الرمز البرمجي.
    """
    normalized_code = str(
        code or ""
    ).strip()

    if not normalized_code:
        raise AccommodationServiceError(
            "رمز مؤشر الإيواء مطلوب."
        )

    result = calculate_accommodation_metrics()

    indicators = result.get(
        "indicators",
        {},
    )

    indicator = indicators.get(
        normalized_code
    )

    if not isinstance(indicator, dict):
        raise AccommodationServiceError(
            f"مؤشر الإيواء غير موجود: {normalized_code}"
        )

    return indicator
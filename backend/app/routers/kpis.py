"""
KPI API for the Libyan National Tourism Intelligence Platform.

يوفر هذا الراوتر:
- المحافظة على المسارات القديمة للبيانات الأساسية.
- المؤشرات الوطنية المحسوبة من KPI Engine.
- مؤشر واحد حسب الرمز البرمجي.
- مؤشرات المدن والقارات.
- لقطة موحدة جاهزة لأول لوحة مؤشرات وطنية.

مبدأ منهجي:
لا يعيد الراوتر قيمة مصطنعة عند غياب مدخلات المؤشر؛ بل يعرض المؤشر
بحالة unavailable كما يقرر محرك المؤشرات.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.services.data_service import (
    load_national_kpis,
    load_tourism_data,
)
from app.services.kpi_engine import (
    KPIEngineError,
    calculate_city_kpis,
    calculate_continent_kpis,
    calculate_dashboard_snapshot,
    calculate_indicator,
    calculate_national_kpis,
)

router = APIRouter(tags=["KPIs"])

JsonObject = dict[str, Any]


def _raise_engine_http_error(exc: KPIEngineError) -> None:
    """تحويل أخطاء المحرك إلى استجابات HTTP واضحة."""
    message = str(exc)

    not_found_markers = (
        "غير موجودة",
        "غير موجود",
        "غير مسجل",
    )

    status_code = (
        status.HTTP_404_NOT_FOUND
        if any(marker in message for marker in not_found_markers)
        else status.HTTP_422_UNPROCESSABLE_ENTITY
    )

    raise HTTPException(
        status_code=status_code,
        detail={
            "status": "kpi_engine_error",
            "message_ar": message,
        },
    ) from exc


# =========================================================
# Legacy-compatible endpoints
# =========================================================

@router.get(
    "/api/kpis",
    summary="البيانات السياحية الأساسية",
)
def get_legacy_kpis() -> JsonObject:
    """
    مسار متوافق مع النسخة السابقة من الواجهة.

    يعيد البيانات الأساسية المجمعة من ملفات JSON، ولا يمثل ناتج
    المحرك الحسابي الكامل. المسار الحديث هو /api/kpis/national.
    """
    return load_tourism_data()


@router.get(
    "/api/summary",
    summary="الملخص الوطني الأساسي",
)
def get_legacy_summary() -> JsonObject:
    """ملخص مبسط للمؤشرات الرئيسية للمحافظة على توافق الواجهة الحالية."""
    data = load_national_kpis()

    return {
        "year": data.get("year"),
        "international_tourists": data.get("international_tourists"),
        "tourism_trips": data.get("tourism_trips"),
        "hotel_guests": data.get("hotel_guests"),
        "hotels": data.get("hotels"),
        "hotel_apartments": data.get("hotel_apartments"),
        "tourist_villages": data.get("tourist_villages"),
        "hotel_rooms": data.get("hotel_rooms"),
        "hotel_beds": data.get("hotel_beds"),
        "tourism_companies": data.get("tourism_companies"),
        "heritage_visitors": data.get("heritage_visitors"),
        "summer_revenue_lyd": data.get("summer_revenue_lyd"),
    }


# =========================================================
# KPI Engine endpoints
# =========================================================

@router.get(
    "/api/kpis/national",
    summary="حساب المؤشرات الوطنية",
)
def get_national_kpis() -> JsonObject:
    """تشغيل محرك المؤشرات وإرجاع المؤشرات المتاحة وغير المتاحة والمطابقات."""
    try:
        return calculate_national_kpis()
    except KPIEngineError as exc:
        _raise_engine_http_error(exc)


@router.get(
    "/api/kpis/indicator/{code}",
    summary="حساب مؤشر واحد",
)
def get_indicator_value(code: str) -> JsonObject:
    """
    إرجاع نتيجة مؤشر واحد باستخدام الرمز البرمجي المسجل، مثل:
    passengers_per_flight أو room_occupancy_rate.
    """
    try:
        return calculate_indicator(code)
    except KPIEngineError as exc:
        _raise_engine_http_error(exc)


@router.get(
    "/api/kpis/cities",
    summary="مؤشرات جميع المدن",
)
def get_city_kpis() -> JsonObject:
    """إرجاع حصص المدن وترتيبها الوطني وتركيب النزلاء لكل مدينة."""
    try:
        return calculate_city_kpis()
    except KPIEngineError as exc:
        _raise_engine_http_error(exc)


@router.get(
    "/api/kpis/cities/{city_id}",
    summary="مؤشرات مدينة محددة",
)
def get_city_kpi(city_id: str) -> JsonObject:
    """إرجاع مؤشرات مدينة واحدة باستخدام معرفها البرمجي."""
    try:
        return calculate_city_kpis(city_id=city_id)
    except KPIEngineError as exc:
        _raise_engine_http_error(exc)


@router.get(
    "/api/kpis/continents",
    summary="الحصة السوقية حسب القارة",
)
def get_continent_kpis() -> JsonObject:
    """إرجاع توزيع السياح الدوليين والحصة السوقية والترتيب حسب القارة."""
    try:
        return calculate_continent_kpis()
    except KPIEngineError as exc:
        _raise_engine_http_error(exc)


@router.get(
    "/api/kpis/dashboard",
    summary="لقطة موحدة للوحة المؤشرات",
)
def get_dashboard_snapshot(
    top_cities: int = Query(
        default=5,
        ge=1,
        le=20,
        description="عدد المدن الأعلى أداءً المطلوب تضمينها في اللقطة.",
    ),
) -> JsonObject:
    """
    إرجاع حزمة واحدة جاهزة للواجهة الأمامية تضم:
    - المؤشرات الوطنية.
    - المؤشرات غير المتاحة وأسبابها.
    - مطابقة المجاميع.
    - أعلى المدن.
    - توزيع القارات.
    """
    try:
        return calculate_dashboard_snapshot(top_cities=top_cities)
    except KPIEngineError as exc:
        _raise_engine_http_error(exc)

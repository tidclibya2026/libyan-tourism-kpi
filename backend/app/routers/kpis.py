"""
KPI API for the Libyan National Tourism Intelligence Platform.

يربط هذا الراوتر محرك المؤشرات بنماذج Pydantic الرسمية، مع:
- المحافظة على المسارات القديمة.
- التحقق التلقائي من شكل كل استجابة.
- توثيق العقود البرمجية في Swagger.
- إرجاع المؤشرات غير المتاحة دون اختلاق قيم.
"""

from __future__ import annotations

from typing import NoReturn

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.kpi import (
    CitiesKPIResponse,
    ContinentsKPIResponse,
    DashboardKPIResponse,
    KPIValue,
    LegacyKPIResponse,
    NationalKPIResponse,
    NationalSummaryResponse,
    SingleCityKPIResponse,
)
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


def _raise_engine_http_error(
    exc: KPIEngineError,
) -> NoReturn:
    """
    تحويل أخطاء KPI Engine إلى استجابة HTTP مفهومة.

    - 404 عندما لا يكون المؤشر أو المدينة مسجلًا.
    - 422 عندما تكون المدخلات غير صالحة للحساب.
    """

    message = str(exc)

    not_found_markers = (
        "غير موجودة",
        "غير موجود",
        "غير مسجل",
        "not found",
        "not registered",
    )

    status_code = (
        status.HTTP_404_NOT_FOUND
        if any(
            marker.lower() in message.lower()
            for marker in not_found_markers
        )
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
    response_model=LegacyKPIResponse,
    response_model_exclude_none=True,
    summary="البيانات السياحية الأساسية",
    description=(
        "مسار متوافق مع الواجهة السابقة. يعيد البيانات الأساسية "
        "المجمعة من ملفات JSON، بينما المسار الحديث للحساب هو "
        "/api/kpis/national."
    ),
)
def get_legacy_kpis() -> dict:
    """
    إرجاع بيانات السياحة الأساسية
    مع المحافظة على التوافق السابق.
    """

    return load_tourism_data()


@router.get(
    "/api/summary",
    response_model=NationalSummaryResponse,
    response_model_exclude_none=True,
    summary="الملخص الوطني الأساسي",
    description=(
        "إرجاع أهم القيم الوطنية المستخدمة "
        "في بطاقات الملخص ولوحة المؤشرات."
    ),
)
def get_legacy_summary() -> dict:
    """
    تجهيز الملخص الوطني من ملف المؤشرات الأساسية.

    يعيد أهم القيم المستخدمة في:
    - بطاقات لوحة المؤشرات.
    - الملخص التنفيذي.
    - اختبارات API.
    """

    data = load_national_kpis()

    return {
        "year": int(
            data.get("year", 0) or 0
        ),

        "international_tourists": int(
            data.get(
                "international_tourists",
                0,
            ) or 0
        ),

        "tourism_trips": int(
            data.get(
                "tourism_trips",
                0,
            ) or 0
        ),

        "hotel_guests": int(
            data.get(
                "hotel_guests",
                0,
            ) or 0
        ),

        "hotels": int(
            data.get(
                "hotels",
                0,
            ) or 0
        ),

        "hotel_apartments": int(
            data.get(
                "hotel_apartments",
                0,
            ) or 0
        ),

        "hotels_and_apartments": int(
            data.get(
                "hotels_and_apartments",
                0,
            ) or 0
        ),

        "tourist_villages": int(
            data.get(
                "tourist_villages",
                0,
            ) or 0
        ),

        "chalets": int(
            data.get(
                "chalets",
                0,
            ) or 0
        ),

        "hotel_rooms": int(
            data.get(
                "hotel_rooms",
                0,
            ) or 0
        ),

        "hotel_beds": int(
            data.get(
                "hotel_beds",
                0,
            ) or 0
        ),

        "tourism_companies": int(
            data.get(
                "tourism_companies",
                0,
            ) or 0
        ),

        "renewed_companies": int(
            data.get(
                "renewed_companies",
                0,
            ) or 0
        ),

        "handicrafts": int(
            data.get(
                "handicrafts",
                0,
            ) or 0
        ),

        "restaurants_cafes": int(
            data.get(
                "restaurants_cafes",
                0,
            ) or 0
        ),

        "flights": int(
            data.get(
                "flights",
                0,
            ) or 0
        ),

        "air_passengers": int(
            data.get(
                "air_passengers",
                0,
            ) or 0
        ),

        "heritage_visitors": int(
            data.get(
                "heritage_visitors",
                0,
            ) or 0
        ),

        "summer_revenue_lyd": (
            data.get(
                "summer_revenue_lyd",
                0,
            ) or 0
        ),
    }


# =========================================================
# KPI Engine endpoints
# =========================================================

@router.get(
    "/api/kpis/national",
    response_model=NationalKPIResponse,
    response_model_exclude_none=True,
    summary="حساب المؤشرات الوطنية",
    description=(
        "تشغيل محرك المؤشرات وإرجاع المؤشرات المحسوبة، "
        "والمؤشرات غير المتاحة، ونتائج مطابقة المجاميع."
    ),
    responses={
        422: {
            "description": (
                "تعذر الحساب بسبب مدخلات غير صالحة."
            )
        }
    },
)
def get_national_kpis() -> dict:
    """
    تشغيل النواة الحسابية الوطنية لمحرك المؤشرات.
    """

    try:
        return calculate_national_kpis()
    except KPIEngineError as exc:
        _raise_engine_http_error(exc)


@router.get(
    "/api/kpis/indicator/{code}",
    response_model=KPIValue,
    response_model_exclude_none=True,
    summary="حساب مؤشر واحد",
    description=(
        "إرجاع مؤشر باستخدام رمزه البرمجي المسجل، "
        "مثل passengers_per_flight أو "
        "room_occupancy_rate."
    ),
    responses={
        404: {
            "description": "رمز المؤشر غير مسجل."
        },
        422: {
            "description": (
                "تعذر حساب المؤشر بسبب مدخلات غير صالحة."
            )
        },
    },
)
def get_indicator_value(
    code: str,
) -> dict:
    """
    إرجاع نتيجة مؤشر واحد،
    سواء كان محسوبًا أو غير متاح.
    """

    try:
        return calculate_indicator(code)
    except KPIEngineError as exc:
        _raise_engine_http_error(exc)


@router.get(
    "/api/kpis/cities",
    response_model=CitiesKPIResponse,
    response_model_exclude_none=True,
    summary="مؤشرات جميع المدن",
    description=(
        "إرجاع إجمالي النزلاء، والترتيب الوطني، "
        "والحصة، والتركيب السوقي لكل مدينة "
        "أو فرع سياحي."
    ),
    responses={
        422: {
            "description": (
                "تعذر حساب مؤشرات المدن."
            )
        }
    },
)
def get_city_kpis() -> dict:
    """
    حساب مؤشرات جميع المدن وترتيبها تنازليًا.
    """

    try:
        return calculate_city_kpis()
    except KPIEngineError as exc:
        _raise_engine_http_error(exc)


@router.get(
    "/api/kpis/cities/{city_id}",
    response_model=SingleCityKPIResponse,
    response_model_exclude_none=True,
    summary="مؤشرات مدينة محددة",
    description=(
        "إرجاع مؤشرات مدينة واحدة "
        "باستخدام معرفها البرمجي."
    ),
    responses={
        404: {
            "description": "معرف المدينة غير موجود."
        },
        422: {
            "description": (
                "تعذر حساب مؤشرات المدينة."
            )
        },
    },
)
def get_city_kpi(
    city_id: str,
) -> dict:
    """
    حساب مؤشرات مدينة واحدة.
    """

    try:
        return calculate_city_kpis(
            city_id=city_id
        )
    except KPIEngineError as exc:
        _raise_engine_http_error(exc)


@router.get(
    "/api/kpis/continents",
    response_model=ContinentsKPIResponse,
    response_model_exclude_none=True,
    summary="الحصة السوقية حسب القارة",
    description=(
        "إرجاع أعداد السياح الدوليين "
        "والحصة السوقية والترتيب حسب القارة."
    ),
    responses={
        422: {
            "description": (
                "تعذر حساب توزيع القارات."
            )
        }
    },
)
def get_continent_kpis() -> dict:
    """
    حساب توزيع السياح الدوليين حسب القارات.
    """

    try:
        return calculate_continent_kpis()
    except KPIEngineError as exc:
        _raise_engine_http_error(exc)


@router.get(
    "/api/kpis/dashboard",
    response_model=DashboardKPIResponse,
    response_model_exclude_none=True,
    summary="لقطة موحدة للوحة المؤشرات",
    description=(
        "إرجاع حزمة واحدة للواجهة الأمامية "
        "تضم المؤشرات الوطنية، والمطابقات، "
        "وأعلى المدن، وتوزيع القارات."
    ),
    responses={
        422: {
            "description": (
                "قيمة top_cities غير صالحة "
                "أو تعذر الحساب."
            )
        }
    },
)
def get_dashboard_snapshot(
    top_cities: int = Query(
        default=5,
        ge=1,
        le=20,
        description=(
            "عدد المدن الأعلى ترتيبًا "
            "المطلوب تضمينها."
        ),
    ),
) -> dict:
    """
    تجهيز لقطة Dashboard موحدة
    في طلب API واحد.
    """

    try:
        return calculate_dashboard_snapshot(
            top_cities=top_cities
        )
    except KPIEngineError as exc:
        _raise_engine_http_error(exc)
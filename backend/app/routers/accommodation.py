"""
Accommodation API router.

يوفر هذا الراوتر:
- الحزمة الكاملة لمحور الإيواء.
- قائمة مؤشرات الإيواء.
- مؤشر إيواء واحد باستخدام الرمز البرمجي.
"""

from __future__ import annotations

from typing import NoReturn

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from app.schemas.accommodation import (
    AccommodationIndicator,
    AccommodationIndicatorsResponse,
    AccommodationResponse,
)
from app.services.accommodation_service import (
    AccommodationServiceError,
    calculate_accommodation_metrics,
    get_accommodation_indicator,
)


router = APIRouter(
    prefix="/api/accommodation",
    tags=["Accommodation"],
)


def _raise_accommodation_http_error(
    exc: AccommodationServiceError,
) -> NoReturn:
    """
    تحويل أخطاء خدمة الإيواء إلى استجابة HTTP واضحة.
    """
    message = str(exc)

    not_found_markers = (
        "غير موجود",
        "غير مسجل",
        "not found",
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
            "status": "accommodation_service_error",
            "message_ar": message,
        },
    ) from exc


@router.get(
    "",
    response_model=AccommodationResponse,
    response_model_exclude_none=False,
    summary="محور الإيواء والإشغال الفندقي",
    description=(
        "إرجاع الطاقة الإيوائية، وتوزيع النزلاء، "
        "والمؤشرات المحسوبة، والمؤشرات غير المتاحة، "
        "وحالة جاهزية البيانات التشغيلية."
    ),
    responses={
        422: {
            "description": (
                "تعذر حساب مؤشرات الإيواء بسبب "
                "بنية بيانات غير صالحة."
            )
        }
    },
)
def get_accommodation() -> dict:
    """
    إرجاع الحزمة الكاملة لمحور الإيواء.
    """
    try:
        return calculate_accommodation_metrics()

    except AccommodationServiceError as exc:
        _raise_accommodation_http_error(exc)


@router.get(
    "/indicators",
    response_model=AccommodationIndicatorsResponse,
    response_model_exclude_none=False,
    summary="قائمة مؤشرات الإيواء",
    description=(
        "إرجاع مؤشرات الإيواء المحسوبة وغير المتاحة "
        "في قائمة موحدة مناسبة للواجهة."
    ),
    responses={
        422: {
            "description": (
                "تعذر تجهيز قائمة مؤشرات الإيواء."
            )
        }
    },
)
def get_accommodation_indicators() -> dict:
    """
    إرجاع جميع مؤشرات الإيواء في قائمة.
    """
    try:
        result = calculate_accommodation_metrics()

    except AccommodationServiceError as exc:
        _raise_accommodation_http_error(exc)

    indicators = result.get(
        "indicators",
        {},
    )

    items = (
        list(indicators.values())
        if isinstance(indicators, dict)
        else []
    )

    return {
        "module": result["module"],
        "module_name_ar": result[
            "module_name_ar"
        ],
        "year": result["year"],
        "status": result["status"],
        "readiness": result["readiness"],
        "items": items,
    }


@router.get(
    "/indicators/{code}",
    response_model=AccommodationIndicator,
    response_model_exclude_none=False,
    summary="مؤشر إيواء واحد",
    description=(
        "إرجاع مؤشر واحد باستخدام رمزه البرمجي، "
        "مثل room_occupancy_rate أو "
        "average_guests_per_facility."
    ),
    responses={
        404: {
            "description": (
                "رمز مؤشر الإيواء غير موجود."
            )
        },
        422: {
            "description": (
                "تعذر حساب مؤشر الإيواء."
            )
        },
    },
)
def get_single_accommodation_indicator(
    code: str,
) -> dict:
    """
    إرجاع مؤشر إيواء واحد.
    """
    try:
        return get_accommodation_indicator(
            code
        )

    except AccommodationServiceError as exc:
        _raise_accommodation_http_error(exc)
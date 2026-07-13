"""
API router for monthly accommodation operations.

يوفر مسارات البيانات التشغيلية الشهرية، والملخص،
والسجلات، والاتجاهات، والسجل التاريخي للمنشآت.
"""

from __future__ import annotations

from typing import NoReturn

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    status,
)

from app.schemas.accommodation_monthly import (
    AccommodationFacilityHistoryResponse,
    AccommodationMonthlyRecordsResponse,
    AccommodationMonthlyResponse,
    AccommodationMonthlySummaryResponse,
    AccommodationMonthlyTrendsResponse,
)
from app.services.accommodation_monthly_service import (
    AccommodationMonthlyServiceError,
    calculate_monthly_accommodation_metrics,
    get_facility_monthly_history,
    get_monthly_accommodation_records,
    get_monthly_accommodation_summary,
    get_monthly_accommodation_trends,
)


router = APIRouter(
    prefix="/api/accommodation/monthly",
    tags=["Accommodation Monthly"],
)


def _raise_monthly_http_error(
    exc: AccommodationMonthlyServiceError,
) -> NoReturn:
    """
    تحويل أخطاء الخدمة إلى استجابة HTTP موحدة.
    """
    message = str(exc)

    not_found_markers = (
        "غير موجود",
        "not found",
    )

    is_not_found = any(
        marker.casefold()
        in message.casefold()
        for marker in not_found_markers
    )

    raise HTTPException(
        status_code=(
            status.HTTP_404_NOT_FOUND
            if is_not_found
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        ),
        detail={
            "status": (
                "accommodation_monthly_service_error"
            ),
            "message_ar": message,
        },
    ) from exc


def _build_filters(
    *,
    month: int | None,
    branch: str | None,
    municipality: str | None,
    verification_status: str | None,
) -> dict:
    """
    تجهيز مرشحات الخدمة بصورة موحدة.
    """
    return {
        "month": month,
        "branch": branch,
        "municipality": municipality,
        "verification_status": verification_status,
    }


@router.get(
    "",
    response_model=AccommodationMonthlyResponse,
    response_model_exclude_none=False,
    summary="الإيواء التشغيلي الشهري",
    description=(
        "إرجاع المجاميع والمؤشرات والاتجاهات التشغيلية "
        "الشهرية. عند غياب البيانات تكون قيم المؤشرات "
        "غير متاحة ولا تُعامل كقيم صفرية."
    ),
    responses={
        422: {
            "description": (
                "بنية بيانات الإيواء الشهرية غير صالحة."
            )
        }
    },
)
def get_monthly_accommodation(
    month: int | None = Query(
        default=None,
        ge=1,
        le=12,
        description="رقم الشهر من 1 إلى 12.",
    ),
    branch: str | None = Query(
        default=None,
        description="فرع مركز المعلومات السياحية.",
    ),
    municipality: str | None = Query(
        default=None,
        description="البلدية.",
    ),
    verification_status: str | None = Query(
        default=None,
        description="حالة التحقق من السجل.",
    ),
    include_records: bool = Query(
        default=False,
        description=(
            "إرفاق السجلات التفصيلية داخل الاستجابة."
        ),
    ),
) -> dict:
    """
    إرجاع الحزمة الكاملة لبيانات الإيواء الشهرية.
    """
    try:
        return calculate_monthly_accommodation_metrics(
            **_build_filters(
                month=month,
                branch=branch,
                municipality=municipality,
                verification_status=(
                    verification_status
                ),
            ),
            include_records=include_records,
        )

    except AccommodationMonthlyServiceError as exc:
        _raise_monthly_http_error(exc)


@router.get(
    "/summary",
    response_model=AccommodationMonthlySummaryResponse,
    response_model_exclude_none=False,
    summary="ملخص الإيواء التشغيلي الشهري",
    description=(
        "إرجاع المجاميع والمؤشرات دون السجلات "
        "التفصيلية أو سلسلة الاتجاهات."
    ),
)
def get_monthly_accommodation_summary_endpoint(
    month: int | None = Query(
        default=None,
        ge=1,
        le=12,
    ),
    branch: str | None = None,
    municipality: str | None = None,
    verification_status: str | None = None,
) -> dict:
    """
    إرجاع الملخص التشغيلي الشهري.
    """
    try:
        return get_monthly_accommodation_summary(
            **_build_filters(
                month=month,
                branch=branch,
                municipality=municipality,
                verification_status=(
                    verification_status
                ),
            )
        )

    except AccommodationMonthlyServiceError as exc:
        _raise_monthly_http_error(exc)


@router.get(
    "/records",
    response_model=AccommodationMonthlyRecordsResponse,
    response_model_exclude_none=False,
    summary="سجلات الإيواء التشغيلية الشهرية",
    description=(
        "إرجاع السجلات الشهرية بعد تطبيق المرشحات."
    ),
)
def get_monthly_accommodation_records_endpoint(
    month: int | None = Query(
        default=None,
        ge=1,
        le=12,
    ),
    branch: str | None = None,
    municipality: str | None = None,
    verification_status: str | None = None,
) -> dict:
    """
    إرجاع السجلات التشغيلية الشهرية.
    """
    try:
        return get_monthly_accommodation_records(
            **_build_filters(
                month=month,
                branch=branch,
                municipality=municipality,
                verification_status=(
                    verification_status
                ),
            )
        )

    except AccommodationMonthlyServiceError as exc:
        _raise_monthly_http_error(exc)


@router.get(
    "/trends",
    response_model=AccommodationMonthlyTrendsResponse,
    response_model_exclude_none=False,
    summary="اتجاهات الإيواء التشغيلية الشهرية",
    description=(
        "إرجاع مؤشرات الإيواء مجمعة حسب السنة والشهر."
    ),
)
def get_monthly_accommodation_trends_endpoint(
    month: int | None = Query(
        default=None,
        ge=1,
        le=12,
    ),
    branch: str | None = None,
    municipality: str | None = None,
    verification_status: str | None = None,
) -> dict:
    """
    إرجاع سلسلة الاتجاهات الشهرية.
    """
    try:
        return get_monthly_accommodation_trends(
            **_build_filters(
                month=month,
                branch=branch,
                municipality=municipality,
                verification_status=(
                    verification_status
                ),
            )
        )

    except AccommodationMonthlyServiceError as exc:
        _raise_monthly_http_error(exc)


@router.get(
    "/facilities/{facility_id}/history",
    response_model=AccommodationFacilityHistoryResponse,
    response_model_exclude_none=False,
    summary="السجل التاريخي الشهري لمنشأة",
    description=(
        "إرجاع جميع السجلات الشهرية الخاصة بمنشأة "
        "إيواء واحدة مرتبة زمنياً."
    ),
    responses={
        404: {
            "description": (
                "معرف المنشأة غير موجود في البيانات الشهرية."
            )
        }
    },
)
def get_facility_monthly_history_endpoint(
    facility_id: str,
) -> dict:
    """
    إرجاع السجل الشهري التاريخي لمنشأة محددة.
    """
    try:
        return get_facility_monthly_history(
            facility_id
        )

    except AccommodationMonthlyServiceError as exc:
        _raise_monthly_http_error(exc)
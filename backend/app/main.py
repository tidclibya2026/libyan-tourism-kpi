"""
Application entry point for the Libyan National Tourism Intelligence Platform.

هذا الملف مسؤول عن:
- إنشاء تطبيق FastAPI.
- ربط جميع Routers المعتمدة.
- إعداد CORS.
- عرض معلومات النظام.
- تنفيذ فحوصات الصحة والجاهزية.
- معالجة أخطاء طبقة البيانات بصورة موحدة.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import (
    ALLOWED_ORIGINS,
    API_PREFIX,
    APP_DESCRIPTION,
    APP_NAME,
    APP_NAME_AR,
    APP_SHORT_NAME,
    APP_VERSION,
    DEFAULT_DATA_YEAR,
    ENVIRONMENT,
    FORECAST_TARGET_YEAR,
    get_settings_summary,
)
from app.routers import (
    accommodation,
    accommodation_monthly,
    cities,
    forecast,
    kpis,
    metadata,
)
from app.services.data_service import (
    DataServiceError,
    get_data_status,
)


# =========================================================
# OpenAPI documentation groups
# =========================================================

OPENAPI_TAGS: list[dict[str, str]] = [
    {
        "name": "System",
        "description": "معلومات النظام وفحوصات الصحة والجاهزية.",
    },
    {
        "name": "KPIs",
        "description": "المؤشرات السياحية الوطنية والملخصات الأساسية.",
    },
    {
        "name": "Accommodation",
        "description": (
            "الطاقة الإيوائية والنزلاء "
            "والمؤشرات التشغيلية وجودة البيانات."
        ),
    },
    {
        "name": "Cities",
        "description": "مؤشرات المدن والتوزيع الجغرافي للطلب السياحي.",
    },
    {
        "name": "Forecast",
        "description": "التنبؤات والسيناريوهات السياحية حتى عام 2035.",
    },
    {
        "name": "Metadata Registry",
        "description": "سجل المؤشرات ومصادر البيانات وقواعد الجودة.",
    },
]


# =========================================================
# FastAPI application
# =========================================================

app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=OPENAPI_TAGS,
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=["*"],
)


# =========================================================
# API routers
# =========================================================

app.include_router(kpis.router)
app.include_router(accommodation.router)
app.include_router(accommodation_monthly.router)
app.include_router(cities.router)
app.include_router(forecast.router)
app.include_router(metadata.router)


# =========================================================
# Error handlers
# =========================================================

@app.exception_handler(DataServiceError)
async def data_service_error_handler(
    _request: Request,
    exc: DataServiceError,
) -> JSONResponse:
    """
    تحويل أخطاء ملفات البيانات إلى استجابة واضحة
    بدل إرجاع خطأ داخلي مبهم.
    """

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "data_service_error",
            "message_ar": (
                "تعذر الوصول إلى بيانات المنصة أو التحقق منها."
            ),
            "detail": str(exc),
        },
    )


# =========================================================
# System endpoints
# =========================================================

@app.get(
    "/",
    tags=["System"],
    summary="معلومات المنصة",
)
def home() -> dict[str, Any]:
    """
    إرجاع بطاقة تعريف مختصرة للمنصة وروابط التوثيق.
    """

    return {
        "system": APP_NAME,
        "system_ar": APP_NAME_AR,
        "short_name": APP_SHORT_NAME,
        "version": APP_VERSION,
        "environment": ENVIRONMENT,
        "status": "running",
        "default_data_year": DEFAULT_DATA_YEAR,
        "forecast_target_year": FORECAST_TARGET_YEAR,
        "api_prefix": API_PREFIX,
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        },
    }


@app.get(
    f"{API_PREFIX}/health",
    tags=["System"],
    summary="فحص صحة التطبيق والبيانات",
)
def health() -> dict[str, Any]:
    """
    فحص وجود الملفات الأساسية ونتيجة التحقق المختصرة.

    يعيد المسار 200 ما دام التطبيق قادرًا على الاستجابة،
    بينما يوضح status حالة البيانات الفعلية.
    """

    data_status = get_data_status()
    validation = data_status.get("validation", {})

    missing_files = data_status.get(
        "missing_required_files",
        [],
    )

    errors_count = int(
        validation.get("errors_count", 0) or 0
    )

    warnings_count = int(
        validation.get("warnings_count", 0) or 0
    )

    if missing_files or errors_count > 0:
        overall_status = "unhealthy"

    elif warnings_count > 0:
        overall_status = "healthy_with_warnings"

    else:
        overall_status = "healthy"

    return {
        "status": overall_status,
        "application": {
            "name": APP_NAME,
            "name_ar": APP_NAME_AR,
            "short_name": APP_SHORT_NAME,
            "version": APP_VERSION,
            "environment": ENVIRONMENT,
        },
        "data": data_status,
    }


@app.get(
    f"{API_PREFIX}/ready",
    tags=["System"],
    summary="فحص جاهزية المنصة للاستخدام",
)
def readiness() -> JSONResponse:
    """
    إرجاع 200 عندما تكون البيانات الأساسية جاهزة،
    وإرجاع 503 عند فقد ملف أساسي أو وجود خطأ تحقق.
    """

    data_status = get_data_status()
    validation = data_status.get("validation", {})

    missing_files = data_status.get(
        "missing_required_files",
        [],
    )

    errors_count = int(
        validation.get("errors_count", 0) or 0
    )

    is_ready = (
        not missing_files
        and errors_count == 0
    )

    payload = {
        "status": (
            "ready"
            if is_ready
            else "not_ready"
        ),
        "missing_required_files": missing_files,
        "validation": validation,
    }

    return JSONResponse(
        status_code=(
            status.HTTP_200_OK
            if is_ready
            else status.HTTP_503_SERVICE_UNAVAILABLE
        ),
        content=payload,
    )


@app.get(
    f"{API_PREFIX}/settings",
    tags=["System"],
    summary="ملخص إعدادات غير حساسة",
)
def settings_summary() -> dict[str, Any]:
    """
    إرجاع إعدادات تشخيصية غير حساسة
    للمطورين والإدارة الفنية.
    """

    return get_settings_summary()


# =========================================================
# Browser auxiliary routes
# =========================================================

@app.get(
    "/favicon.ico",
    include_in_schema=False,
)
def favicon() -> Response:
    """
    منع ظهور رسالة 404 عند طلب المتصفح لأيقونة الموقع.
    """

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )
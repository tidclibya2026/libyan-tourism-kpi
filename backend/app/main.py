from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import (
    ALLOWED_ORIGINS,
    APP_DESCRIPTION,
    APP_NAME,
    APP_NAME_AR,
    APP_SHORT_NAME,
    APP_VERSION,
    DEFAULT_DATA_YEAR,
    ENVIRONMENT,
    FORECAST_TARGET_YEAR,
)
from app.routers import cities, forecast, kpis
from app.services.data_service import (
    get_data_status,
    validate_all_data,
)


app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(kpis.router)
app.include_router(cities.router)
app.include_router(forecast.router)


@app.get("/", tags=["System"])
def home() -> dict[str, object]:
    """
    معلومات المنصة الأساسية.
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
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        },
    }


@app.get("/api/health", tags=["System"])
def health() -> dict[str, object]:
    """
    فحص حالة التطبيق وملفات البيانات والسجل الوطني للمؤشرات.
    """
    data_status = get_data_status()
    validation = validate_all_data()

    errors_count = validation.get("errors_count", 0)
    warnings_count = validation.get("warnings_count", 0)

    if errors_count > 0:
        overall_status = "unhealthy"
    elif warnings_count > 0:
        overall_status = "healthy_with_warnings"
    else:
        overall_status = "healthy"

    return {
        "status": overall_status,
        "application": {
            "name": APP_NAME,
            "short_name": APP_SHORT_NAME,
            "version": APP_VERSION,
            "environment": ENVIRONMENT,
        },
        "data": data_status,
        "validation": validation,
    }
"""
Central configuration for the Libyan National Tourism Intelligence Platform.

يحتوي هذا الملف على:
- معلومات النظام.
- مسارات المشروع والبيانات.
- إعدادات واجهات API.
- إعدادات البيئة والتشغيل.
- مسارات التقارير والسجلات والملفات المكانية.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final


def env_bool(name: str, default: bool = False) -> bool:
    """
    قراءة قيمة من متغيرات البيئة وتحويلها إلى Boolean.
    """
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
        "enabled",
    }


def env_int(name: str, default: int) -> int:
    """
    قراءة رقم صحيح من متغيرات البيئة بأمان.
    """
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def env_list(name: str, default: list[str]) -> list[str]:
    """
    قراءة قائمة مفصولة بفواصل من متغيرات البيئة.
    """
    value = os.getenv(name)

    if not value:
        return default

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


# =========================================================
# Project paths
# =========================================================

CONFIG_FILE: Final[Path] = Path(__file__).resolve()

CORE_DIR: Final[Path] = CONFIG_FILE.parent
APP_DIR: Final[Path] = CORE_DIR.parent
BACKEND_DIR: Final[Path] = APP_DIR.parent
PROJECT_ROOT: Final[Path] = BACKEND_DIR.parent

DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
CORE_DATA_DIR: Final[Path] = DATA_DIR / "core"
METADATA_DIR: Final[Path] = DATA_DIR / "metadata"
GEOJSON_DIR: Final[Path] = DATA_DIR / "geojson"
FORECAST_DATA_DIR: Final[Path] = DATA_DIR / "forecast"

REPORTS_DIR: Final[Path] = PROJECT_ROOT / "reports"
EXPORTS_DIR: Final[Path] = PROJECT_ROOT / "exports"
LOGS_DIR: Final[Path] = PROJECT_ROOT / "logs"
TESTS_DIR: Final[Path] = PROJECT_ROOT / "tests"


# =========================================================
# Main data files
# =========================================================

NATIONAL_KPIS_FILE: Final[Path] = (
    CORE_DATA_DIR / "national_kpis_2025.json"
)

CITIES_FILE: Final[Path] = (
    CORE_DATA_DIR / "cities_2025.json"
)

CONTINENTS_FILE: Final[Path] = (
    CORE_DATA_DIR / "continents_2025.json"
)

ACCOMMODATION_FILE: Final[Path] = (
    CORE_DATA_DIR / "accommodation_2025.json"
)

DATA_SOURCES_FILE: Final[Path] = (
    METADATA_DIR / "data_sources.json"
)

INDICATOR_REGISTRY_FILE: Final[Path] = (
    METADATA_DIR / "indicator_registry.json"
)


# =========================================================
# Application identity
# =========================================================

APP_NAME: Final[str] = os.getenv(
    "APP_NAME",
    "Libyan National Tourism Intelligence Platform",
)

APP_NAME_AR: Final[str] = os.getenv(
    "APP_NAME_AR",
    "المنصة الوطنية الذكية للمؤشرات السياحية الليبية",
)

APP_SHORT_NAME: Final[str] = os.getenv(
    "APP_SHORT_NAME",
    "LNTIP",
)

APP_VERSION: Final[str] = os.getenv(
    "APP_VERSION",
    "2.0.0",
)

APP_DESCRIPTION: Final[str] = os.getenv(
    "APP_DESCRIPTION",
    (
        "National platform for tourism indicators, "
        "analytics, GIS, forecasting and decision support in Libya."
    ),
)

ORGANIZATION_NAME: Final[str] = os.getenv(
    "ORGANIZATION_NAME",
    "Tourism Information and Documentation Center",
)

ORGANIZATION_NAME_AR: Final[str] = os.getenv(
    "ORGANIZATION_NAME_AR",
    "مركز المعلومات والتوثيق السياحي",
)

COUNTRY_NAME: Final[str] = "Libya"
COUNTRY_NAME_AR: Final[str] = "ليبيا"
COUNTRY_CODE: Final[str] = "LY"


# =========================================================
# API configuration
# =========================================================

API_PREFIX: Final[str] = os.getenv(
    "API_PREFIX",
    "/api",
)

API_V1_PREFIX: Final[str] = os.getenv(
    "API_V1_PREFIX",
    "/api/v1",
)

DEFAULT_DATA_YEAR: Final[int] = env_int(
    "DEFAULT_DATA_YEAR",
    2025,
)

DEBUG: Final[bool] = env_bool(
    "DEBUG",
    True,
)

ENVIRONMENT: Final[str] = os.getenv(
    "ENVIRONMENT",
    "development",
)

HOST: Final[str] = os.getenv(
    "HOST",
    "127.0.0.1",
)

PORT: Final[int] = env_int(
    "PORT",
    8000,
)


# =========================================================
# CORS configuration
# =========================================================

DEFAULT_ALLOWED_ORIGINS: Final[list[str]] = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "https://tidclibya2026.github.io",
]

ALLOWED_ORIGINS: Final[list[str]] = env_list(
    "ALLOWED_ORIGINS",
    DEFAULT_ALLOWED_ORIGINS,
)


# =========================================================
# Data and reporting configuration
# =========================================================

DEFAULT_LANGUAGE: Final[str] = os.getenv(
    "DEFAULT_LANGUAGE",
    "ar",
)

SUPPORTED_LANGUAGES: Final[tuple[str, ...]] = (
    "ar",
    "en",
)

DEFAULT_TIMEZONE: Final[str] = os.getenv(
    "DEFAULT_TIMEZONE",
    "Africa/Tripoli",
)

DEFAULT_CURRENCY: Final[str] = os.getenv(
    "DEFAULT_CURRENCY",
    "LYD",
)

DEFAULT_DECIMAL_PLACES: Final[int] = env_int(
    "DEFAULT_DECIMAL_PLACES",
    2,
)

ENABLE_FORECAST: Final[bool] = env_bool(
    "ENABLE_FORECAST",
    True,
)

FORECAST_TARGET_YEAR: Final[int] = env_int(
    "FORECAST_TARGET_YEAR",
    2035,
)

ENABLE_REPORT_EXPORT: Final[bool] = env_bool(
    "ENABLE_REPORT_EXPORT",
    True,
)


# =========================================================
# Directory initialization
# =========================================================

REQUIRED_DIRECTORIES: Final[tuple[Path, ...]] = (
    DATA_DIR,
    CORE_DATA_DIR,
    METADATA_DIR,
    GEOJSON_DIR,
    FORECAST_DATA_DIR,
    REPORTS_DIR,
    EXPORTS_DIR,
    LOGS_DIR,
)


def ensure_required_directories() -> None:
    """
    إنشاء المجلدات التشغيلية المطلوبة إذا لم تكن موجودة.
    """
    for directory in REQUIRED_DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)


def get_project_paths() -> dict[str, str]:
    """
    إرجاع مسارات النظام لأغراض الفحص وHealth Check.
    """
    return {
        "project_root": str(PROJECT_ROOT),
        "backend_dir": str(BACKEND_DIR),
        "app_dir": str(APP_DIR),
        "data_dir": str(DATA_DIR),
        "core_data_dir": str(CORE_DATA_DIR),
        "metadata_dir": str(METADATA_DIR),
        "geojson_dir": str(GEOJSON_DIR),
        "forecast_data_dir": str(FORECAST_DATA_DIR),
        "reports_dir": str(REPORTS_DIR),
        "exports_dir": str(EXPORTS_DIR),
        "logs_dir": str(LOGS_DIR),
    }


def get_settings_summary() -> dict[str, object]:
    """
    ملخص إعدادات غير حساسة للاستخدام في الفحص والتشخيص.
    """
    return {
        "app_name": APP_NAME,
        "app_name_ar": APP_NAME_AR,
        "short_name": APP_SHORT_NAME,
        "version": APP_VERSION,
        "environment": ENVIRONMENT,
        "debug": DEBUG,
        "api_prefix": API_PREFIX,
        "api_v1_prefix": API_V1_PREFIX,
        "default_data_year": DEFAULT_DATA_YEAR,
        "forecast_target_year": FORECAST_TARGET_YEAR,
        "timezone": DEFAULT_TIMEZONE,
        "currency": DEFAULT_CURRENCY,
        "allowed_origins": ALLOWED_ORIGINS,
        "paths": get_project_paths(),
    }


ensure_required_directories()
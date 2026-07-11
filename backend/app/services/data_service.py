"""
Data access, indexing and validation services for the
Libyan National Tourism Intelligence Platform.

هذه الطبقة مسؤولة عن:
- قراءة ملفات JSON المركزية بأمان.
- تخزين البيانات المقروءة مؤقتًا لتحسين الأداء.
- المحافظة على التوافق مع الواجهات القديمة.
- بناء فهارس للمؤشرات ومصادر البيانات.
- التحقق من سلامة المجاميع والمراجع والتعريفات.
"""

from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import (
    CITIES_FILE,
    CONTINENTS_FILE,
    DATA_SOURCES_FILE,
    INDICATOR_REGISTRY_FILE,
    NATIONAL_KPIS_FILE,
    PROJECT_ROOT,
)
from app.core.enums import (
    AggregationMethod,
    ConfidenceLevel,
    DataStatus,
    GeographyLevel,
    IndicatorCategory,
    IndicatorDirection,
    IndicatorType,
    MeasurementUnit,
    TimeGranularity,
    UpdateFrequency,
    ValidationStatus,
    enum_values,
)

JsonObject = dict[str, Any]

LEGACY_DATA_FILE = PROJECT_ROOT / "data" / "tourism_2025.json"


class DataServiceError(RuntimeError):
    """خطأ موحد عند تعذر قراءة البيانات أو التحقق منها."""


def _issue(
    code: str,
    message_ar: str,
    *,
    severity: str = "error",
    location: str | None = None,
    details: dict[str, Any] | None = None,
) -> JsonObject:
    item: JsonObject = {
        "code": code,
        "severity": severity,
        "message_ar": message_ar,
    }

    if location:
        item["location"] = location

    if details:
        item["details"] = details

    return item


def _ensure_mapping(value: Any, *, path: Path) -> JsonObject:
    if not isinstance(value, dict):
        raise DataServiceError(
            f"يجب أن يكون جذر ملف البيانات كائن JSON: {path}"
        )
    return value


@lru_cache(maxsize=16)
def _load_json_cached(path_text: str) -> JsonObject:
    path = Path(path_text)

    if not path.exists():
        raise DataServiceError(f"ملف البيانات غير موجود: {path}")

    if not path.is_file():
        raise DataServiceError(f"مسار البيانات ليس ملفًا: {path}")

    try:
        with path.open("r", encoding="utf-8-sig") as file:
            payload = json.load(file)
    except json.JSONDecodeError as exc:
        raise DataServiceError(
            f"ملف JSON غير صالح: {path} "
            f"(السطر {exc.lineno}، العمود {exc.colno})"
        ) from exc
    except OSError as exc:
        raise DataServiceError(f"تعذر قراءة ملف البيانات: {path}") from exc

    return _ensure_mapping(payload, path=path)


def load_json(path: Path) -> JsonObject:
    """
    قراءة ملف JSON مع إرجاع نسخة مستقلة حتى لا يعدّل المستدعي الذاكرة المؤقتة.
    """
    return deepcopy(_load_json_cached(str(path.resolve())))


def clear_data_cache() -> None:
    """مسح ذاكرة ملفات JSON المؤقتة بعد تعديل البيانات أثناء التشغيل."""
    _load_json_cached.cache_clear()


def load_national_kpis() -> JsonObject:
    return load_json(NATIONAL_KPIS_FILE)


def load_cities() -> JsonObject:
    return load_json(CITIES_FILE)


def load_continents() -> JsonObject:
    return load_json(CONTINENTS_FILE)


def load_data_sources() -> JsonObject:
    return load_json(DATA_SOURCES_FILE)


def load_indicator_registry() -> JsonObject:
    return load_json(INDICATOR_REGISTRY_FILE)


def load_tourism_data() -> JsonObject:
    """
    محمّل تجميعي متوافق مع الواجهات القديمة.

    يجمع ملفات النواة في كائن واحد حتى تستمر المسارات الحالية مثل:
    /api/kpis
    /api/summary
    /api/cities
    في العمل دون تغيير فوري.
    """
    national = load_national_kpis()
    cities = load_cities()
    continents = load_continents()

    continent_items = continents.get("items", [])
    if not isinstance(continent_items, list):
        continent_items = []

    return {
        **national,
        "cities": cities.get("items", []),
        "continents": {
            item.get("name_en", item.get("id", "unknown")): item.get(
                "tourists", 0
            )
            for item in continent_items
            if isinstance(item, dict)
        },
        "metadata": {
            "cities_total_guests": cities.get("total_guests"),
            "continents_total": continents.get("total"),
            "data_sources_registry": DATA_SOURCES_FILE.name,
            "indicator_registry": INDICATOR_REGISTRY_FILE.name,
        },
    }


def get_data_source_index() -> dict[str, JsonObject]:
    """فهرس مصادر البيانات باستخدام source_id."""
    registry = load_data_sources()
    sources = registry.get("sources", [])

    if not isinstance(sources, list):
        return {}

    return {
        str(source["source_id"]): source
        for source in sources
        if isinstance(source, dict) and source.get("source_id")
    }


def get_indicator_index() -> dict[str, JsonObject]:
    """فهرس المؤشرات باستخدام indicator_id."""
    registry = load_indicator_registry()
    indicators = registry.get("indicators", [])

    if not isinstance(indicators, list):
        return {}

    return {
        str(indicator["indicator_id"]): indicator
        for indicator in indicators
        if isinstance(indicator, dict) and indicator.get("indicator_id")
    }


def get_indicator_code_index() -> dict[str, JsonObject]:
    """فهرس المؤشرات باستخدام الرمز البرمجي code."""
    registry = load_indicator_registry()
    indicators = registry.get("indicators", [])

    if not isinstance(indicators, list):
        return {}

    return {
        str(indicator["code"]): indicator
        for indicator in indicators
        if isinstance(indicator, dict) and indicator.get("code")
    }


def get_data_source(source_id: str) -> JsonObject | None:
    source = get_data_source_index().get(source_id)
    return deepcopy(source) if source else None


def get_indicator(
    *,
    indicator_id: str | None = None,
    code: str | None = None,
) -> JsonObject | None:
    if indicator_id:
        indicator = get_indicator_index().get(indicator_id)
        return deepcopy(indicator) if indicator else None

    if code:
        indicator = get_indicator_code_index().get(code)
        return deepcopy(indicator) if indicator else None

    return None


def _duplicate_values(items: list[JsonObject], field: str) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()

    for item in items:
        value = item.get(field)
        if value is None:
            continue

        normalized = str(value).strip()
        if not normalized:
            continue

        if normalized in seen:
            duplicates.add(normalized)
        else:
            seen.add(normalized)

    return sorted(duplicates)


def validate_core_data() -> JsonObject:
    """التحقق من اتساق مجاميع المؤشرات الوطنية والمدن والقارات."""
    issues: list[JsonObject] = []

    national = load_national_kpis()
    cities_payload = load_cities()
    continents_payload = load_continents()

    cities = cities_payload.get("items", [])
    if not isinstance(cities, list):
        issues.append(
            _issue(
                "CITIES_ITEMS_INVALID",
                "الحقل items في ملف المدن يجب أن يكون قائمة.",
                location="cities_2025.json.items",
            )
        )
        cities = []

    city_ids: list[str] = []
    calculated_city_total = 0

    for index, city in enumerate(cities):
        if not isinstance(city, dict):
            issues.append(
                _issue(
                    "CITY_RECORD_INVALID",
                    "يوجد سجل مدينة ليس كائن JSON صالحًا.",
                    location=f"cities_2025.json.items[{index}]",
                )
            )
            continue

        city_id = str(city.get("id", "")).strip()
        if city_id:
            city_ids.append(city_id)

        libyans = city.get("libyans", 0)
        arabs = city.get("arabs", 0)
        foreigners = city.get("foreigners", 0)
        declared_total = city.get("total_guests", 0)

        numeric_values = [libyans, arabs, foreigners, declared_total]
        if not all(isinstance(value, (int, float)) for value in numeric_values):
            issues.append(
                _issue(
                    "CITY_GUEST_VALUES_INVALID",
                    "قيم النزلاء في المدينة يجب أن تكون رقمية.",
                    location=f"cities_2025.json.items[{index}]",
                )
            )
            continue

        calculated_total = libyans + arabs + foreigners
        calculated_city_total += declared_total

        if calculated_total != declared_total:
            issues.append(
                _issue(
                    "CITY_TOTAL_MISMATCH",
                    "إجمالي نزلاء المدينة لا يساوي مجموع الليبيين والعرب والأجانب.",
                    location=f"cities_2025.json.items[{index}]",
                    details={
                        "city_id": city_id,
                        "declared_total": declared_total,
                        "calculated_total": calculated_total,
                    },
                )
            )

    duplicate_city_ids = sorted(
        city_id for city_id in set(city_ids) if city_ids.count(city_id) > 1
    )
    if duplicate_city_ids:
        issues.append(
            _issue(
                "DUPLICATE_CITY_IDS",
                "يوجد تكرار في معرفات المدن.",
                location="cities_2025.json.items",
                details={"duplicates": duplicate_city_ids},
            )
        )

    declared_cities_total = cities_payload.get("total_guests")
    if declared_cities_total != calculated_city_total:
        issues.append(
            _issue(
                "CITIES_TOTAL_MISMATCH",
                "إجمالي ملف المدن لا يساوي مجموع إجماليات المدن.",
                location="cities_2025.json.total_guests",
                details={
                    "declared_total": declared_cities_total,
                    "calculated_total": calculated_city_total,
                },
            )
        )

    national_hotel_guests = national.get("hotel_guests")
    if national_hotel_guests != calculated_city_total:
        issues.append(
            _issue(
                "NATIONAL_CITY_TOTAL_MISMATCH",
                "إجمالي نزلاء الإيواء الوطني لا يطابق مجموع المدن.",
                severity="warning",
                details={
                    "national_hotel_guests": national_hotel_guests,
                    "cities_total_guests": calculated_city_total,
                },
            )
        )

    continents = continents_payload.get("items", [])
    if not isinstance(continents, list):
        issues.append(
            _issue(
                "CONTINENTS_ITEMS_INVALID",
                "الحقل items في ملف القارات يجب أن يكون قائمة.",
                location="continents_2025.json.items",
            )
        )
        continents = []

    calculated_continent_total = 0
    continent_ids: list[str] = []

    for index, continent in enumerate(continents):
        if not isinstance(continent, dict):
            issues.append(
                _issue(
                    "CONTINENT_RECORD_INVALID",
                    "يوجد سجل قارة ليس كائن JSON صالحًا.",
                    location=f"continents_2025.json.items[{index}]",
                )
            )
            continue

        continent_id = str(continent.get("id", "")).strip()
        if continent_id:
            continent_ids.append(continent_id)

        tourists = continent.get("tourists", 0)
        if not isinstance(tourists, (int, float)):
            issues.append(
                _issue(
                    "CONTINENT_TOURISTS_INVALID",
                    "عدد السياح حسب القارة يجب أن يكون رقميًا.",
                    location=f"continents_2025.json.items[{index}].tourists",
                )
            )
            continue

        calculated_continent_total += tourists

    duplicate_continent_ids = sorted(
        continent_id
        for continent_id in set(continent_ids)
        if continent_ids.count(continent_id) > 1
    )
    if duplicate_continent_ids:
        issues.append(
            _issue(
                "DUPLICATE_CONTINENT_IDS",
                "يوجد تكرار في معرفات القارات.",
                location="continents_2025.json.items",
                details={"duplicates": duplicate_continent_ids},
            )
        )

    declared_continent_total = continents_payload.get("total")
    if declared_continent_total != calculated_continent_total:
        issues.append(
            _issue(
                "CONTINENTS_TOTAL_MISMATCH",
                "إجمالي ملف القارات لا يساوي مجموع القارات.",
                location="continents_2025.json.total",
                details={
                    "declared_total": declared_continent_total,
                    "calculated_total": calculated_continent_total,
                },
            )
        )

    national_international_tourists = national.get("international_tourists")
    if national_international_tourists != calculated_continent_total:
        issues.append(
            _issue(
                "NATIONAL_CONTINENT_TOTAL_MISMATCH",
                "عدد السياح الدوليين الوطني لا يطابق مجموع القارات.",
                severity="warning",
                details={
                    "national_international_tourists": national_international_tourists,
                    "continents_total": calculated_continent_total,
                },
            )
        )

    errors = [item for item in issues if item["severity"] == "error"]
    warnings = [item for item in issues if item["severity"] == "warning"]

    return {
        "status": "valid" if not issues else (
            "valid_with_warnings" if not errors else "invalid"
        ),
        "errors_count": len(errors),
        "warnings_count": len(warnings),
        "checks": {
            "cities_count": len(cities),
            "cities_total_guests": calculated_city_total,
            "continents_count": len(continents),
            "continents_total_tourists": calculated_continent_total,
        },
        "issues": issues,
    }


def validate_data_sources_registry() -> JsonObject:
    """التحقق من بنية سجل مصادر البيانات وعدم تكرار المعرفات والرموز."""
    registry = load_data_sources()
    issues: list[JsonObject] = []
    sources = registry.get("sources", [])

    if not isinstance(sources, list):
        return {
            "status": "invalid",
            "errors_count": 1,
            "warnings_count": 0,
            "sources_count": 0,
            "issues": [
                _issue(
                    "SOURCES_LIST_INVALID",
                    "الحقل sources في سجل المصادر يجب أن يكون قائمة.",
                    location="data_sources.json.sources",
                )
            ],
        }

    valid_sources = [item for item in sources if isinstance(item, dict)]

    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            issues.append(
                _issue(
                    "SOURCE_RECORD_INVALID",
                    "يوجد سجل مصدر ليس كائن JSON صالحًا.",
                    location=f"data_sources.json.sources[{index}]",
                )
            )
            continue

        for field in ("source_id", "code", "name_ar", "name_en"):
            if not source.get(field):
                issues.append(
                    _issue(
                        "SOURCE_REQUIRED_FIELD_MISSING",
                        "يوجد حقل إلزامي مفقود في سجل مصدر البيانات.",
                        location=f"data_sources.json.sources[{index}].{field}",
                        details={"field": field},
                    )
                )

    for field in ("source_id", "code"):
        duplicates = _duplicate_values(valid_sources, field)
        if duplicates:
            issues.append(
                _issue(
                    "DUPLICATE_SOURCE_FIELD",
                    f"يوجد تكرار في الحقل {field} داخل سجل المصادر.",
                    location=f"data_sources.json.sources.{field}",
                    details={"duplicates": duplicates},
                )
            )

    errors = [item for item in issues if item["severity"] == "error"]
    warnings = [item for item in issues if item["severity"] == "warning"]

    return {
        "status": "valid" if not issues else (
            "valid_with_warnings" if not errors else "invalid"
        ),
        "errors_count": len(errors),
        "warnings_count": len(warnings),
        "sources_count": len(valid_sources),
        "issues": issues,
    }


def validate_indicator_registry() -> JsonObject:
    """
    التحقق من سجل المؤشرات، قيم التصنيفات، والمعادلات، ومراجع المصادر.
    """
    registry = load_indicator_registry()
    sources_index = get_data_source_index()
    issues: list[JsonObject] = []
    indicators = registry.get("indicators", [])

    if not isinstance(indicators, list):
        return {
            "status": "invalid",
            "errors_count": 1,
            "warnings_count": 0,
            "indicators_count": 0,
            "issues": [
                _issue(
                    "INDICATORS_LIST_INVALID",
                    "الحقل indicators في سجل المؤشرات يجب أن يكون قائمة.",
                    location="indicator_registry.json.indicators",
                )
            ],
        }

    valid_indicators = [item for item in indicators if isinstance(item, dict)]

    allowed_values = {
        "category": set(enum_values(IndicatorCategory)),
        "indicator_type": set(enum_values(IndicatorType)),
        "measurement_unit": set(enum_values(MeasurementUnit)),
        "direction": set(enum_values(IndicatorDirection)),
        "aggregation_method": set(enum_values(AggregationMethod)),
        "time_granularity": set(enum_values(TimeGranularity)),
        "update_frequency": set(enum_values(UpdateFrequency)),
        "geography_level": set(enum_values(GeographyLevel)),
    }

    for index, indicator in enumerate(indicators):
        location = f"indicator_registry.json.indicators[{index}]"

        if not isinstance(indicator, dict):
            issues.append(
                _issue(
                    "INDICATOR_RECORD_INVALID",
                    "يوجد سجل مؤشر ليس كائن JSON صالحًا.",
                    location=location,
                )
            )
            continue

        for field in (
            "indicator_id",
            "code",
            "name_ar",
            "name_en",
            "category",
            "indicator_type",
            "measurement_unit",
            "calculation",
        ):
            if indicator.get(field) in (None, "", []):
                issues.append(
                    _issue(
                        "INDICATOR_REQUIRED_FIELD_MISSING",
                        "يوجد حقل إلزامي مفقود في تعريف المؤشر.",
                        location=f"{location}.{field}",
                        details={"field": field},
                    )
                )

        for field, allowed in allowed_values.items():
            value = indicator.get(field)
            if value is not None and value not in allowed:
                issues.append(
                    _issue(
                        "INDICATOR_ENUM_VALUE_INVALID",
                        "قيمة تصنيف المؤشر غير موجودة في القيم الموحدة للنظام.",
                        location=f"{location}.{field}",
                        details={
                            "field": field,
                            "value": value,
                        },
                    )
                )

        calculation = indicator.get("calculation")
        if not isinstance(calculation, dict):
            issues.append(
                _issue(
                    "INDICATOR_CALCULATION_INVALID",
                    "تعريف calculation يجب أن يكون كائن JSON.",
                    location=f"{location}.calculation",
                )
            )
        else:
            if not calculation.get("formula"):
                issues.append(
                    _issue(
                        "INDICATOR_FORMULA_MISSING",
                        "المؤشر لا يحتوي على معادلة حساب موثقة.",
                        location=f"{location}.calculation.formula",
                    )
                )

            method = calculation.get("method")
            if method == "ratio" and not calculation.get("denominator"):
                issues.append(
                    _issue(
                        "INDICATOR_DENOMINATOR_MISSING",
                        "مؤشر النسبة لا يحتوي على مقام denominator.",
                        location=f"{location}.calculation.denominator",
                    )
                )

        source_ids = indicator.get("data_source_ids", [])
        if not isinstance(source_ids, list):
            issues.append(
                _issue(
                    "INDICATOR_SOURCE_IDS_INVALID",
                    "الحقل data_source_ids يجب أن يكون قائمة.",
                    location=f"{location}.data_source_ids",
                )
            )
        else:
            for source_id in source_ids:
                if source_id not in sources_index:
                    issues.append(
                        _issue(
                            "INDICATOR_SOURCE_NOT_REGISTERED",
                            "المؤشر يشير إلى مصدر غير مسجل في سجل مصادر البيانات.",
                            location=f"{location}.data_source_ids",
                            details={
                                "indicator_id": indicator.get("indicator_id"),
                                "source_id": source_id,
                            },
                        )
                    )

        quality = indicator.get("quality", {})
        if not isinstance(quality, dict):
            issues.append(
                _issue(
                    "INDICATOR_QUALITY_INVALID",
                    "الحقل quality يجب أن يكون كائن JSON.",
                    location=f"{location}.quality",
                )
            )
        else:
            quality_enum_fields = {
                "status": set(enum_values(DataStatus)),
                "validation_status": set(enum_values(ValidationStatus)),
                "confidence_level": set(enum_values(ConfidenceLevel)),
            }
            for field, allowed in quality_enum_fields.items():
                value = quality.get(field)
                if value is not None and value not in allowed:
                    issues.append(
                        _issue(
                            "INDICATOR_QUALITY_ENUM_INVALID",
                            "قيمة جودة المؤشر غير موجودة في القيم الموحدة للنظام.",
                            location=f"{location}.quality.{field}",
                            details={"field": field, "value": value},
                        )
                    )

    for field in ("indicator_id", "code"):
        duplicates = _duplicate_values(valid_indicators, field)
        if duplicates:
            issues.append(
                _issue(
                    "DUPLICATE_INDICATOR_FIELD",
                    f"يوجد تكرار في الحقل {field} داخل سجل المؤشرات.",
                    location=f"indicator_registry.json.indicators.{field}",
                    details={"duplicates": duplicates},
                )
            )

    summary = registry.get("summary", {})
    declared_count = summary.get("indicator_count") if isinstance(summary, dict) else None
    actual_count = len(valid_indicators)

    if declared_count is not None and declared_count != actual_count:
        issues.append(
            _issue(
                "INDICATOR_COUNT_MISMATCH",
                "عدد المؤشرات في summary لا يطابق العدد الفعلي.",
                severity="warning",
                location="indicator_registry.json.summary.indicator_count",
                details={
                    "declared_count": declared_count,
                    "actual_count": actual_count,
                },
            )
        )

    errors = [item for item in issues if item["severity"] == "error"]
    warnings = [item for item in issues if item["severity"] == "warning"]

    return {
        "status": "valid" if not issues else (
            "valid_with_warnings" if not errors else "invalid"
        ),
        "errors_count": len(errors),
        "warnings_count": len(warnings),
        "indicators_count": actual_count,
        "registered_sources_count": len(sources_index),
        "issues": issues,
    }


def validate_all_data() -> JsonObject:
    """تشغيل جميع فحوصات البيانات وإرجاع نتيجة موحدة."""
    checks = {
        "core_data": validate_core_data(),
        "data_sources_registry": validate_data_sources_registry(),
        "indicator_registry": validate_indicator_registry(),
    }

    total_errors = sum(
        int(result.get("errors_count", 0)) for result in checks.values()
    )
    total_warnings = sum(
        int(result.get("warnings_count", 0)) for result in checks.values()
    )

    if total_errors:
        status = "invalid"
    elif total_warnings:
        status = "valid_with_warnings"
    else:
        status = "valid"

    return {
        "status": status,
        "errors_count": total_errors,
        "warnings_count": total_warnings,
        "checks": checks,
    }


def get_data_status() -> JsonObject:
    """حالة وجود الملفات ونتيجة تحقق مختصرة للاستخدام في Health Check."""
    files = {
        "national_kpis": NATIONAL_KPIS_FILE,
        "cities": CITIES_FILE,
        "continents": CONTINENTS_FILE,
        "data_sources": DATA_SOURCES_FILE,
        "indicator_registry": INDICATOR_REGISTRY_FILE,
        "legacy_data": LEGACY_DATA_FILE,
    }

    file_status = {
        name: {
            "path": str(path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
        }
        for name, path in files.items()
    }

    required_names = {
        "national_kpis",
        "cities",
        "continents",
        "data_sources",
        "indicator_registry",
    }
    missing_required = [
        name
        for name in required_names
        if not file_status[name]["exists"]
    ]

    response: JsonObject = {
        "status": "healthy" if not missing_required else "degraded",
        "missing_required_files": sorted(missing_required),
        "files": file_status,
        "cache": {
            "hits": _load_json_cached.cache_info().hits,
            "misses": _load_json_cached.cache_info().misses,
            "current_size": _load_json_cached.cache_info().currsize,
            "max_size": _load_json_cached.cache_info().maxsize,
        },
    }

    if not missing_required:
        validation = validate_all_data()
        response["validation"] = {
            "status": validation["status"],
            "errors_count": validation["errors_count"],
            "warnings_count": validation["warnings_count"],
        }

        if validation["status"] == "invalid":
            response["status"] = "degraded"

    return response

"""
Metadata API for the Libyan National Tourism Intelligence Platform.

يوفر هذا الراوتر واجهات قراءة منظمة من أجل:
- السجل الوطني لمصادر البيانات السياحية.
- السجل التشغيلي للمؤشرات السياحية.
- البحث والتصفية والترقيم.
- ربط المؤشرات بمصادرها الفعلية.
- عرض نتائج فحوصات جودة وسلامة البيانات.

ملاحظة أمنية:
لا يتضمن هذا الراوتر عمليات إنشاء أو تعديل أو حذف؛ إذ تؤجل هذه العمليات
إلى ما بعد بناء نظام المستخدمين والصلاحيات وسجل التدقيق.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.core.enums import (
    ConfidenceLevel,
    DataSourceType,
    DataStatus,
    GeographyLevel,
    IndicatorCategory,
    IndicatorType,
    MeasurementUnit,
    UpdateFrequency,
    ValidationStatus,
    get_enum_catalog,
)
from app.services.data_service import (
    get_data_source,
    get_data_source_index,
    get_indicator,
    load_data_sources,
    load_indicator_registry,
    validate_all_data,
    validate_data_sources_registry,
    validate_indicator_registry,
)

router = APIRouter(
    prefix="/api/metadata",
    tags=["Metadata Registry"],
)

JsonObject = dict[str, Any]


def _as_list(value: Any) -> list[JsonObject]:
    """إرجاع قائمة آمنة تحتوي فقط على كائنات JSON."""
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _normalize_text(value: Any) -> str:
    """توحيد النص لأغراض البحث غير الحساس لحالة الأحرف."""
    return str(value or "").strip().casefold()


def _matches_query(item: JsonObject, query: str, fields: tuple[str, ...]) -> bool:
    """البحث في مجموعة محددة من الحقول النصية."""
    needle = _normalize_text(query)
    if not needle:
        return True

    return any(
        needle in _normalize_text(item.get(field))
        for field in fields
    )


def _paginate(
    items: list[JsonObject],
    *,
    offset: int,
    limit: int,
) -> JsonObject:
    """تطبيق ترقيم بسيط وثابت على النتائج."""
    total = len(items)
    page_items = items[offset : offset + limit]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "count": len(page_items),
        "has_more": offset + len(page_items) < total,
        "items": page_items,
    }


def _counter(values: list[Any]) -> dict[str, int]:
    """إنشاء توزيع تكراري مرتب حسب الاسم."""
    counts = Counter(
        str(value)
        for value in values
        if value not in (None, "")
    )
    return dict(sorted(counts.items()))


def _indicator_quality_value(indicator: JsonObject, field: str) -> Any:
    quality = indicator.get("quality", {})
    if not isinstance(quality, dict):
        return None
    return quality.get(field)


def _indicator_publication_value(indicator: JsonObject, field: str) -> Any:
    publication = indicator.get("publication", {})
    if not isinstance(publication, dict):
        return None
    return publication.get(field)


@router.get("", summary="ملخص سجل البيانات والمؤشرات")
def metadata_summary() -> JsonObject:
    """ملخص تنفيذي للسجلين مع التوزيعات وحالة التحقق."""
    sources_registry = load_data_sources()
    indicators_registry = load_indicator_registry()

    sources = _as_list(sources_registry.get("sources"))
    indicators = _as_list(indicators_registry.get("indicators"))

    sources_validation = validate_data_sources_registry()
    indicators_validation = validate_indicator_registry()

    return {
        "registry": {
            "sources": {
                "name_ar": sources_registry.get("registry_name_ar"),
                "name_en": sources_registry.get("registry_name_en"),
                "schema_version": sources_registry.get("schema_version"),
                "reference_year": sources_registry.get("reference_year"),
                "last_updated": sources_registry.get("last_updated"),
                "count": len(sources),
            },
            "indicators": {
                "name_ar": indicators_registry.get("registry_name_ar"),
                "name_en": indicators_registry.get("registry_name_en"),
                "standard_id": indicators_registry.get("standard_id"),
                "standard_version": indicators_registry.get("standard_version"),
                "schema_version": indicators_registry.get("schema_version"),
                "reference_year": indicators_registry.get("reference_year"),
                "last_updated": indicators_registry.get("last_updated"),
                "count": len(indicators),
                "national_registry_target": (
                    indicators_registry.get("summary", {}).get(
                        "national_registry_target"
                    )
                    if isinstance(indicators_registry.get("summary"), dict)
                    else None
                ),
            },
        },
        "distributions": {
            "sources_by_type": _counter(
                [source.get("source_type") for source in sources]
            ),
            "sources_by_status": _counter(
                [source.get("status") for source in sources]
            ),
            "sources_by_integration_status": _counter(
                [source.get("integration_status") for source in sources]
            ),
            "indicators_by_category": _counter(
                [indicator.get("category") for indicator in indicators]
            ),
            "indicators_by_type": _counter(
                [indicator.get("indicator_type") for indicator in indicators]
            ),
            "indicators_by_status": _counter(
                [
                    _indicator_quality_value(indicator, "status")
                    for indicator in indicators
                ]
            ),
        },
        "validation": {
            "sources": sources_validation,
            "indicators": indicators_validation,
        },
    }


@router.get("/catalog", summary="كتالوج التصنيفات الموحدة")
def metadata_catalog() -> JsonObject:
    """إرجاع القيم الموحدة المستخدمة في الفلاتر والنماذج والواجهات."""
    return {
        "catalog": get_enum_catalog(),
    }


@router.get("/validation", summary="فحص شامل للبيانات والسجلات")
def metadata_validation() -> JsonObject:
    """تشغيل بوابة الجودة وإرجاع جميع نتائج التحقق."""
    return validate_all_data()


@router.get("/sources", summary="قائمة مصادر البيانات")
def list_data_sources(
    q: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="بحث في المعرف والرمز والاسم والجهة والوحدة المسؤولة.",
    ),
    source_type: DataSourceType | None = Query(default=None),
    status: DataStatus | None = Query(default=None),
    validation_status: ValidationStatus | None = Query(default=None),
    confidence_level: ConfidenceLevel | None = Query(default=None),
    update_frequency: UpdateFrequency | None = Query(default=None),
    geography_level: GeographyLevel | None = Query(default=None),
    integration_status: str | None = Query(
        default=None,
        min_length=1,
        max_length=50,
    ),
    is_primary_source: bool | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> JsonObject:
    """البحث والتصفية في السجل الوطني لمصادر البيانات."""
    registry = load_data_sources()
    sources = _as_list(registry.get("sources"))

    filtered: list[JsonObject] = []

    for source in sources:
        if q and not _matches_query(
            source,
            q,
            (
                "source_id",
                "code",
                "name_ar",
                "name_en",
                "organization_ar",
                "organization_en",
                "responsible_unit_ar",
                "responsible_unit_en",
            ),
        ):
            continue

        if source_type and source.get("source_type") != source_type.value:
            continue
        if status and source.get("status") != status.value:
            continue
        if (
            validation_status
            and source.get("validation_status") != validation_status.value
        ):
            continue
        if (
            confidence_level
            and source.get("confidence_level") != confidence_level.value
        ):
            continue
        if (
            update_frequency
            and source.get("update_frequency") != update_frequency.value
        ):
            continue
        if (
            geography_level
            and source.get("geography_level") != geography_level.value
        ):
            continue
        if (
            integration_status
            and _normalize_text(source.get("integration_status"))
            != _normalize_text(integration_status)
        ):
            continue
        if (
            is_primary_source is not None
            and source.get("is_primary_source") is not is_primary_source
        ):
            continue

        filtered.append(source)

    filtered.sort(
        key=lambda item: (
            _normalize_text(item.get("source_id")),
            _normalize_text(item.get("name_en")),
        )
    )

    response = _paginate(filtered, offset=offset, limit=limit)
    response["filters"] = {
        "q": q,
        "source_type": source_type.value if source_type else None,
        "status": status.value if status else None,
        "validation_status": (
            validation_status.value if validation_status else None
        ),
        "confidence_level": (
            confidence_level.value if confidence_level else None
        ),
        "update_frequency": (
            update_frequency.value if update_frequency else None
        ),
        "geography_level": (
            geography_level.value if geography_level else None
        ),
        "integration_status": integration_status,
        "is_primary_source": is_primary_source,
    }
    return response


@router.get(
    "/sources/{source_id}/indicators",
    summary="المؤشرات المرتبطة بمصدر بيانات",
)
def source_indicators(source_id: str) -> JsonObject:
    """إرجاع كل المؤشرات التي تعتمد على مصدر محدد."""
    source = get_data_source(source_id)
    if source is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "DATA_SOURCE_NOT_FOUND",
                "message_ar": "مصدر البيانات غير موجود في السجل.",
                "source_id": source_id,
            },
        )

    registry = load_indicator_registry()
    indicators = _as_list(registry.get("indicators"))
    linked = [
        indicator
        for indicator in indicators
        if source_id in indicator.get("data_source_ids", [])
    ]

    linked.sort(
        key=lambda item: (
            _normalize_text(item.get("category")),
            _normalize_text(item.get("indicator_id")),
        )
    )

    return {
        "source": source,
        "indicators_count": len(linked),
        "indicators": linked,
    }


@router.get("/sources/{source_id}", summary="تفاصيل مصدر بيانات")
def data_source_detail(source_id: str) -> JsonObject:
    """تفاصيل مصدر واحد مع عدد المؤشرات التي تعتمد عليه."""
    source = get_data_source(source_id)
    if source is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "DATA_SOURCE_NOT_FOUND",
                "message_ar": "مصدر البيانات غير موجود في السجل.",
                "source_id": source_id,
            },
        )

    indicator_registry = load_indicator_registry()
    indicators = _as_list(indicator_registry.get("indicators"))
    linked_ids = [
        str(indicator.get("indicator_id"))
        for indicator in indicators
        if source_id in indicator.get("data_source_ids", [])
        and indicator.get("indicator_id")
    ]

    return {
        "source": source,
        "linked_indicators_count": len(linked_ids),
        "linked_indicator_ids": sorted(linked_ids),
    }


@router.get("/indicators", summary="قائمة المؤشرات السياحية")
def list_indicators(
    q: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="بحث في المعرف والرمز والاسم والوصف.",
    ),
    category: IndicatorCategory | None = Query(default=None),
    indicator_type: IndicatorType | None = Query(default=None),
    measurement_unit: MeasurementUnit | None = Query(default=None),
    status: DataStatus | None = Query(default=None),
    validation_status: ValidationStatus | None = Query(default=None),
    confidence_level: ConfidenceLevel | None = Query(default=None),
    source_id: str | None = Query(
        default=None,
        min_length=1,
        max_length=50,
    ),
    publishable: bool | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> JsonObject:
    """البحث والتصفية في السجل التشغيلي للمؤشرات."""
    registry = load_indicator_registry()
    indicators = _as_list(registry.get("indicators"))

    if source_id and source_id not in get_data_source_index():
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_SOURCE_FILTER",
                "message_ar": "معرف مصدر البيانات المستخدم في الفلتر غير مسجل.",
                "source_id": source_id,
            },
        )

    filtered: list[JsonObject] = []

    for indicator in indicators:
        if q and not _matches_query(
            indicator,
            q,
            (
                "indicator_id",
                "code",
                "name_ar",
                "name_en",
                "description_ar",
                "description_en",
            ),
        ):
            continue

        if category and indicator.get("category") != category.value:
            continue
        if (
            indicator_type
            and indicator.get("indicator_type") != indicator_type.value
        ):
            continue
        if (
            measurement_unit
            and indicator.get("measurement_unit") != measurement_unit.value
        ):
            continue
        if status and _indicator_quality_value(indicator, "status") != status.value:
            continue
        if (
            validation_status
            and _indicator_quality_value(indicator, "validation_status")
            != validation_status.value
        ):
            continue
        if (
            confidence_level
            and _indicator_quality_value(indicator, "confidence_level")
            != confidence_level.value
        ):
            continue
        if source_id and source_id not in indicator.get("data_source_ids", []):
            continue
        if (
            publishable is not None
            and _indicator_publication_value(indicator, "publishable")
            is not publishable
        ):
            continue

        filtered.append(indicator)

    filtered.sort(
        key=lambda item: (
            int(
                _indicator_publication_value(item, "display_order")
                or 999999
            ),
            _normalize_text(item.get("indicator_id")),
        )
    )

    response = _paginate(filtered, offset=offset, limit=limit)
    response["filters"] = {
        "q": q,
        "category": category.value if category else None,
        "indicator_type": indicator_type.value if indicator_type else None,
        "measurement_unit": (
            measurement_unit.value if measurement_unit else None
        ),
        "status": status.value if status else None,
        "validation_status": (
            validation_status.value if validation_status else None
        ),
        "confidence_level": (
            confidence_level.value if confidence_level else None
        ),
        "source_id": source_id,
        "publishable": publishable,
    }
    return response


@router.get(
    "/indicators/code/{code}",
    summary="تفاصيل مؤشر حسب الرمز البرمجي",
)
def indicator_detail_by_code(code: str) -> JsonObject:
    """إرجاع تعريف مؤشر باستخدام code بدل indicator_id."""
    indicator = get_indicator(code=code)
    if indicator is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "INDICATOR_NOT_FOUND",
                "message_ar": "المؤشر غير موجود في السجل.",
                "indicator_code": code,
            },
        )

    sources_index = get_data_source_index()
    resolved_sources = [
        sources_index[source_id]
        for source_id in indicator.get("data_source_ids", [])
        if source_id in sources_index
    ]

    return {
        "indicator": indicator,
        "resolved_sources_count": len(resolved_sources),
        "resolved_sources": resolved_sources,
    }


@router.get(
    "/indicators/{indicator_id}",
    summary="تفاصيل مؤشر حسب المعرف الوطني",
)
def indicator_detail(indicator_id: str) -> JsonObject:
    """إرجاع تعريف المؤشر وربطه بسجلات مصادره."""
    indicator = get_indicator(indicator_id=indicator_id)
    if indicator is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "INDICATOR_NOT_FOUND",
                "message_ar": "المؤشر غير موجود في السجل.",
                "indicator_id": indicator_id,
            },
        )

    sources_index = get_data_source_index()
    resolved_sources = [
        sources_index[source_id]
        for source_id in indicator.get("data_source_ids", [])
        if source_id in sources_index
    ]

    missing_source_ids = [
        source_id
        for source_id in indicator.get("data_source_ids", [])
        if source_id not in sources_index
    ]

    return {
        "indicator": indicator,
        "resolved_sources_count": len(resolved_sources),
        "resolved_sources": resolved_sources,
        "missing_source_ids": missing_source_ids,
    }

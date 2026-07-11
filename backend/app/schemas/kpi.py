"""
Pydantic response schemas for the Libyan National Tourism Intelligence Platform.

هذا الملف يحدد العقود الرسمية لاستجابات محرك المؤشرات، ويهدف إلى:
- تثبيت شكل البيانات بين Backend وFrontend.
- توثيق واجهات API تلقائيًا في Swagger.
- اكتشاف أي تغيير غير مقصود في أسماء الحقول أو أنواعها.
- دعم المؤشرات الوطنية والمدن والقارات ولوحة القيادة.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# =========================================================
# Base models
# =========================================================

class APIModel(BaseModel):
    """
    النموذج الأساسي لجميع استجابات المنصة.

    يسمح مؤقتًا بحقول إضافية حتى لا تتعطل المسارات الحالية
    أثناء الانتقال التدريجي إلى عقود API صارمة.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class BilingualName(APIModel):
    """اسم ثنائي اللغة."""

    name_ar: str | None = None
    name_en: str | None = None


# =========================================================
# Indicator schemas
# =========================================================

class IndicatorDefinitionSummary(APIModel):
    """
    تعريف مختصر للمؤشر مأخوذ من السجل الوطني للمؤشرات.
    """

    indicator_id: str | None = None
    code: str
    name_ar: str | None = None
    name_en: str | None = None
    category: str | None = None
    indicator_type: str | None = None
    measurement_unit: str | None = None
    direction: str | None = None
    status: str | None = None
    validation_status: str | None = None
    confidence_level: str | None = None


class KPIValue(APIModel):
    """
    نتيجة مؤشر قابل للحساب.
    """

    indicator_id: str | None = None
    code: str
    name_ar: str | None = None
    name_en: str | None = None

    value: int | float | str | None = None
    measurement_unit: str | None = None

    calculation_status: Literal[
        "calculated",
        "available",
        "unavailable",
        "not_applicable",
    ] = "calculated"

    reference_year: int | None = None
    source_ids: list[str] = Field(default_factory=list)

    confidence_level: str | None = None
    validation_status: str | None = None
    notes: str | None = None
    notes_ar: str | None = None


class UnavailableKPI(APIModel):
    """
    مؤشر معرّف في السجل، لكن مدخلاته غير متوفرة حاليًا.
    """

    indicator_id: str | None = None
    code: str
    name_ar: str | None = None
    name_en: str | None = None

    value: None = None
    measurement_unit: str | None = None
    calculation_status: Literal["unavailable"] = "unavailable"

    missing_inputs: list[str] = Field(default_factory=list)
    reason: str | None = None
    reason_ar: str | None = None


class SingleIndicatorResponse(APIModel):
    """
    استجابة مؤشر واحد سواء كان محسوبًا أو غير متاح.
    """

    indicator_id: str | None = None
    code: str
    name_ar: str | None = None
    name_en: str | None = None

    value: int | float | str | None = None
    measurement_unit: str | None = None
    calculation_status: str

    reference_year: int | None = None
    source_ids: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)

    confidence_level: str | None = None
    validation_status: str | None = None
    reason: str | None = None
    reason_ar: str | None = None
    notes: str | None = None
    notes_ar: str | None = None


# =========================================================
# Data reconciliation schemas
# =========================================================

class ReconciliationItem(APIModel):
    """
    نتيجة مطابقة مجموع تفصيلي مع قيمة وطنية مرجعية.
    """

    name: str | None = None
    name_ar: str | None = None

    calculated_total: int | float | None = None
    reported_total: int | float | None = None
    difference: int | float = 0

    matched: bool | None = None
    status: Literal[
        "matched",
        "warning",
        "mismatch",
        "not_checked",
    ] | None = None


class ReconciliationSummary(APIModel):
    """
    ملخص عمليات المطابقة بين البيانات التفصيلية والوطنية.
    """

    status: str | None = None
    checks_count: int | None = None
    matched_count: int | None = None
    mismatched_count: int | None = None
    checks: dict[str, ReconciliationItem] = Field(default_factory=dict)


# =========================================================
# National KPI schemas
# =========================================================

class NationalKPIResponse(APIModel):
    """
    الحزمة الوطنية الكاملة الناتجة عن محرك المؤشرات.
    """

    reference_year: int
    status: str = "calculated"

    calculated_indicators_count: int = 0
    unavailable_indicators_count: int = 0

    indicators: list[KPIValue] = Field(default_factory=list)
    unavailable_indicators: list[UnavailableKPI] = Field(
        default_factory=list
    )

    reconciliation: dict[str, Any] | ReconciliationSummary = Field(
        default_factory=dict
    )

    generated_at: str | None = None
    engine_version: str | None = None


class LegacyKPIResponse(APIModel):
    """
    استجابة المسار القديم /api/kpis للمحافظة على التوافق.
    """

    year: int
    country: str | None = None
    system: str | None = None
    source: str | None = None


class NationalSummaryResponse(APIModel):
    """
    الملخص الوطني السريع المستخدم في بطاقات Dashboard.
    """

    year: int
    international_tourists: int = 0
    tourism_trips: int = 0
    hotel_guests: int = 0
    hotels: int = 0
    tourism_companies: int = 0
    heritage_visitors: int = 0
    summer_revenue_lyd: int | float = 0


# =========================================================
# City KPI schemas
# =========================================================

class CityKPIItem(APIModel):
    """
    مؤشرات مدينة أو فرع سياحي واحد.
    """

    id: str
    name_ar: str
    name_en: str | None = None

    libyans: int = 0
    arabs: int = 0
    foreigners: int = 0
    total_guests: int = 0

    share_percent: float | None = None
    domestic_share_percent: float | None = None
    arab_share_percent: float | None = None
    foreign_share_percent: float | None = None

    national_rank: int | None = None

    companies: int | None = None
    offices: int | None = None
    accommodation_total: int | None = None
    hotels: int | None = None
    hotel_apartments: int | None = None
    tourist_villages: int | None = None

    lat: float | None = None
    lng: float | None = None


class CitiesKPIResponse(APIModel):
    """
    قائمة مؤشرات المدن مرتبة وفق الأداء أو عدد النزلاء.
    """

    reference_year: int | None = None
    year: int | None = None

    total_guests: int = 0
    cities_count: int = 0

    items: list[CityKPIItem] = Field(default_factory=list)
    cities: list[CityKPIItem] = Field(default_factory=list)

    generated_at: str | None = None


class SingleCityKPIResponse(CityKPIItem):
    """استجابة مدينة واحدة."""

    reference_year: int | None = None


# =========================================================
# Continent KPI schemas
# =========================================================

class ContinentKPIItem(APIModel):
    """
    توزيع السياح الدوليين حسب القارة.
    """

    id: str
    name_ar: str
    name_en: str

    tourists: int = 0
    share_percent: float | None = None
    national_rank: int | None = None


class ContinentsKPIResponse(APIModel):
    """
    الحصة السوقية للقارات والأسواق المصدرة.
    """

    reference_year: int | None = None
    year: int | None = None

    total: int = 0
    total_international_tourists: int | None = None
    continents_count: int | None = None

    items: list[ContinentKPIItem] = Field(default_factory=list)
    generated_at: str | None = None


# =========================================================
# Dashboard schemas
# =========================================================

class DashboardCounts(APIModel):
    """
    أعداد المؤشرات المتاحة وغير المتاحة في لقطة اللوحة.
    """

    calculated_indicators: int = 0
    unavailable_indicators: int = 0
    cities: int = 0
    continents: int = 0


class DashboardKPIResponse(APIModel):
    """
    الحزمة الموحدة التي تستهلكها الواجهة الأمامية للوحة المؤشرات.
    """

    reference_year: int
    status: str = "ready"

    national: NationalKPIResponse | dict[str, Any]
    top_cities: list[CityKPIItem] = Field(default_factory=list)
    continents: list[ContinentKPIItem] = Field(default_factory=list)

    unavailable_indicators: list[
        UnavailableKPI | dict[str, Any]
    ] = Field(default_factory=list)

    reconciliation: dict[str, Any] | ReconciliationSummary = Field(
        default_factory=dict
    )

    counts: DashboardCounts | dict[str, Any] | None = None
    additional_metrics: dict[str, Any] = Field(default_factory=dict)

    generated_at: str | None = None


# =========================================================
# Error and status schemas
# =========================================================

class APIErrorResponse(APIModel):
    """
    صيغة موحدة لأخطاء واجهات المؤشرات.
    """

    status: str = "error"
    message: str | None = None
    message_ar: str | None = None
    detail: str | dict[str, Any] | list[Any] | None = None


class APIStatusResponse(APIModel):
    """
    استجابة حالة عامة.
    """

    status: str
    message: str | None = None
    message_ar: str | None = None

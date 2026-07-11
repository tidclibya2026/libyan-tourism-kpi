"""
Pydantic schemas for the Libyan National Tourism Intelligence Platform.

هذا الملف يحدد عقود الاستجابة الرسمية الخاصة بمحرك المؤشرات:
- المؤشرات الوطنية.
- المؤشر الواحد.
- مؤشرات المدن.
- مؤشرات القارات.
- حزمة Dashboard.
- استجابات الأخطاء والحالة.

تمت مراعاة التوافق مع مخرجات KPI Engine الحالية،
خصوصًا أن حقل notes قد يأتي كنص أو قائمة.
"""

from __future__ import annotations

from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


# =========================================================
# Base model
# =========================================================

class APIModel(BaseModel):
    """
    النموذج الأساسي لجميع استجابات المنصة.

    نسمح مؤقتًا بالحقول الإضافية أثناء التطوير المرحلي
    حتى لا تتعطل الواجهات عند إضافة حقول متوافقة.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


# =========================================================
# Shared schemas
# =========================================================

class EngineMetadata(APIModel):
    """
    بيانات إصدار محرك المؤشرات ووقت الحساب.
    """

    name: str
    version: str

    standard: str | None = None
    calculated_at: str | None = None


class KPIValue(APIModel):
    """
    نتيجة مؤشر سياحي واحد.

    يدعم:
    - المؤشرات الرقمية.
    - المؤشرات غير المتاحة.
    - المؤشرات متعددة الأبعاد.
    - الملاحظات كنص أو قائمة.
    """

    indicator_id: str | None = None
    code: str

    name_ar: str | None = None
    name_en: str | None = None

    category: str | None = None
    indicator_type: str | None = None
    measurement_unit: str | None = None

    reference_year: int | None = None

    value: Any = None

    calculation_status: str

    calculation_method: str | None = None
    registered_formula: str | None = None

    inputs: dict[str, Any] = Field(
        default_factory=dict
    )

    data_source_ids: list[str] = Field(
        default_factory=list
    )

    quality: dict[str, Any] = Field(
        default_factory=dict
    )

    publication: dict[str, Any] = Field(
        default_factory=dict
    )

    notes: list[str] = Field(
        default_factory=list
    )

    @field_validator(
        "notes",
        mode="before",
    )
    @classmethod
    def normalize_notes(
        cls,
        value: Any,
    ) -> list[str]:
        """
        توحيد الملاحظات في صورة قائمة نصية.

        يقبل:
        - None
        - نصًا واحدًا
        - قائمة
        - Tuple
        - Set
        """

        if value is None:
            return []

        if isinstance(value, str):
            cleaned_value = value.strip()

            if not cleaned_value:
                return []

            return [cleaned_value]

        if isinstance(
            value,
            (list, tuple, set),
        ):
            return [
                str(item).strip()
                for item in value
                if (
                    item is not None
                    and str(item).strip()
                )
            ]

        cleaned_value = str(value).strip()

        if not cleaned_value:
            return []

        return [cleaned_value]


# =========================================================
# National KPI schemas
# =========================================================

class LegacyKPIResponse(APIModel):
    """
    استجابة المسار القديم:

    /api/kpis

    يسمح بالحقول الإضافية لأن الملف الوطني يحتوي
    على عدد كبير من القيم الأساسية.
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
    hotel_apartments: int = 0
    hotels_and_apartments: int = 0
    tourist_villages: int = 0
    chalets: int = 0

    hotel_rooms: int = 0
    hotel_beds: int = 0

    tourism_companies: int = 0
    renewed_companies: int = 0

    handicrafts: int = 0
    restaurants_cafes: int = 0

    flights: int = 0
    air_passengers: int = 0

    heritage_visitors: int = 0
    summer_revenue_lyd: int | float = 0


class NationalKPIResponse(APIModel):
    """
    الحزمة الوطنية الكاملة الناتجة عن KPI Engine.
    """

    engine: EngineMetadata

    reference_year: int
    status: str

    calculated_indicators_count: int = 0
    unavailable_indicators_count: int = 0

    indicators: list[KPIValue] = Field(
        default_factory=list
    )

    unavailable_indicators: list[KPIValue] = Field(
        default_factory=list
    )

    reconciliation: dict[str, Any] = Field(
        default_factory=dict
    )

    supplementary_metrics: dict[str, Any] = Field(
        default_factory=dict
    )


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
    calculated_total_guests: int = 0

    share_percent: float | int | None = None

    domestic_share_percent: float | int | None = None
    arab_share_percent: float | int | None = None
    foreign_share_percent: float | int | None = None

    national_rank: int | None = None

    companies: int | None = None
    offices: int | None = None

    accommodation_total: int | None = None
    hotels: int | None = None
    hotel_apartments: int | None = None
    tourist_villages: int | None = None

    lat: float | None = None
    lng: float | None = None

    calculation_warnings: list[str] = Field(
        default_factory=list
    )

    @field_validator(
        "calculation_warnings",
        mode="before",
    )
    @classmethod
    def normalize_calculation_warnings(
        cls,
        value: Any,
    ) -> list[str]:
        """
        توحيد تحذيرات الحساب في قائمة نصية.
        """

        if value is None:
            return []

        if isinstance(value, str):
            cleaned_value = value.strip()

            if not cleaned_value:
                return []

            return [cleaned_value]

        if isinstance(
            value,
            (list, tuple, set),
        ):
            return [
                str(item).strip()
                for item in value
                if (
                    item is not None
                    and str(item).strip()
                )
            ]

        cleaned_value = str(value).strip()

        if not cleaned_value:
            return []

        return [cleaned_value]


class CitiesKPIResponse(APIModel):
    """
    قائمة المدن مرتبة حسب إجمالي النزلاء.
    """

    year: int

    national_total_guests: int
    cities_count: int

    items: list[CityKPIItem] = Field(
        default_factory=list
    )


class SingleCityKPIResponse(APIModel):
    """
    استجابة مدينة واحدة كما يعيدها محرك المؤشرات.
    """

    year: int
    national_total_guests: int

    city: CityKPIItem


# =========================================================
# Continent KPI schemas
# =========================================================

class ContinentKPIItem(APIModel):
    """
    الحصة السوقية لقارة واحدة.
    """

    id: str

    name_ar: str
    name_en: str

    tourists: int = 0

    market_share_percent: float | int | None = None
    market_rank: int | None = None


class ContinentsKPIResponse(APIModel):
    """
    توزيع السياح الدوليين حسب القارات.
    """

    year: int

    international_tourists_total: int
    continents_count: int

    items: list[ContinentKPIItem] = Field(
        default_factory=list
    )


# =========================================================
# Dashboard schemas
# =========================================================

class DashboardNationalSection(APIModel):
    """
    القسم الوطني داخل لقطة Dashboard.
    """

    indicators: list[KPIValue] = Field(
        default_factory=list
    )

    unavailable_indicators: list[KPIValue] = Field(
        default_factory=list
    )

    reconciliation: dict[str, Any] = Field(
        default_factory=dict
    )

    supplementary_metrics: dict[str, Any] = Field(
        default_factory=dict
    )


class DashboardCitiesSection(APIModel):
    """
    قسم المدن الأعلى ترتيبًا داخل لقطة Dashboard.
    """

    national_total_guests: int
    cities_count: int

    top_items: list[CityKPIItem] = Field(
        default_factory=list
    )


class DashboardKPIResponse(APIModel):
    """
    الحزمة الموحدة الجاهزة للاستهلاك
    من الواجهة الأمامية.
    """

    engine: EngineMetadata
    reference_year: int

    national: DashboardNationalSection
    cities: DashboardCitiesSection
    continents: ContinentsKPIResponse


# =========================================================
# Validation and reconciliation schemas
# =========================================================

class ReconciliationItem(APIModel):
    """
    نتيجة مطابقة قيمة تفصيلية مع القيمة الوطنية.
    """

    name: str | None = None
    name_ar: str | None = None

    calculated_total: int | float | None = None
    reported_total: int | float | None = None

    difference: int | float = 0

    matched: bool | None = None
    status: str | None = None


class ReconciliationSummary(APIModel):
    """
    ملخص عمليات مطابقة المجاميع.
    """

    status: str | None = None

    checks_count: int = 0
    matched_count: int = 0
    mismatched_count: int = 0

    checks: dict[str, ReconciliationItem] = Field(
        default_factory=dict
    )


# =========================================================
# Generic status and error schemas
# =========================================================

class APIErrorResponse(APIModel):
    """
    صيغة موحدة لأخطاء واجهات المؤشرات.
    """

    status: str = "error"

    message: str | None = None
    message_ar: str | None = None

    detail: Any = None


class APIStatusResponse(APIModel):
    """
    استجابة حالة عامة.
    """

    status: str

    message: str | None = None
    message_ar: str | None = None
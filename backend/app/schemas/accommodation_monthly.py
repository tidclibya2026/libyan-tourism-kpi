"""
Pydantic schemas for monthly accommodation operations.

نماذج الاستجابة الخاصة ببيانات الإيواء التشغيلية الشهرية،
ومؤشرات الإشغال والليالي والإيرادات.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.schemas.kpi import APIModel


class AccommodationMonthlyRecord(APIModel):
    """سجل تشغيلي شهري لمنشأة إيواء واحدة."""

    facility_id: str
    facility_name: str

    branch: str = ""
    municipality: str = ""

    year: int
    month: int

    available_rooms: int | float
    sold_room_nights: int | float

    available_beds: int | float
    occupied_bed_nights: int | float

    libyan_guests: int | float
    arab_guests: int | float
    foreign_guests: int | float

    tourist_nights: int | float
    room_revenue_lyd: int | float

    source_reference: str = ""
    verification_status: str = ""


class AccommodationMonthlyTotals(APIModel):
    """المجاميع التشغيلية ضمن نطاق التصفية."""

    reporting_facilities: int
    months_covered: int

    available_room_nights: int | float | None = None
    sold_room_nights: int | float | None = None

    available_bed_nights: int | float | None = None
    occupied_bed_nights: int | float | None = None

    libyan_guests: int | float | None = None
    arab_guests: int | float | None = None
    foreign_guests: int | float | None = None
    total_guests: int | float | None = None

    tourist_nights: int | float | None = None
    room_revenue_lyd: int | float | None = None


class AccommodationMonthlyIndicator(APIModel):
    """نتيجة مؤشر تشغيلي شهري واحد."""

    code: str
    name_ar: str

    value: int | float | None = None
    unit: str

    status: str
    quality_status: str

    calculation_method: str | None = None

    inputs: dict[str, Any] = Field(
        default_factory=dict
    )

    missing_inputs: list[str] = Field(
        default_factory=list
    )

    note_ar: str | None = None


class AccommodationMonthlyReadiness(APIModel):
    """جاهزية مؤشرات الإيواء التشغيلية."""

    total_indicators: int
    available_indicators: int
    unavailable_indicators: int

    readiness_percent: int | float
    operational_data_complete: bool


class AccommodationMonthlyTrend(APIModel):
    """نقطة زمنية ضمن الاتجاه التشغيلي الشهري."""

    year: int
    month: int

    records_count: int
    reporting_facilities: int

    total_guests: int | float | None = None
    tourist_nights: int | float | None = None
    sold_room_nights: int | float | None = None

    room_occupancy_rate: int | float | None = None
    bed_occupancy_rate: int | float | None = None
    average_length_of_stay: int | float | None = None
    average_daily_rate: int | float | None = None
    revenue_per_available_room: int | float | None = None


class AccommodationMonthlyResponse(APIModel):
    """الاستجابة الكاملة لمحور الإيواء التشغيلي الشهري."""

    schema_version: str

    module: str
    module_name_ar: str

    year: int
    generated_at: str

    status: str

    records_count: int
    source_records_count: int

    filters_applied: dict[str, Any] = Field(
        default_factory=dict
    )

    filter_options: dict[str, Any] = Field(
        default_factory=dict
    )

    totals: AccommodationMonthlyTotals

    indicators: dict[
        str,
        AccommodationMonthlyIndicator,
    ] = Field(
        default_factory=dict
    )

    readiness: AccommodationMonthlyReadiness

    trends: list[
        AccommodationMonthlyTrend
    ] = Field(
        default_factory=list
    )

    records: list[
        AccommodationMonthlyRecord
    ] | None = None

    methodology: dict[str, Any] = Field(
        default_factory=dict
    )


class AccommodationMonthlySummaryResponse(APIModel):
    """استجابة الملخص دون السجلات والاتجاهات."""

    schema_version: str

    module: str
    module_name_ar: str

    year: int
    generated_at: str

    status: str

    records_count: int
    source_records_count: int

    filters_applied: dict[str, Any] = Field(
        default_factory=dict
    )

    filter_options: dict[str, Any] = Field(
        default_factory=dict
    )

    totals: AccommodationMonthlyTotals

    indicators: dict[
        str,
        AccommodationMonthlyIndicator,
    ] = Field(
        default_factory=dict
    )

    readiness: AccommodationMonthlyReadiness

    methodology: dict[str, Any] = Field(
        default_factory=dict
    )


class AccommodationMonthlyRecordsResponse(APIModel):
    """قائمة السجلات التشغيلية الشهرية."""

    module: str
    module_name_ar: str

    year: int
    status: str
    records_count: int

    filters_applied: dict[str, Any] = Field(
        default_factory=dict
    )

    items: list[
        AccommodationMonthlyRecord
    ] = Field(
        default_factory=list
    )


class AccommodationMonthlyTrendsResponse(APIModel):
    """اتجاهات مؤشرات الإيواء حسب الشهر."""

    module: str
    module_name_ar: str

    year: int
    status: str
    records_count: int

    filters_applied: dict[str, Any] = Field(
        default_factory=dict
    )

    items: list[
        AccommodationMonthlyTrend
    ] = Field(
        default_factory=list
    )


class AccommodationFacilityHistoryResponse(APIModel):
    """السجل التشغيلي التاريخي لمنشأة محددة."""

    module: str

    facility_id: str
    facility_name: str

    records_count: int

    items: list[
        AccommodationMonthlyRecord
    ] = Field(
        default_factory=list
    )
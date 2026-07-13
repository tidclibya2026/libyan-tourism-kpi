"""
Pydantic schemas for the accommodation module.

تحدد هذه النماذج عقود API الخاصة بمحور:
- الإيواء السياحي.
- الطاقة الاستيعابية.
- توزيع النزلاء.
- مؤشرات الإشغال والإيرادات.
- جاهزية البيانات التشغيلية.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.schemas.kpi import APIModel


class AccommodationInventory(APIModel):
    """
    الطاقة الإيوائية الرسمية المسجلة.
    """

    hotels: int | None = None
    hotel_apartments: int | None = None
    hotels_and_apartments: int | None = None

    tourist_villages: int | None = None
    chalets: int | None = None

    reported_rooms: int | None = None
    reported_hotel_beds: int | None = None
    reported_chalet_beds: int | None = None


class AccommodationGuests(APIModel):
    """
    النزلاء المسجلون حسب الجنسية.
    """

    total_guests: int | None = None
    libyan_guests: int | None = None
    arab_guests: int | None = None
    foreign_guests: int | None = None

    reconciliation_status: str | None = None
    source_file: str | None = None


class AccommodationIndicator(APIModel):
    """
    نتيجة مؤشر واحد ضمن محور الإيواء.

    تسمح القيمة بأن تكون None عندما لا تتوفر
    البيانات التشغيلية اللازمة للحساب.
    """

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


class AccommodationReadiness(APIModel):
    """
    جاهزية بيانات مؤشرات الإيواء.
    """

    total_indicators: int
    available_indicators: int
    unavailable_indicators: int

    readiness_percent: int | float | None = None
    operational_data_complete: bool


class AccommodationQualityFlag(APIModel):
    """
    تنبيه أو ملاحظة مرتبطة بجودة بيانات الإيواء.
    """

    code: str
    severity: str
    message_ar: str


class AccommodationResponse(APIModel):
    """
    الاستجابة الكاملة لمحور الإيواء.
    """

    schema_version: str

    module: str
    module_name_ar: str

    year: int
    generated_at: str

    status: str

    inventory: AccommodationInventory
    guests: AccommodationGuests

    indicators: dict[
        str,
        AccommodationIndicator,
    ] = Field(
        default_factory=dict
    )

    readiness: AccommodationReadiness

    quality_flags: list[
        AccommodationQualityFlag
    ] = Field(
        default_factory=list
    )

    methodology: dict[str, Any] = Field(
        default_factory=dict
    )


class AccommodationIndicatorsResponse(APIModel):
    """
    قائمة مؤشرات الإيواء دون إعادة كامل بيانات الوحدة.
    """

    module: str
    module_name_ar: str

    year: int
    status: str

    readiness: AccommodationReadiness

    items: list[
        AccommodationIndicator
    ] = Field(
        default_factory=list
    )
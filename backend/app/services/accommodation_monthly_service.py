"""
Monthly accommodation operational analytics service.

تقوم هذه الطبقة بحساب مؤشرات الإيواء الشهرية
من السجلات الفعلية فقط، ولا تعتبر غياب البيانات صفراً.
"""

from __future__ import annotations

import calendar
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any
from zoneinfo import ZoneInfo

from app.services.data_service import (
    load_accommodation_monthly,
)


JsonObject = dict[str, Any]

DEFAULT_TIMEZONE = "Africa/Tripoli"
DECIMAL_PLACES = 2


class AccommodationMonthlyServiceError(ValueError):
    """خطأ موحد في خدمة الإيواء التشغيلي الشهري."""


def _to_decimal(
    value: Any,
    field_name: str,
) -> Decimal:
    if (
        isinstance(value, bool)
        or not isinstance(
            value,
            (int, float, Decimal),
        )
    ):
        raise AccommodationMonthlyServiceError(
            f"الحقل {field_name} يجب أن يكون رقمياً."
        )

    try:
        number = Decimal(str(value))

    except (
        InvalidOperation,
        ValueError,
    ) as exc:
        raise AccommodationMonthlyServiceError(
            f"تعذر تحويل الحقل {field_name} إلى رقم."
        ) from exc

    if not number.is_finite():
        raise AccommodationMonthlyServiceError(
            f"الحقل {field_name} ليس رقماً صالحاً."
        )

    if number < 0:
        raise AccommodationMonthlyServiceError(
            f"الحقل {field_name} لا يجوز أن يكون سالباً."
        )

    return number


def _json_number(
    value: Decimal,
    *,
    decimal_places: int = DECIMAL_PLACES,
    prefer_integer: bool = False,
) -> int | float:
    quantum = (
        Decimal("1")
        if decimal_places == 0
        else Decimal("1").scaleb(
            -decimal_places
        )
    )

    rounded = value.quantize(
        quantum,
        rounding=ROUND_HALF_UP,
    )

    if (
        prefer_integer
        or rounded
        == rounded.to_integral_value()
    ):
        return int(rounded)

    return float(rounded)


def _safe_ratio(
    numerator: Decimal,
    denominator: Decimal,
    *,
    multiplier: int = 1,
) -> int | float | None:
    if denominator == 0:
        return None

    result = (
        numerator
        / denominator
        * Decimal(str(multiplier))
    )

    return _json_number(result)


def _required_text(
    record: JsonObject,
    field: str,
) -> str:
    value = str(
        record.get(field, "")
    ).strip()

    if not value:
        raise AccommodationMonthlyServiceError(
            f"الحقل {field} مطلوب وغير فارغ."
        )

    return value


def _optional_text(
    record: JsonObject,
    field: str,
) -> str:
    return str(
        record.get(field, "") or ""
    ).strip()


def _integer(
    record: JsonObject,
    field: str,
) -> int:
    number = _to_decimal(
        record.get(field),
        field,
    )

    if (
        number
        != number.to_integral_value()
    ):
        raise AccommodationMonthlyServiceError(
            f"الحقل {field} يجب أن يكون عدداً صحيحاً."
        )

    return int(number)


def _normalize_record(
    record: JsonObject,
    *,
    index: int,
) -> JsonObject:
    facility_id = _required_text(
        record,
        "facility_id",
    )

    facility_name = _required_text(
        record,
        "facility_name",
    )

    year = _integer(
        record,
        "year",
    )

    month = _integer(
        record,
        "month",
    )

    if not 1 <= month <= 12:
        raise AccommodationMonthlyServiceError(
            f"الشهر في السجل رقم {index} "
            "خارج النطاق من 1 إلى 12."
        )

    numeric_fields = (
        "available_rooms",
        "sold_room_nights",
        "available_beds",
        "occupied_bed_nights",
        "libyan_guests",
        "arab_guests",
        "foreign_guests",
        "tourist_nights",
        "room_revenue_lyd",
    )

    numbers = {
        field: _to_decimal(
            record.get(field),
            field,
        )
        for field in numeric_fields
    }

    days = calendar.monthrange(
        year,
        month,
    )[1]

    maximum_room_nights = (
        numbers["available_rooms"]
        * Decimal(days)
    )

    if (
        numbers["sold_room_nights"]
        > maximum_room_nights
    ):
        raise AccommodationMonthlyServiceError(
            f"ليالي الغرف المباعة في السجل رقم {index} "
            "تتجاوز الطاقة الشهرية المتاحة."
        )

    maximum_bed_nights = (
        numbers["available_beds"]
        * Decimal(days)
    )

    if (
        numbers["occupied_bed_nights"]
        > maximum_bed_nights
    ):
        raise AccommodationMonthlyServiceError(
            f"ليالي الأسرة المشغولة في السجل رقم {index} "
            "تتجاوز الطاقة الشهرية المتاحة."
        )

    normalized_numbers = {
        field: _json_number(
            value,
            decimal_places=2,
            prefer_integer=(
                field
                != "room_revenue_lyd"
            ),
        )
        for field, value in numbers.items()
    }

    return {
        "facility_id": facility_id,
        "facility_name": facility_name,
        "branch": _optional_text(
            record,
            "branch",
        ),
        "municipality": _optional_text(
            record,
            "municipality",
        ),
        "year": year,
        "month": month,
        **normalized_numbers,
        "source_reference": _optional_text(
            record,
            "source_reference",
        ),
        "verification_status": _optional_text(
            record,
            "verification_status",
        ),
    }


def _load_normalized_records(
    payload: JsonObject,
) -> list[JsonObject]:
    records = payload.get("records")

    if not isinstance(records, list):
        raise AccommodationMonthlyServiceError(
            "الحقل records يجب أن يكون قائمة."
        )

    normalized_records: list[
        JsonObject
    ] = []

    for index, record in enumerate(
        records,
        start=1,
    ):
        if not isinstance(record, dict):
            raise AccommodationMonthlyServiceError(
                f"السجل رقم {index} ليس كائن JSON."
            )

        normalized_records.append(
            _normalize_record(
                record,
                index=index,
            )
        )

    composite_keys: set[
        tuple[str, int, int]
    ] = set()

    for record in normalized_records:
        key = (
            record["facility_id"],
            record["year"],
            record["month"],
        )

        if key in composite_keys:
            raise AccommodationMonthlyServiceError(
                "يوجد سجل شهري مكرر للمنشأة "
                f"{record['facility_id']} في "
                f"{record['year']}-"
                f"{record['month']:02d}."
            )

        composite_keys.add(key)

    return normalized_records


def _filter_records(
    records: list[JsonObject],
    *,
    month: int | None = None,
    branch: str | None = None,
    municipality: str | None = None,
    verification_status: str | None = None,
    facility_id: str | None = None,
) -> list[JsonObject]:
    if (
        month is not None
        and not 1 <= month <= 12
    ):
        raise AccommodationMonthlyServiceError(
            "قيمة month يجب أن تكون بين 1 و12."
        )

    def normalize(
        value: str | None,
    ) -> str | None:
        if not value:
            return None

        return value.strip().casefold()

    branch_filter = normalize(branch)
    municipality_filter = normalize(
        municipality
    )
    verification_filter = normalize(
        verification_status
    )
    facility_filter = normalize(
        facility_id
    )

    return [
        record
        for record in records
        if (
            month is None
            or record["month"] == month
        )
        and (
            branch_filter is None
            or record["branch"].casefold()
            == branch_filter
        )
        and (
            municipality_filter is None
            or record[
                "municipality"
            ].casefold()
            == municipality_filter
        )
        and (
            verification_filter is None
            or record[
                "verification_status"
            ].casefold()
            == verification_filter
        )
        and (
            facility_filter is None
            or record[
                "facility_id"
            ].casefold()
            == facility_filter
        )
    ]


def _unavailable_indicator(
    *,
    code: str,
    name_ar: str,
    unit: str,
    missing_inputs: list[str],
    note_ar: str,
) -> JsonObject:
    return {
        "code": code,
        "name_ar": name_ar,
        "value": None,
        "unit": unit,
        "status": "unavailable",
        "quality_status": (
            "no_operational_data"
        ),
        "calculation_method": (
            "not_calculated"
        ),
        "inputs": {},
        "missing_inputs": missing_inputs,
        "note_ar": note_ar,
    }


def _available_indicator(
    *,
    code: str,
    name_ar: str,
    value: int | float | None,
    unit: str,
    calculation_method: str,
    inputs: JsonObject,
) -> JsonObject:
    if value is None:
        return _unavailable_indicator(
            code=code,
            name_ar=name_ar,
            unit=unit,
            missing_inputs=[
                name
                for name, item
                in inputs.items()
                if item in (None, 0)
            ],
            note_ar=(
                "تعذر حساب المؤشر لأن المقام "
                "يساوي صفراً أو المدخلات غير مكتملة."
            ),
        )

    return {
        "code": code,
        "name_ar": name_ar,
        "value": value,
        "unit": unit,
        "status": "available",
        "quality_status": (
            "calculated_from_reported_records"
        ),
        "calculation_method": (
            calculation_method
        ),
        "inputs": inputs,
        "missing_inputs": [],
        "note_ar": (
            "قيمة محسوبة من سجلات "
            "الإيواء الشهرية الفعلية."
        ),
    }


def _empty_totals() -> JsonObject:
    return {
        "reporting_facilities": 0,
        "months_covered": 0,
        "available_room_nights": None,
        "sold_room_nights": None,
        "available_bed_nights": None,
        "occupied_bed_nights": None,
        "libyan_guests": None,
        "arab_guests": None,
        "foreign_guests": None,
        "total_guests": None,
        "tourist_nights": None,
        "room_revenue_lyd": None,
    }


def _empty_indicators() -> dict[
    str,
    JsonObject,
]:
    note = (
        "لا توجد سجلات تشغيلية شهرية؛ "
        "لم يتم اعتماد قيمة صفرية للمؤشر."
    )

    definitions = (
        (
            "room_occupancy_rate",
            "نسبة إشغال الغرف",
            "percent",
            [
                "sold_room_nights",
                "available_room_nights",
            ],
        ),
        (
            "bed_occupancy_rate",
            "نسبة إشغال الأسرة",
            "percent",
            [
                "occupied_bed_nights",
                "available_bed_nights",
            ],
        ),
        (
            "average_length_of_stay",
            "متوسط مدة الإقامة",
            "night",
            [
                "tourist_nights",
                "total_guests",
            ],
        ),
        (
            "average_daily_rate",
            "متوسط سعر الغرفة ADR",
            "lyd_per_sold_room_night",
            [
                "room_revenue_lyd",
                "sold_room_nights",
            ],
        ),
        (
            "revenue_per_available_room",
            "العائد على الغرفة المتاحة RevPAR",
            "lyd_per_available_room_night",
            [
                "room_revenue_lyd",
                "available_room_nights",
            ],
        ),
    )

    return {
        code: _unavailable_indicator(
            code=code,
            name_ar=name_ar,
            unit=unit,
            missing_inputs=missing_inputs,
            note_ar=note,
        )
        for (
            code,
            name_ar,
            unit,
            missing_inputs,
        ) in definitions
    }


def _aggregate_records(
    records: list[JsonObject],
) -> tuple[
    JsonObject,
    dict[str, JsonObject],
]:
    available_room_nights = Decimal("0")
    sold_room_nights = Decimal("0")

    available_bed_nights = Decimal("0")
    occupied_bed_nights = Decimal("0")

    libyan_guests = Decimal("0")
    arab_guests = Decimal("0")
    foreign_guests = Decimal("0")

    tourist_nights = Decimal("0")
    room_revenue = Decimal("0")

    for record in records:
        days = calendar.monthrange(
            record["year"],
            record["month"],
        )[1]

        available_room_nights += (
            Decimal(
                str(
                    record[
                        "available_rooms"
                    ]
                )
            )
            * Decimal(days)
        )

        sold_room_nights += Decimal(
            str(
                record[
                    "sold_room_nights"
                ]
            )
        )

        available_bed_nights += (
            Decimal(
                str(
                    record[
                        "available_beds"
                    ]
                )
            )
            * Decimal(days)
        )

        occupied_bed_nights += Decimal(
            str(
                record[
                    "occupied_bed_nights"
                ]
            )
        )

        libyan_guests += Decimal(
            str(record["libyan_guests"])
        )

        arab_guests += Decimal(
            str(record["arab_guests"])
        )

        foreign_guests += Decimal(
            str(record["foreign_guests"])
        )

        tourist_nights += Decimal(
            str(record["tourist_nights"])
        )

        room_revenue += Decimal(
            str(
                record[
                    "room_revenue_lyd"
                ]
            )
        )

    total_guests = (
        libyan_guests
        + arab_guests
        + foreign_guests
    )

    totals = {
        "reporting_facilities": len(
            {
                record["facility_id"]
                for record in records
            }
        ),
        "months_covered": len(
            {
                (
                    record["year"],
                    record["month"],
                )
                for record in records
            }
        ),
        "available_room_nights": (
            _json_number(
                available_room_nights,
                decimal_places=0,
                prefer_integer=True,
            )
        ),
        "sold_room_nights": _json_number(
            sold_room_nights,
            decimal_places=0,
            prefer_integer=True,
        ),
        "available_bed_nights": (
            _json_number(
                available_bed_nights,
                decimal_places=0,
                prefer_integer=True,
            )
        ),
        "occupied_bed_nights": (
            _json_number(
                occupied_bed_nights,
                decimal_places=0,
                prefer_integer=True,
            )
        ),
        "libyan_guests": _json_number(
            libyan_guests,
            decimal_places=0,
            prefer_integer=True,
        ),
        "arab_guests": _json_number(
            arab_guests,
            decimal_places=0,
            prefer_integer=True,
        ),
        "foreign_guests": _json_number(
            foreign_guests,
            decimal_places=0,
            prefer_integer=True,
        ),
        "total_guests": _json_number(
            total_guests,
            decimal_places=0,
            prefer_integer=True,
        ),
        "tourist_nights": _json_number(
            tourist_nights,
            decimal_places=0,
            prefer_integer=True,
        ),
        "room_revenue_lyd": _json_number(
            room_revenue,
        ),
    }

    indicators = {
        "room_occupancy_rate": (
            _available_indicator(
                code=(
                    "room_occupancy_rate"
                ),
                name_ar=(
                    "نسبة إشغال الغرف"
                ),
                value=_safe_ratio(
                    sold_room_nights,
                    available_room_nights,
                    multiplier=100,
                ),
                unit="percent",
                calculation_method=(
                    "sold_room_nights / "
                    "available_room_nights * 100"
                ),
                inputs={
                    "sold_room_nights": (
                        totals[
                            "sold_room_nights"
                        ]
                    ),
                    "available_room_nights": (
                        totals[
                            "available_room_nights"
                        ]
                    ),
                },
            )
        ),
        "bed_occupancy_rate": (
            _available_indicator(
                code="bed_occupancy_rate",
                name_ar=(
                    "نسبة إشغال الأسرة"
                ),
                value=_safe_ratio(
                    occupied_bed_nights,
                    available_bed_nights,
                    multiplier=100,
                ),
                unit="percent",
                calculation_method=(
                    "occupied_bed_nights / "
                    "available_bed_nights * 100"
                ),
                inputs={
                    "occupied_bed_nights": (
                        totals[
                            "occupied_bed_nights"
                        ]
                    ),
                    "available_bed_nights": (
                        totals[
                            "available_bed_nights"
                        ]
                    ),
                },
            )
        ),
        "average_length_of_stay": (
            _available_indicator(
                code=(
                    "average_length_of_stay"
                ),
                name_ar=(
                    "متوسط مدة الإقامة"
                ),
                value=_safe_ratio(
                    tourist_nights,
                    total_guests,
                ),
                unit="night",
                calculation_method=(
                    "tourist_nights / "
                    "total_guests"
                ),
                inputs={
                    "tourist_nights": (
                        totals[
                            "tourist_nights"
                        ]
                    ),
                    "total_guests": (
                        totals[
                            "total_guests"
                        ]
                    ),
                },
            )
        ),
        "average_daily_rate": (
            _available_indicator(
                code="average_daily_rate",
                name_ar=(
                    "متوسط سعر الغرفة ADR"
                ),
                value=_safe_ratio(
                    room_revenue,
                    sold_room_nights,
                ),
                unit=(
                    "lyd_per_sold_room_night"
                ),
                calculation_method=(
                    "room_revenue_lyd / "
                    "sold_room_nights"
                ),
                inputs={
                    "room_revenue_lyd": (
                        totals[
                            "room_revenue_lyd"
                        ]
                    ),
                    "sold_room_nights": (
                        totals[
                            "sold_room_nights"
                        ]
                    ),
                },
            )
        ),
        "revenue_per_available_room": (
            _available_indicator(
                code=(
                    "revenue_per_available_room"
                ),
                name_ar=(
                    "العائد على الغرفة "
                    "المتاحة RevPAR"
                ),
                value=_safe_ratio(
                    room_revenue,
                    available_room_nights,
                ),
                unit=(
                    "lyd_per_available_room_night"
                ),
                calculation_method=(
                    "room_revenue_lyd / "
                    "available_room_nights"
                ),
                inputs={
                    "room_revenue_lyd": (
                        totals[
                            "room_revenue_lyd"
                        ]
                    ),
                    "available_room_nights": (
                        totals[
                            "available_room_nights"
                        ]
                    ),
                },
            )
        ),
    }

    return totals, indicators


def _filter_options(
    records: list[JsonObject],
) -> JsonObject:
    return {
        "months": sorted(
            {
                record["month"]
                for record in records
            }
        ),
        "branches": sorted(
            {
                record["branch"]
                for record in records
                if record["branch"]
            }
        ),
        "municipalities": sorted(
            {
                record["municipality"]
                for record in records
                if record["municipality"]
            }
        ),
        "verification_statuses": sorted(
            {
                record[
                    "verification_status"
                ]
                for record in records
                if record[
                    "verification_status"
                ]
            }
        ),
    }


def _build_trends(
    records: list[JsonObject],
) -> list[JsonObject]:
    trends: list[JsonObject] = []

    periods = sorted(
        {
            (
                record["year"],
                record["month"],
            )
            for record in records
        }
    )

    for year, month in periods:
        monthly_records = [
            record
            for record in records
            if (
                record["year"] == year
                and record["month"]
                == month
            )
        ]

        totals, indicators = (
            _aggregate_records(
                monthly_records
            )
        )

        trends.append(
            {
                "year": year,
                "month": month,
                "records_count": len(
                    monthly_records
                ),
                "reporting_facilities": (
                    totals[
                        "reporting_facilities"
                    ]
                ),
                "total_guests": totals[
                    "total_guests"
                ],
                "tourist_nights": totals[
                    "tourist_nights"
                ],
                "sold_room_nights": totals[
                    "sold_room_nights"
                ],
                "room_occupancy_rate": (
                    indicators[
                        "room_occupancy_rate"
                    ]["value"]
                ),
                "bed_occupancy_rate": (
                    indicators[
                        "bed_occupancy_rate"
                    ]["value"]
                ),
                "average_length_of_stay": (
                    indicators[
                        "average_length_of_stay"
                    ]["value"]
                ),
                "average_daily_rate": (
                    indicators[
                        "average_daily_rate"
                    ]["value"]
                ),
                "revenue_per_available_room": (
                    indicators[
                        "revenue_per_available_room"
                    ]["value"]
                ),
            }
        )

    return trends


def calculate_monthly_accommodation_metrics(
    *,
    month: int | None = None,
    branch: str | None = None,
    municipality: str | None = None,
    verification_status: str | None = None,
    include_records: bool = False,
) -> JsonObject:
    payload = load_accommodation_monthly()

    if not isinstance(payload, dict):
        raise AccommodationMonthlyServiceError(
            "جذر ملف البيانات يجب أن يكون كائن JSON."
        )

    records = _load_normalized_records(
        payload
    )

    filtered_records = _filter_records(
        records,
        month=month,
        branch=branch,
        municipality=municipality,
        verification_status=(
            verification_status
        ),
    )

    if not records:
        module_status = "no_data"
        totals = _empty_totals()
        indicators = _empty_indicators()
        trends: list[JsonObject] = []

    elif not filtered_records:
        module_status = "no_matching_data"
        totals = _empty_totals()
        indicators = _empty_indicators()
        trends = []

    else:
        module_status = "available"

        totals, indicators = (
            _aggregate_records(
                filtered_records
            )
        )

        trends = _build_trends(
            filtered_records
        )

    available_count = sum(
        1
        for indicator
        in indicators.values()
        if indicator["status"]
        == "available"
    )

    response: JsonObject = {
        "schema_version": str(
            payload.get(
                "schema_version",
                "1.0",
            )
        ),
        "module": "accommodation_monthly",
        "module_name_ar": (
            "الإيواء التشغيلي الشهري"
        ),
        "year": int(
            payload.get(
                "year",
                2025,
            )
        ),
        "generated_at": datetime.now(
            ZoneInfo(
                DEFAULT_TIMEZONE
            )
        ).isoformat(),
        "status": module_status,
        "records_count": len(
            filtered_records
        ),
        "source_records_count": len(
            records
        ),
        "filters_applied": {
            "month": month,
            "branch": branch,
            "municipality": municipality,
            "verification_status": (
                verification_status
            ),
        },
        "filter_options": _filter_options(
            records
        ),
        "totals": totals,
        "indicators": indicators,
        "readiness": {
            "total_indicators": len(
                indicators
            ),
            "available_indicators": (
                available_count
            ),
            "unavailable_indicators": (
                len(indicators)
                - available_count
            ),
            "readiness_percent": (
                round(
                    available_count
                    / len(indicators)
                    * 100,
                    2,
                )
                if indicators
                else 0
            ),
            "operational_data_complete": (
                bool(filtered_records)
                and available_count
                == len(indicators)
            ),
        },
        "trends": trends,
        "methodology": {
            "zero_policy": (
                "لا يتم تحويل غياب السجلات "
                "إلى قيمة تشغيلية صفرية."
            ),
            "room_occupancy_formula": (
                "sold_room_nights / "
                "available_room_nights * 100"
            ),
            "bed_occupancy_formula": (
                "occupied_bed_nights / "
                "available_bed_nights * 100"
            ),
            "average_length_of_stay_formula": (
                "tourist_nights / total_guests"
            ),
            "adr_formula": (
                "room_revenue_lyd / "
                "sold_room_nights"
            ),
            "revpar_formula": (
                "room_revenue_lyd / "
                "available_room_nights"
            ),
        },
    }

    if include_records:
        response["records"] = (
            filtered_records
        )

    return response


def get_monthly_accommodation_summary(
    **filters: Any,
) -> JsonObject:
    result = (
        calculate_monthly_accommodation_metrics(
            **filters,
            include_records=False,
        )
    )

    result.pop(
        "trends",
        None,
    )

    result.pop(
        "records",
        None,
    )

    return result


def get_monthly_accommodation_records(
    **filters: Any,
) -> JsonObject:
    result = (
        calculate_monthly_accommodation_metrics(
            **filters,
            include_records=True,
        )
    )

    return {
        "module": result["module"],
        "module_name_ar": result[
            "module_name_ar"
        ],
        "year": result["year"],
        "status": result["status"],
        "records_count": result[
            "records_count"
        ],
        "filters_applied": result[
            "filters_applied"
        ],
        "items": result.get(
            "records",
            [],
        ),
    }


def get_monthly_accommodation_trends(
    **filters: Any,
) -> JsonObject:
    result = (
        calculate_monthly_accommodation_metrics(
            **filters,
            include_records=False,
        )
    )

    return {
        "module": result["module"],
        "module_name_ar": result[
            "module_name_ar"
        ],
        "year": result["year"],
        "status": result["status"],
        "records_count": result[
            "records_count"
        ],
        "filters_applied": result[
            "filters_applied"
        ],
        "items": result["trends"],
    }


def get_facility_monthly_history(
    facility_id: str,
) -> JsonObject:
    normalized_id = facility_id.strip()

    if not normalized_id:
        raise AccommodationMonthlyServiceError(
            "معرف المنشأة مطلوب."
        )

    payload = load_accommodation_monthly()

    records = _load_normalized_records(
        payload
    )

    facility_records = _filter_records(
        records,
        facility_id=normalized_id,
    )

    if not facility_records:
        raise AccommodationMonthlyServiceError(
            f"المنشأة {normalized_id} "
            "غير موجودة في البيانات الشهرية."
        )

    facility_records.sort(
        key=lambda record: (
            record["year"],
            record["month"],
        )
    )

    return {
        "module": "accommodation_monthly",
        "facility_id": normalized_id,
        "facility_name": facility_records[
            0
        ]["facility_name"],
        "records_count": len(
            facility_records
        ),
        "items": facility_records,
    }
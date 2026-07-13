"""
Automated tests for the accommodation module.

تتحقق هذه الاختبارات من:
- تحميل بيانات الإيواء.
- سلامة المؤشرات المحسوبة.
- عدم اختلاق نسب الإشغال.
- توافق النتائج مع نماذج Pydantic.
- تشغيل مسارات API.
- ظهور المسارات والنماذج في OpenAPI.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.accommodation import (
    AccommodationResponse,
)
from app.services.accommodation_service import (
    AccommodationServiceError,
    calculate_accommodation_metrics,
    get_accommodation_indicator,
)
from app.services.data_service import (
    load_accommodation,
)


@pytest.fixture(scope="module")
def client() -> Generator[
    TestClient,
    None,
    None,
]:
    """
    إنشاء عميل اختبار واحد لمسارات الإيواء.
    """
    with TestClient(app) as test_client:
        yield test_client


# =========================================================
# Data loading tests
# =========================================================

def test_load_accommodation_data() -> None:
    """
    التحقق من تحميل ملف الإيواء.
    """
    data = load_accommodation()

    assert data["module"] == "accommodation"
    assert data["year"] == 2025

    assert (
        data["guests_reference"]["total_guests"]
        == 373843
    )

    assert (
        data["inventory"]["hotels"]
        == 384
    )


def test_accommodation_inventory() -> None:
    """
    التحقق من الطاقة الإيوائية الأساسية.
    """
    result = calculate_accommodation_metrics()

    inventory = result["inventory"]

    assert inventory["hotels"] == 384

    assert (
        inventory["hotel_apartments"]
        == 258
    )

    assert (
        inventory["hotels_and_apartments"]
        == 642
    )

    assert (
        inventory["tourist_villages"]
        == 134
    )

    assert inventory["chalets"] == 1980
    assert inventory["reported_rooms"] == 21821

    assert (
        inventory["reported_hotel_beds"]
        == 75606
    )

    assert (
        inventory["reported_chalet_beds"]
        == 15840
    )


def test_accommodation_guest_reconciliation() -> None:
    """
    التحقق من تطابق إجمالي النزلاء
    مع مجموع الجنسيات.
    """
    result = calculate_accommodation_metrics()

    guests = result["guests"]

    calculated_total = (
        guests["libyan_guests"]
        + guests["arab_guests"]
        + guests["foreign_guests"]
    )

    assert guests["total_guests"] == 373843
    assert calculated_total == 373843

    assert (
        guests["reconciliation_status"]
        == "matched"
    )


# =========================================================
# Indicator calculation tests
# =========================================================

def test_accommodation_calculated_metrics() -> None:
    """
    التحقق من المتوسطات المحسوبة.
    """
    result = calculate_accommodation_metrics()

    indicators = result["indicators"]

    assert indicators[
        "average_guests_per_facility"
    ]["value"] == pytest.approx(
        582.31,
        abs=0.01,
    )

    assert indicators[
        "average_rooms_per_facility"
    ]["value"] == pytest.approx(
        33.99,
        abs=0.01,
    )

    assert indicators[
        "average_beds_per_facility"
    ]["value"] == pytest.approx(
        117.77,
        abs=0.01,
    )

    assert indicators[
        "average_beds_per_room"
    ]["value"] == pytest.approx(
        3.46,
        abs=0.01,
    )


def test_guest_market_shares() -> None:
    """
    التحقق من حصص النزلاء حسب الجنسية.
    """
    result = calculate_accommodation_metrics()

    indicators = result["indicators"]

    libyan_share = indicators[
        "libyan_guest_share"
    ]["value"]

    arab_share = indicators[
        "arab_guest_share"
    ]["value"]

    foreign_share = indicators[
        "foreign_guest_share"
    ]["value"]

    assert libyan_share == pytest.approx(
        70.45,
        abs=0.02,
    )

    assert arab_share == pytest.approx(
        24.76,
        abs=0.02,
    )

    assert foreign_share == pytest.approx(
        4.79,
        abs=0.02,
    )

    assert (
        libyan_share
        + arab_share
        + foreign_share
    ) == pytest.approx(
        100,
        abs=0.05,
    )


def test_operational_indicators_unavailable() -> None:
    """
    يجب ألا يختلق النظام الإشغال أو الإيرادات
    عند غياب البيانات التشغيلية.
    """
    result = calculate_accommodation_metrics()

    indicators = result["indicators"]

    unavailable_codes = {
        "average_length_of_stay",
        "room_occupancy_rate",
        "bed_occupancy_rate",
        "average_daily_rate",
        "revenue_per_available_room",
    }

    for code in unavailable_codes:
        indicator = indicators[code]

        assert indicator["value"] is None
        assert indicator["status"] == "unavailable"

        assert indicator[
            "quality_status"
        ] == "missing_operational_inputs"

        assert indicator["missing_inputs"]


def test_accommodation_readiness() -> None:
    """
    التحقق من حالة جاهزية المؤشرات.
    """
    result = calculate_accommodation_metrics()

    readiness = result["readiness"]

    assert result[
        "status"
    ] == "available_with_operational_gaps"

    assert readiness["total_indicators"] == 12
    assert readiness["available_indicators"] == 7
    assert readiness["unavailable_indicators"] == 5

    assert readiness[
        "readiness_percent"
    ] == pytest.approx(
        58.33,
        abs=0.01,
    )

    assert (
        readiness["operational_data_complete"]
        is False
    )


def test_single_accommodation_indicator() -> None:
    """
    التحقق من إرجاع مؤشر واحد.
    """
    indicator = get_accommodation_indicator(
        "average_guests_per_facility"
    )

    assert (
        indicator["code"]
        == "average_guests_per_facility"
    )

    assert indicator["value"] == pytest.approx(
        582.31,
        abs=0.01,
    )

    assert indicator["status"] == "available"


def test_unknown_accommodation_indicator() -> None:
    """
    التحقق من رفض رمز مؤشر غير موجود.
    """
    with pytest.raises(
        AccommodationServiceError
    ):
        get_accommodation_indicator(
            "unknown_accommodation_indicator"
        )


# =========================================================
# Schema validation
# =========================================================

def test_accommodation_response_schema() -> None:
    """
    التحقق من توافق الحزمة مع Pydantic.
    """
    result = calculate_accommodation_metrics()

    validated = (
        AccommodationResponse.model_validate(
            result
        )
    )

    assert validated.module == "accommodation"
    assert validated.year == 2025

    assert (
        validated.readiness.total_indicators
        == 12
    )

    assert (
        validated.readiness.available_indicators
        == 7
    )


# =========================================================
# API tests
# =========================================================

def test_accommodation_endpoint(
    client: TestClient,
) -> None:
    """
    التحقق من الحزمة الكاملة عبر API.
    """
    response = client.get(
        "/api/accommodation"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["module"] == "accommodation"
    assert payload["year"] == 2025

    assert (
        payload["inventory"]["hotels"]
        == 384
    )

    assert (
        payload["guests"]["total_guests"]
        == 373843
    )

    assert (
        payload["readiness"]["total_indicators"]
        == 12
    )


def test_accommodation_indicators_endpoint(
    client: TestClient,
) -> None:
    """
    التحقق من قائمة مؤشرات الإيواء.
    """
    response = client.get(
        "/api/accommodation/indicators"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["module"] == "accommodation"
    assert len(payload["items"]) == 12

    codes = {
        item["code"]
        for item in payload["items"]
    }

    assert (
        "average_guests_per_facility"
        in codes
    )

    assert "room_occupancy_rate" in codes


def test_single_accommodation_indicator_endpoint(
    client: TestClient,
) -> None:
    """
    التحقق من مسار مؤشر واحد.
    """
    response = client.get(
        (
            "/api/accommodation/indicators/"
            "average_guests_per_facility"
        )
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["code"]
        == "average_guests_per_facility"
    )

    assert payload["value"] == pytest.approx(
        582.31,
        abs=0.01,
    )


def test_unavailable_occupancy_endpoint(
    client: TestClient,
) -> None:
    """
    التحقق من إرجاع الإشغال كغير متاح.
    """
    response = client.get(
        (
            "/api/accommodation/indicators/"
            "room_occupancy_rate"
        )
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["value"] is None
    assert payload["status"] == "unavailable"

    assert {
        "occupied_room_nights",
        "available_room_nights",
    }.issubset(
        set(payload["missing_inputs"])
    )


def test_unknown_indicator_endpoint(
    client: TestClient,
) -> None:
    """
    التحقق من إرجاع 404 لمؤشر غير موجود.
    """
    response = client.get(
        (
            "/api/accommodation/indicators/"
            "unknown_indicator"
        )
    )

    assert response.status_code == 404

    payload = response.json()

    assert (
        payload["detail"]["status"]
        == "accommodation_service_error"
    )


def test_openapi_contains_accommodation(
    client: TestClient,
) -> None:
    """
    التحقق من ظهور مسارات ونماذج الإيواء
    في توثيق OpenAPI.
    """
    response = client.get(
        "/openapi.json"
    )

    assert response.status_code == 200

    payload = response.json()

    paths = payload["paths"]

    assert (
        "/api/accommodation"
        in paths
    )

    assert (
        "/api/accommodation/indicators"
        in paths
    )

    assert (
        "/api/accommodation/indicators/{code}"
        in paths
    )

    schemas = payload[
        "components"
    ]["schemas"]

    expected_models = {
        "AccommodationResponse",
        "AccommodationIndicator",
        "AccommodationIndicatorsResponse",
        "AccommodationInventory",
        "AccommodationGuests",
        "AccommodationReadiness",
    }

    assert expected_models.issubset(
        schemas.keys()
    )
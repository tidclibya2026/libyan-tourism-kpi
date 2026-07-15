"""
Automated tests for monthly accommodation operations.

تتحقق الاختبارات من:
- تحميل ملف البيانات الشهرية.
- عدم تحويل غياب البيانات إلى قيم صفرية.
- صحة حساب الإشغال وADR وRevPAR.
- التصفية حسب الشهر.
- رفض السجلات المكررة.
- سلامة مسارات API وتوثيق OpenAPI.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.accommodation_monthly import (
    AccommodationMonthlyResponse,
)
from app.services import (
    accommodation_monthly_service,
)
from app.services.accommodation_monthly_service import (
    AccommodationMonthlyServiceError,
    calculate_monthly_accommodation_metrics,
)
from app.services.data_service import (
    load_accommodation_monthly,
)


@pytest.fixture(scope="module")
def client() -> Generator[
    TestClient,
    None,
    None,
]:
    """
    إنشاء عميل اختبار لمسارات API.
    """
    with TestClient(app) as test_client:
        yield test_client


def _sample_payload() -> dict:
    """
    بيانات اختبار تشغيلية لا تمثل بيانات رسمية.
    """
    return {
        "schema_version": "1.0",
        "module": "accommodation_monthly",
        "year": 2025,
        "status": "working_dataset",
        "records": [
            {
                "facility_id": "FAC-001",
                "facility_name": "مرفق اختباري",
                "branch": "طرابلس",
                "municipality": "طرابلس المركز",
                "year": 2025,
                "month": 1,
                "available_rooms": 10,
                "sold_room_nights": 155,
                "available_beds": 20,
                "occupied_bed_nights": 310,
                "libyan_guests": 80,
                "arab_guests": 15,
                "foreign_guests": 5,
                "tourist_nights": 200,
                "room_revenue_lyd": 31000,
                "source_reference": "TEST-001",
                "verification_status": "verified",
            }
        ],
    }


def test_load_monthly_accommodation_data() -> None:
    """
    التحقق من تحميل ملف البيانات الرسمي.
    """
    payload = load_accommodation_monthly()

    assert payload["module"] == (
        "accommodation_monthly"
    )

    assert payload["year"] == 2025
    assert payload["records"] == []


def test_empty_dataset_status_is_no_data() -> None:
    """
    الملف الفارغ يجب أن يعيد no_data.
    """
    result = (
        calculate_monthly_accommodation_metrics()
    )

    assert result["status"] == "no_data"
    assert result["records_count"] == 0
    assert result["source_records_count"] == 0


def test_empty_dataset_does_not_report_zero_metrics() -> None:
    """
    غياب البيانات لا يجوز تمثيله بصفر تشغيلي.
    """
    result = (
        calculate_monthly_accommodation_metrics()
    )

    totals = result["totals"]

    assert totals["available_room_nights"] is None
    assert totals["sold_room_nights"] is None

    assert totals["available_bed_nights"] is None
    assert totals["occupied_bed_nights"] is None

    assert totals["total_guests"] is None
    assert totals["tourist_nights"] is None
    assert totals["room_revenue_lyd"] is None


def test_empty_dataset_indicators_are_unavailable() -> None:
    """
    جميع المؤشرات التشغيلية غير متاحة عند غياب السجلات.
    """
    result = (
        calculate_monthly_accommodation_metrics()
    )

    readiness = result["readiness"]

    assert readiness["total_indicators"] == 5
    assert readiness["available_indicators"] == 0
    assert readiness["unavailable_indicators"] == 5

    assert (
        readiness["operational_data_complete"]
        is False
    )

    for indicator in result[
        "indicators"
    ].values():
        assert indicator["value"] is None
        assert indicator["status"] == "unavailable"


def test_monthly_response_schema() -> None:
    """
    التحقق من توافق الخدمة مع نموذج Pydantic.
    """
    result = (
        calculate_monthly_accommodation_metrics()
    )

    model = AccommodationMonthlyResponse(
        **result
    )

    assert model.status == "no_data"
    assert model.records_count == 0

    assert (
        model.indicators[
            "room_occupancy_rate"
        ].value
        is None
    )


def test_monthly_calculations_with_reported_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    التحقق من المعادلات باستخدام سجل اختباري.
    """
    monkeypatch.setattr(
        accommodation_monthly_service,
        "load_accommodation_monthly",
        _sample_payload,
    )

    result = (
        calculate_monthly_accommodation_metrics()
    )

    totals = result["totals"]
    indicators = result["indicators"]

    assert result["status"] == "available"
    assert result["records_count"] == 1

    assert totals["available_room_nights"] == 310
    assert totals["sold_room_nights"] == 155

    assert totals["available_bed_nights"] == 620
    assert totals["occupied_bed_nights"] == 310

    assert totals["total_guests"] == 100
    assert totals["tourist_nights"] == 200
    assert totals["room_revenue_lyd"] == 31000

    assert indicators[
        "room_occupancy_rate"
    ]["value"] == pytest.approx(
        50,
        abs=0.01,
    )

    assert indicators[
        "bed_occupancy_rate"
    ]["value"] == pytest.approx(
        50,
        abs=0.01,
    )

    assert indicators[
        "average_length_of_stay"
    ]["value"] == pytest.approx(
        2,
        abs=0.01,
    )

    assert indicators[
        "average_daily_rate"
    ]["value"] == pytest.approx(
        200,
        abs=0.01,
    )

    assert indicators[
        "revenue_per_available_room"
    ]["value"] == pytest.approx(
        100,
        abs=0.01,
    )


def test_month_filter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    التحقق من تطبيق مرشح الشهر.
    """
    payload = _sample_payload()

    second_record = dict(
        payload["records"][0]
    )

    second_record.update(
        {
            "month": 2,
            "sold_room_nights": 140,
            "occupied_bed_nights": 280,
            "libyan_guests": 40,
            "arab_guests": 8,
            "foreign_guests": 2,
            "tourist_nights": 100,
            "room_revenue_lyd": 28000,
            "source_reference": "TEST-002",
        }
    )

    payload["records"].append(
        second_record
    )

    monkeypatch.setattr(
        accommodation_monthly_service,
        "load_accommodation_monthly",
        lambda: payload,
    )

    result = (
        calculate_monthly_accommodation_metrics(
            month=2
        )
    )

    assert result["status"] == "available"
    assert result["records_count"] == 1
    assert result["source_records_count"] == 2

    assert result["totals"]["total_guests"] == 50
    assert result["totals"]["tourist_nights"] == 100

    assert result["filters_applied"]["month"] == 2


def test_duplicate_record_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    منع تكرار المنشأة في السنة والشهر نفسيهما.
    """
    payload = _sample_payload()

    payload["records"].append(
        dict(
            payload["records"][0]
        )
    )

    monkeypatch.setattr(
        accommodation_monthly_service,
        "load_accommodation_monthly",
        lambda: payload,
    )

    with pytest.raises(
        AccommodationMonthlyServiceError,
        match="مكرر",
    ):
        calculate_monthly_accommodation_metrics()


def test_monthly_root_endpoint(
    client: TestClient,
) -> None:
    """
    اختبار المسار الرئيسي للوحدة.
    """
    response = client.get(
        "/api/accommodation/monthly"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "no_data"
    assert payload["records_count"] == 0

    assert (
        payload["indicators"][
            "room_occupancy_rate"
        ]["value"]
        is None
    )


def test_monthly_summary_endpoint(
    client: TestClient,
) -> None:
    """
    اختبار مسار الملخص.
    """
    response = client.get(
        "/api/accommodation/monthly/summary"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "no_data"
    assert "trends" not in payload
    assert "records" not in payload


def test_monthly_records_and_trends_endpoints(
    client: TestClient,
) -> None:
    """
    اختبار مساري السجلات والاتجاهات.
    """
    records_response = client.get(
        "/api/accommodation/monthly/records"
    )

    assert records_response.status_code == 200
    assert records_response.json()["items"] == []

    trends_response = client.get(
        "/api/accommodation/monthly/trends"
    )

    assert trends_response.status_code == 200
    assert trends_response.json()["items"] == []


def test_monthly_invalid_month_rejected(
    client: TestClient,
) -> None:
    """
    رفض أرقام الأشهر خارج النطاق.
    """
    response = client.get(
        "/api/accommodation/monthly?month=13"
    )

    assert response.status_code == 422


def test_unknown_facility_returns_404(
    client: TestClient,
) -> None:
    """
    المنشأة غير الموجودة يجب أن تعيد 404.
    """
    response = client.get(
        "/api/accommodation/monthly/"
        "facilities/FAC-404/history"
    )

    assert response.status_code == 404

    detail = response.json()["detail"]

    assert detail["status"] == (
        "accommodation_monthly_service_error"
    )


def test_monthly_routes_in_openapi(
    client: TestClient,
) -> None:
    """
    التحقق من ظهور المسارات في وثيقة OpenAPI.
    """
    response = client.get(
        "/openapi.json"
    )

    assert response.status_code == 200

    paths = response.json()["paths"]

    expected_paths = {
        "/api/accommodation/monthly",
        "/api/accommodation/monthly/summary",
        "/api/accommodation/monthly/records",
        "/api/accommodation/monthly/trends",
        (
            "/api/accommodation/monthly/"
            "facilities/{facility_id}/history"
        ),
    }

    assert expected_paths.issubset(
        set(paths)
    )

def _mixed_verification_payload() -> dict:
    """
    بيانات مختلطة لاختبار سياسة التحقق الافتراضية.
    """
    payload = _sample_payload()

    pending_record = dict(
        payload["records"][0]
    )

    pending_record.update(
        {
            "month": 2,
            "sold_room_nights": 140,
            "occupied_bed_nights": 280,
            "libyan_guests": 40,
            "arab_guests": 8,
            "foreign_guests": 2,
            "tourist_nights": 100,
            "room_revenue_lyd": 28000,
            "source_reference": "PENDING-REVIEW-002",
            "verification_status": "pending_review",
        }
    )

    payload["records"].append(
        pending_record
    )

    return payload


def test_default_policy_uses_verified_records_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    الحساب الافتراضي يجب أن يعتمد السجلات المتحققة فقط.
    """
    payload = _mixed_verification_payload()

    monkeypatch.setattr(
        accommodation_monthly_service,
        "load_accommodation_monthly",
        lambda: payload,
    )

    result = (
        calculate_monthly_accommodation_metrics()
    )

    assert result["status"] == "available"

    assert result["source_records_count"] == 2
    assert result["records_count"] == 1

    assert (
        result["filters_applied"][
            "verification_status"
        ]
        == "verified"
    )

    assert (
        result["totals"][
            "reporting_facilities"
        ]
        == 1
    )

    assert (
        result["totals"][
            "months_covered"
        ]
        == 1
    )

    assert (
        result["totals"][
            "total_guests"
        ]
        == 100
    )

    assert (
        result["totals"][
            "tourist_nights"
        ]
        == 200
    )


def test_explicit_status_filter_and_history_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    يمكن فحص الحالات الأخرى صراحة،
    بينما سجل المنشأة العام يعرض verified فقط.
    """
    payload = _mixed_verification_payload()

    monkeypatch.setattr(
        accommodation_monthly_service,
        "load_accommodation_monthly",
        lambda: payload,
    )

    pending_result = (
        calculate_monthly_accommodation_metrics(
            verification_status="pending_review"
        )
    )

    assert pending_result["status"] == "available"
    assert pending_result["records_count"] == 1

    assert (
        pending_result["totals"][
            "total_guests"
        ]
        == 50
    )

    assert (
        pending_result["filters_applied"][
            "verification_status"
        ]
        == "pending_review"
    )

    history = (
        accommodation_monthly_service
        .get_facility_monthly_history(
            "FAC-001"
        )
    )

    assert history["records_count"] == 1

    assert all(
        item["verification_status"]
        == "verified"
        for item in history["items"]
    )

def test_api_defaults_to_verified_records(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    مسار API الافتراضي لا يعرض pending_review.
    """
    payload = _mixed_verification_payload()

    monkeypatch.setattr(
        accommodation_monthly_service,
        "load_accommodation_monthly",
        lambda: payload,
    )

    response = client.get(
        "/api/accommodation/monthly"
    )

    assert response.status_code == 200

    result = response.json()

    assert result["source_records_count"] == 2
    assert result["records_count"] == 1

    assert (
        result["filters_applied"][
            "verification_status"
        ]
        == "verified"
    )

    assert (
        result["totals"]["total_guests"]
        == 100
    )

    pending_response = client.get(
        "/api/accommodation/monthly",
        params={
            "verification_status": (
                "pending_review"
            )
        },
    )

    assert pending_response.status_code == 200

    pending_result = pending_response.json()

    assert pending_result["records_count"] == 1

    assert (
        pending_result["filters_applied"][
            "verification_status"
        ]
        == "pending_review"
    )

    assert (
        pending_result["totals"][
            "total_guests"
        ]
        == 50
    )

def test_facility_history_uses_verified_records_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    سجل المنشأة العام يعرض verified فقط.
    """
    payload = _mixed_verification_payload()

    monkeypatch.setattr(
        accommodation_monthly_service,
        "load_accommodation_monthly",
        lambda: payload,
    )

    history = (
        accommodation_monthly_service
        .get_facility_monthly_history(
            "FAC-001"
        )
    )

    assert history["records_count"] == 1

    assert all(
        item["verification_status"]
        == "verified"
        for item in history["items"]
    )

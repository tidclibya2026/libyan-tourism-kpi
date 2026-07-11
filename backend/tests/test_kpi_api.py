"""
Automated API tests for the Libyan National Tourism Intelligence Platform.

تتحقق الاختبارات من:
- صحة تشغيل التطبيق.
- جاهزية ملفات البيانات.
- استمرار المسارات القديمة.
- مؤشرات السياحة الوطنية.
- مؤشرات المدن والقارات.
- المؤشرات غير المتاحة.
- حزمة Dashboard.
- عقود Pydantic وتوثيق OpenAPI.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """
    إنشاء عميل اختبار واحد لجميع اختبارات الملف.
    """

    with TestClient(app) as test_client:
        yield test_client


# =========================================================
# System endpoints
# =========================================================

def test_home_endpoint(
    client: TestClient,
) -> None:
    """
    التحقق من بطاقة تعريف المنصة.
    """

    response = client.get("/")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "running"
    assert payload["short_name"] == "LNTIP"
    assert payload["version"]

    assert (
        payload["documentation"]["swagger"]
        == "/docs"
    )


def test_health_endpoint(
    client: TestClient,
) -> None:
    """
    التحقق من فحص الصحة.
    """

    response = client.get("/api/health")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] in {
        "healthy",
        "healthy_with_warnings",
    }

    assert "application" in payload
    assert "data" in payload


def test_readiness_endpoint(
    client: TestClient,
) -> None:
    """
    التحقق من جاهزية ملفات البيانات.
    """

    response = client.get("/api/ready")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ready"

    assert payload.get(
        "missing_required_files",
        [],
    ) == []

    validation = payload.get(
        "validation",
        {},
    )

    assert int(
        validation.get(
            "errors_count",
            0,
        ) or 0
    ) == 0


# =========================================================
# Legacy-compatible endpoints
# =========================================================

def test_legacy_kpis_endpoint(
    client: TestClient,
) -> None:
    """
    ضمان استمرار المسار القديم.
    """

    response = client.get("/api/kpis")

    assert response.status_code == 200

    payload = response.json()

    assert payload["year"] == 2025

    assert (
        payload["international_tourists"]
        == 2752
    )

    assert payload["hotel_guests"] == 373843


def test_summary_endpoint(
    client: TestClient,
) -> None:
    """
    التحقق من الملخص الوطني.
    """

    response = client.get("/api/summary")

    assert response.status_code == 200

    payload = response.json()

    assert payload["year"] == 2025
    assert payload["international_tourists"] == 2752
    assert payload["tourism_trips"] == 489
    assert payload["hotel_guests"] == 373843
    assert payload["flights"] == 30736
    assert payload["air_passengers"] == 3089211


# =========================================================
# National KPI endpoints
# =========================================================

def test_national_kpis_endpoint(
    client: TestClient,
) -> None:
    """
    التحقق من الحزمة الوطنية.
    """

    response = client.get(
        "/api/kpis/national"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["reference_year"] == 2025
    assert payload["status"] == "calculated"

    assert (
        payload["calculated_indicators_count"]
        > 0
    )

    assert isinstance(
        payload["indicators"],
        list,
    )

    assert isinstance(
        payload["unavailable_indicators"],
        list,
    )

    assert payload["engine"]["name"]
    assert payload["engine"]["version"]


def test_passengers_per_flight_endpoint(
    client: TestClient,
) -> None:
    """
    اختبار متوسط المسافرين لكل رحلة.
    """

    response = client.get(
        "/api/kpis/indicator/"
        "passengers_per_flight"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["code"]
        == "passengers_per_flight"
    )

    assert payload["value"] == pytest.approx(
        100.51,
        abs=0.02,
    )

    assert payload["calculation_status"] in {
        "calculated",
        "available",
        "source_value",
    }

    assert isinstance(
        payload.get("notes", []),
        list,
    )


def test_unavailable_occupancy_endpoint(
    client: TestClient,
) -> None:
    """
    يجب ألا يختلق النظام نسبة إشغال.
    """

    response = client.get(
        "/api/kpis/indicator/"
        "room_occupancy_rate"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["code"]
        == "room_occupancy_rate"
    )

    assert payload.get("value") is None

    assert (
        payload["calculation_status"]
        == "unavailable"
    )

    assert isinstance(
        payload.get("notes", []),
        list,
    )


# =========================================================
# City endpoints
# =========================================================

def test_cities_endpoint(
    client: TestClient,
) -> None:
    """
    التحقق من إجمالي وترتيب المدن.
    """

    response = client.get(
        "/api/kpis/cities"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["year"] == 2025

    assert (
        payload["national_total_guests"]
        == 373843
    )

    assert payload["cities_count"] == 10
    assert len(payload["items"]) == 10

    assert (
        payload["items"][0]["id"]
        == "tripoli"
    )

    assert (
        payload["items"][0]["national_rank"]
        == 1
    )


def test_tripoli_endpoint(
    client: TestClient,
) -> None:
    """
    التحقق من بيانات طرابلس.
    """

    response = client.get(
        "/api/kpis/cities/tripoli"
    )

    assert response.status_code == 200

    payload = response.json()
    city = payload["city"]

    assert city["id"] == "tripoli"
    assert city["name_ar"] == "طرابلس"
    assert city["total_guests"] == 208758
    assert city["national_rank"] == 1

    assert city[
        "share_percent"
    ] == pytest.approx(
        55.84,
        abs=0.05,
    )


# =========================================================
# Continent endpoints
# =========================================================

def test_continents_endpoint(
    client: TestClient,
) -> None:
    """
    التحقق من توزيع القارات.
    """

    response = client.get(
        "/api/kpis/continents"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["year"] == 2025

    assert (
        payload["international_tourists_total"]
        == 2752
    )

    assert payload["continents_count"] == 5
    assert len(payload["items"]) == 5

    europe = payload["items"][0]

    assert europe["id"] == "europe"
    assert europe["tourists"] == 1243
    assert europe["market_rank"] == 1

    assert europe[
        "market_share_percent"
    ] == pytest.approx(
        45.17,
        abs=0.05,
    )


# =========================================================
# Dashboard endpoint
# =========================================================

def test_dashboard_endpoint(
    client: TestClient,
) -> None:
    """
    التحقق من حزمة Dashboard الموحدة.
    """

    response = client.get(
        "/api/kpis/dashboard",
        params={
            "top_cities": 5,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["reference_year"] == 2025

    assert "engine" in payload
    assert "national" in payload
    assert "cities" in payload
    assert "continents" in payload

    top_items = payload[
        "cities"
    ]["top_items"]

    assert len(top_items) == 5

    assert top_items[0]["id"] == "tripoli"

    assert (
        top_items[0]["national_rank"]
        == 1
    )


def test_dashboard_top_cities_validation(
    client: TestClient,
) -> None:
    """
    التحقق من رفض قيمة غير صالحة.
    """

    response = client.get(
        "/api/kpis/dashboard",
        params={
            "top_cities": 0,
        },
    )

    assert response.status_code == 422


# =========================================================
# Metadata and OpenAPI
# =========================================================

def test_metadata_endpoint(
    client: TestClient,
) -> None:
    """
    التحقق من سجل المؤشرات والمصادر.
    """

    response = client.get(
        "/api/metadata"
    )

    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_openapi_contains_kpi_models(
    client: TestClient,
) -> None:
    """
    التحقق من ربط response_model داخل OpenAPI.
    """

    response = client.get(
        "/openapi.json"
    )

    assert response.status_code == 200

    payload = response.json()

    schemas = payload[
        "components"
    ]["schemas"]

    expected_models = {
        "KPIValue",
        "NationalKPIResponse",
        "CitiesKPIResponse",
        "SingleCityKPIResponse",
        "ContinentsKPIResponse",
        "DashboardKPIResponse",
    }

    assert expected_models.issubset(
        schemas.keys()
    )

    national_schema = (
        payload["paths"]
        ["/api/kpis/national"]
        ["get"]
        ["responses"]
        ["200"]
        ["content"]
        ["application/json"]
        ["schema"]
    )

    assert national_schema.get("$ref") == (
        "#/components/schemas/"
        "NationalKPIResponse"
    )
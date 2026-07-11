"""
Automated tests for the National Tourism KPI Engine.

تتحقق هذه الاختبارات من:
- سلامة الدوال الحسابية الأساسية.
- صحة مؤشر المسافرين لكل رحلة.
- التعامل الإحصائي الصحيح مع المؤشرات غير المتاحة.
- مطابقة مجاميع المدن والقارات.
- ترتيب المدن والقارات.
- سلامة حزمة Dashboard.
- توافق نتائج المحرك مع Pydantic schemas.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.schemas.kpi import KPIValue
from app.services.kpi_engine import (
    calculate_city_kpis,
    calculate_continent_kpis,
    calculate_dashboard_snapshot,
    calculate_indicator,
    calculate_national_kpis,
    growth_forecast,
    growth_rate,
    percent,
)


# =========================================================
# Helper functions
# =========================================================

def collect_numeric_differences(
    value: Any,
) -> list[float]:
    """
    البحث التكراري عن جميع الحقول المسماة difference.

    تستخدم للتأكد من أن مطابقة المجاميع التفصيلية
    مع المجاميع الوطنية لا تحتوي فروقات.
    """

    differences: list[float] = []

    if isinstance(value, dict):
        for key, item in value.items():
            if (
                key == "difference"
                and isinstance(item, (int, float))
            ):
                differences.append(float(item))
            else:
                differences.extend(
                    collect_numeric_differences(item)
                )

    elif isinstance(value, list):
        for item in value:
            differences.extend(
                collect_numeric_differences(item)
            )

    return differences


def get_city_items(
    result: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    قراءة قائمة المدن مع دعم اسم الحقل الحالي
    وأي شكل متوافق مستخدم أثناء التطوير.
    """

    items = result.get("items")

    if isinstance(items, list):
        return items

    cities = result.get("cities")

    if isinstance(cities, list):
        return cities

    return []


# =========================================================
# Basic calculation tests
# =========================================================

def test_percent_calculation() -> None:
    """
    اختبار حساب النسبة المئوية.
    """

    result = percent(25, 100)

    assert result == pytest.approx(
        25.0,
        abs=0.01,
    )


def test_growth_rate_calculation() -> None:
    """
    اختبار معدل النمو بين قيمتين.
    """

    result = growth_rate(
        current_value=120,
        previous_value=100,
    )

    assert result == pytest.approx(
        20.0,
        abs=0.01,
    )


def test_growth_forecast_calculation() -> None:
    """
    اختبار النمو المركب لسنتين بنسبة 10%.
    """

    result = growth_forecast(
        value=100,
        rate=0.10,
        years=2,
    )

    assert result == pytest.approx(
        121,
        abs=0.01,
    )


# =========================================================
# Individual indicator tests
# =========================================================

def test_passengers_per_flight_indicator() -> None:
    """
    التحقق من مؤشر متوسط المسافرين لكل رحلة.

    3,089,211 مسافر ÷ 30,736 رحلة
    يساوي تقريبًا 100.51 مسافر لكل رحلة.
    """

    result = calculate_indicator(
        "passengers_per_flight"
    )

    assert result["code"] == "passengers_per_flight"

    assert result["value"] == pytest.approx(
        100.51,
        abs=0.02,
    )

    assert result["calculation_status"] in {
        "calculated",
        "available",
        "source_value",
    }

    assert isinstance(
        result.get("notes", []),
        list,
    )


def test_passengers_per_flight_schema() -> None:
    """
    التحقق من توافق نتيجة المؤشر مع نموذج Pydantic.
    """

    result = calculate_indicator(
        "passengers_per_flight"
    )

    validated = KPIValue.model_validate(result)

    assert validated.code == "passengers_per_flight"

    assert validated.value == pytest.approx(
        100.51,
        abs=0.02,
    )

    assert isinstance(validated.notes, list)


def test_room_occupancy_rate_is_unavailable() -> None:
    """
    يجب ألا يختلق النظام نسبة إشغال دون بيانات
    ليالي الغرف المباعة والمتاحة.
    """

    result = calculate_indicator(
        "room_occupancy_rate"
    )

    assert result["code"] == "room_occupancy_rate"

    assert result.get("value") is None

    assert result["calculation_status"] == "unavailable"

    assert isinstance(
        result.get("notes", []),
        list,
    )


def test_room_occupancy_schema() -> None:
    """
    التحقق من قبول Pydantic للمؤشر غير المتاح.
    """

    result = calculate_indicator(
        "room_occupancy_rate"
    )

    validated = KPIValue.model_validate(result)

    assert validated.value is None
    assert validated.calculation_status == "unavailable"
    assert isinstance(validated.notes, list)


# =========================================================
# National indicators tests
# =========================================================

def test_national_kpi_engine_returns_results() -> None:
    """
    التحقق من وجود مؤشرات وطنية محسوبة.
    """

    result = calculate_national_kpis()

    assert result["reference_year"] == 2025

    assert (
        result["calculated_indicators_count"]
        > 0
    )

    assert isinstance(
        result["indicators"],
        list,
    )

    assert isinstance(
        result["unavailable_indicators"],
        list,
    )


def test_national_reconciliation_has_no_difference() -> None:
    """
    يجب أن تتطابق مجاميع المدن والقارات
    مع الأرقام الوطنية الحالية.
    """

    result = calculate_national_kpis()

    reconciliation = result.get(
        "reconciliation",
        {},
    )

    differences = collect_numeric_differences(
        reconciliation
    )

    assert differences, (
        "لم يعثر الاختبار على حقول difference "
        "داخل نتيجة المطابقة."
    )

    assert all(
        difference == pytest.approx(
            0.0,
            abs=0.001,
        )
        for difference in differences
    )


# =========================================================
# City tests
# =========================================================

def test_city_totals_and_count() -> None:
    """
    التحقق من إجمالي نزلاء المدن وعدد المدن.
    """

    result = calculate_city_kpis()
    items = get_city_items(result)

    assert result["national_total_guests"] == 373843
    assert result["cities_count"] == 10
    assert len(items) == 10

    calculated_total = sum(
        int(city.get("total_guests", 0) or 0)
        for city in items
    )

    assert calculated_total == 373843


def test_tripoli_is_first_city() -> None:
    """
    طرابلس هي المدينة الأولى وفق إجمالي النزلاء
    في البيانات الحالية.
    """

    result = calculate_city_kpis(
        city_id="tripoli"
    )

    city = result["city"]

    assert city["id"] == "tripoli"
    assert city["name_ar"] == "طرابلس"
    assert city["total_guests"] == 208758
    assert city["national_rank"] == 1

    assert city["share_percent"] == pytest.approx(
        55.84,
        abs=0.05,
    )


# =========================================================
# Continent tests
# =========================================================

def test_continent_distribution() -> None:
    """
    التحقق من تطابق توزيع القارات مع إجمالي
    السياح الدوليين.
    """

    result = calculate_continent_kpis()

    assert (
        result["international_tourists_total"]
        == 2752
    )

    assert result["continents_count"] == 5

    total = sum(
        int(item.get("tourists", 0) or 0)
        for item in result["items"]
    )

    assert total == 2752


def test_europe_is_first_market() -> None:
    """
    أوروبا هي السوق القاري الأول حاليًا.
    """

    result = calculate_continent_kpis()

    europe = next(
        item
        for item in result["items"]
        if item["id"] == "europe"
    )

    assert europe["tourists"] == 1243
    assert europe["market_rank"] == 1

    assert europe[
        "market_share_percent"
    ] == pytest.approx(
        45.17,
        abs=0.05,
    )


# =========================================================
# Dashboard tests
# =========================================================

def test_dashboard_snapshot() -> None:
    """
    التحقق من تجهيز حزمة Dashboard موحدة.
    """

    result = calculate_dashboard_snapshot(
        top_cities=5
    )

    assert result["reference_year"] == 2025

    assert "engine" in result
    assert "national" in result
    assert "cities" in result
    assert "continents" in result

    top_items = result["cities"]["top_items"]

    assert len(top_items) == 5

    assert top_items[0]["id"] == "tripoli"
    assert top_items[0]["national_rank"] == 1
"""
Central enumerations for the Libyan National Tourism Intelligence Platform.

يحتوي هذا الملف على القيم والتصنيفات الموحدة المستخدمة في:
- السجل الوطني للمؤشرات السياحية.
- مصادر البيانات.
- محرك المؤشرات KPI Engine.
- التنبؤ والتحليل.
- الصلاحيات والأمن.
- التقارير والتنبيهات.
"""

from __future__ import annotations

from enum import Enum
from typing import TypeVar


class TextEnum(str, Enum):
    """
    فئة أساسية لإنشاء Enums نصية قابلة للاستخدام مباشرة في JSON وFastAPI.
    """

    def __str__(self) -> str:
        return self.value


class DataStatus(TextEnum):
    """
    الحالة التشغيلية للبيانات أو المؤشر.
    """

    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    SUSPENDED = "suspended"


class ValidationStatus(TextEnum):
    """
    نتيجة التحقق الفني أو الإحصائي من البيانات.
    """

    NOT_VALIDATED = "not_validated"
    VALID = "valid"
    VALID_WITH_WARNINGS = "valid_with_warnings"
    INVALID = "invalid"
    REQUIRES_FIELD_VERIFICATION = "requires_field_verification"
    REQUIRES_RECLASSIFICATION = "requires_reclassification"
    POSSIBLE_DUPLICATE = "possible_duplicate"


class ConfidenceLevel(TextEnum):
    """
    مستوى موثوقية البيانات أو نتائج المؤشر.
    """

    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class UpdateFrequency(TextEnum):
    """
    دورية تحديث البيانات والمؤشرات.
    """

    REAL_TIME = "real_time"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMIANNUAL = "semiannual"
    ANNUAL = "annual"
    BIENNIAL = "biennial"
    AD_HOC = "ad_hoc"


class IndicatorType(TextEnum):
    """
    نوع المؤشر وفق موقعه في دورة القياس واتخاذ القرار.
    """

    INPUT = "input"
    ACTIVITY = "activity"
    OUTPUT = "output"
    OUTCOME = "outcome"
    IMPACT = "impact"
    CONTEXT = "context"
    COMPOSITE = "composite"
    FORECAST = "forecast"
    BENCHMARK = "benchmark"


class IndicatorCategory(TextEnum):
    """
    التصنيفات الوطنية الرئيسية للمؤشرات السياحية.
    """

    TOURISM_DEMAND = "tourism_demand"
    ACCOMMODATION = "accommodation"
    TRANSPORT = "transport"
    INVESTMENT = "investment"
    ECONOMIC = "economic"
    EMPLOYMENT = "employment"
    HERITAGE = "heritage"
    MUSEUMS = "museums"
    HANDICRAFTS = "handicrafts"
    COMPANIES = "companies"
    RESTAURANTS_CAFES = "restaurants_cafes"
    SUSTAINABILITY = "sustainability"
    DIGITAL_TRANSFORMATION = "digital_transformation"
    VISITOR_EXPERIENCE = "visitor_experience"
    MARKETING = "marketing"
    GOVERNANCE = "governance"
    DATA_QUALITY = "data_quality"
    FORECASTING = "forecasting"


class MeasurementUnit(TextEnum):
    """
    وحدات القياس القياسية المستخدمة في المؤشرات.
    """

    NUMBER = "number"
    PERCENT = "percent"
    RATE = "rate"
    RATIO = "ratio"
    INDEX = "index"
    SCORE = "score"
    DAYS = "days"
    NIGHTS = "nights"
    HOURS = "hours"
    PERSONS = "persons"
    VISITORS = "visitors"
    TOURISTS = "tourists"
    TRIPS = "trips"
    FLIGHTS = "flights"
    ROOMS = "rooms"
    BEDS = "beds"
    FACILITIES = "facilities"
    COMPANIES = "companies"
    JOBS = "jobs"
    SQUARE_METERS = "square_meters"
    HECTARES = "hectares"
    KILOMETERS = "kilometers"
    LYD = "LYD"
    USD = "USD"
    EUR = "EUR"


class IndicatorDirection(TextEnum):
    """
    اتجاه الأداء المرغوب للمؤشر.
    """

    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"
    TARGET_RANGE = "target_range"
    NEUTRAL = "neutral"


class AggregationMethod(TextEnum):
    """
    طريقة تجميع المؤشر عبر الزمن أو المناطق.
    """

    SUM = "sum"
    AVERAGE = "average"
    WEIGHTED_AVERAGE = "weighted_average"
    MEDIAN = "median"
    MINIMUM = "minimum"
    MAXIMUM = "maximum"
    COUNT = "count"
    DISTINCT_COUNT = "distinct_count"
    LAST_VALUE = "last_value"
    CUMULATIVE = "cumulative"
    RATIO = "ratio"
    FORMULA = "formula"


class DataSourceType(TextEnum):
    """
    نوع مصدر البيانات.
    """

    ADMINISTRATIVE_RECORD = "administrative_record"
    SURVEY = "survey"
    CENSUS = "census"
    FIELD_VISIT = "field_visit"
    INFORMATION_SYSTEM = "information_system"
    API = "api"
    GIS = "gis"
    EXTERNAL_REPORT = "external_report"
    ESTIMATE = "estimate"
    CALCULATED = "calculated"
    FORECAST_MODEL = "forecast_model"


class DataCollectionMethod(TextEnum):
    """
    طريقة جمع أو استلام البيانات.
    """

    MANUAL_ENTRY = "manual_entry"
    FILE_UPLOAD = "file_upload"
    SYSTEM_INTEGRATION = "system_integration"
    API_INTEGRATION = "api_integration"
    FIELD_FORM = "field_form"
    ONLINE_SURVEY = "online_survey"
    DATABASE_IMPORT = "database_import"
    AUTOMATED_CALCULATION = "automated_calculation"


class GeographyLevel(TextEnum):
    """
    المستوى الجغرافي المرتبط بالبيانات.
    """

    NATIONAL = "national"
    REGION = "region"
    GOVERNORATE = "governorate"
    MUNICIPALITY = "municipality"
    CITY = "city"
    DISTRICT = "district"
    SITE = "site"
    FACILITY = "facility"
    BORDER_POINT = "border_point"
    AIRPORT = "airport"
    PORT = "port"


class TimeGranularity(TextEnum):
    """
    المستوى الزمني للبيانات أو المؤشر.
    """

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMIANNUAL = "semiannual"
    ANNUAL = "annual"
    MULTI_YEAR = "multi_year"


class DataClassification(TextEnum):
    """
    تصنيف حساسية البيانات.
    """

    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    CONFIDENTIAL = "confidential"


class AccessLevel(TextEnum):
    """
    مستوى الوصول المطلوب للبيانات أو وظائف النظام.
    """

    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    OPERATIONAL = "operational"
    MANAGEMENT = "management"
    EXECUTIVE = "executive"
    ADMINISTRATIVE = "administrative"
    SYSTEM = "system"


class UserRole(TextEnum):
    """
    الأدوار الرئيسية للمستخدمين.
    """

    VIEWER = "viewer"
    DATA_ENTRY = "data_entry"
    DATA_REVIEWER = "data_reviewer"
    ANALYST = "analyst"
    GIS_SPECIALIST = "gis_specialist"
    REPORTER = "reporter"
    DEPARTMENT_MANAGER = "department_manager"
    EXECUTIVE = "executive"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    AUDITOR = "auditor"


class ForecastScenario(TextEnum):
    """
    سيناريوهات التنبؤ حتى عام 2035.
    """

    CONSERVATIVE = "conservative"
    BASELINE = "baseline"
    OPTIMISTIC = "optimistic"
    ACCELERATED = "accelerated"
    STRESS = "stress"


class ForecastMethod(TextEnum):
    """
    طرق التنبؤ المعتمدة أو المقترحة.
    """

    COMPOUND_GROWTH = "compound_growth"
    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    LINEAR_REGRESSION = "linear_regression"
    ARIMA = "arima"
    PROPHET = "prophet"
    MACHINE_LEARNING = "machine_learning"
    EXPERT_SCENARIO = "expert_scenario"


class AlertLevel(TextEnum):
    """
    مستوى التنبيه في لوحة القيادة ونظام الإنذار المبكر.
    """

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PerformanceStatus(TextEnum):
    """
    حالة أداء المؤشر مقارنة بالهدف أو الخط الأساسي.
    """

    NOT_AVAILABLE = "not_available"
    ON_TRACK = "on_track"
    WATCH = "watch"
    OFF_TRACK = "off_track"
    CRITICAL = "critical"
    EXCEEDED_TARGET = "exceeded_target"


class TrendDirection(TextEnum):
    """
    اتجاه حركة المؤشر.
    """

    STRONGLY_DECREASING = "strongly_decreasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    INCREASING = "increasing"
    STRONGLY_INCREASING = "strongly_increasing"


class ExportFormat(TextEnum):
    """
    صيغ التقارير والتصدير.
    """

    JSON = "json"
    CSV = "csv"
    XLSX = "xlsx"
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    GEOJSON = "geojson"


class AuditAction(TextEnum):
    """
    العمليات التي يجب تسجيلها في سجل التدقيق.
    """

    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    REJECT = "reject"
    PUBLISH = "publish"
    ARCHIVE = "archive"
    IMPORT = "import"
    EXPORT = "export"
    CALCULATE = "calculate"
    FORECAST = "forecast"


EnumType = TypeVar("EnumType", bound=TextEnum)


def enum_values(enum_class: type[EnumType]) -> list[str]:
    """
    إرجاع قيم Enum في صورة قائمة نصية.

    Example:
        enum_values(DataStatus)
    """

    return [item.value for item in enum_class]


def enum_choices(enum_class: type[EnumType]) -> list[dict[str, str]]:
    """
    إرجاع قيم Enum بالشكل المناسب لواجهات API والقوائم المنسدلة.
    """

    return [
        {
            "key": item.name,
            "value": item.value,
        }
        for item in enum_class
    ]


def get_enum_catalog() -> dict[str, list[str]]:
    """
    إرجاع كتالوج مختصر للتصنيفات الأساسية المستخدمة في المنصة.
    """

    return {
        "data_status": enum_values(DataStatus),
        "validation_status": enum_values(ValidationStatus),
        "confidence_levels": enum_values(ConfidenceLevel),
        "update_frequencies": enum_values(UpdateFrequency),
        "indicator_types": enum_values(IndicatorType),
        "indicator_categories": enum_values(IndicatorCategory),
        "measurement_units": enum_values(MeasurementUnit),
        "indicator_directions": enum_values(IndicatorDirection),
        "aggregation_methods": enum_values(AggregationMethod),
        "data_source_types": enum_values(DataSourceType),
        "geography_levels": enum_values(GeographyLevel),
        "time_granularities": enum_values(TimeGranularity),
        "data_classifications": enum_values(DataClassification),
        "access_levels": enum_values(AccessLevel),
        "user_roles": enum_values(UserRole),
        "forecast_scenarios": enum_values(ForecastScenario),
        "forecast_methods": enum_values(ForecastMethod),
        "alert_levels": enum_values(AlertLevel),
        "performance_statuses": enum_values(PerformanceStatus),
        "trend_directions": enum_values(TrendDirection),
        "export_formats": enum_values(ExportFormat),
    }
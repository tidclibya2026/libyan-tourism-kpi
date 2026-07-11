from fastapi import APIRouter
from app.services.data_service import load_tourism_data
from app.services.kpi_engine import growth_forecast

router = APIRouter(prefix="/api/forecast", tags=["Forecast"])

@router.get("/2035")
def forecast_2035():
    data = load_tourism_data()
    years = 10

    return {
        "base_year": 2025,
        "target_year": 2035,
        "international_tourists_2035": growth_forecast(data["international_tourists"], 0.08, years),
        "hotel_guests_2035": growth_forecast(data["hotel_guests"], 0.08, years),
        "hotels_2035": growth_forecast(data["hotels"], 0.04, years),
        "companies_2035": growth_forecast(data["tourism_companies"], 0.07, years),
        "heritage_visitors_2035": growth_forecast(data["heritage_visitors"], 0.06, years),
        "summer_revenue_lyd_2035": growth_forecast(data["summer_revenue_lyd"], 0.10, years)
    }
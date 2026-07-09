from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path


app = FastAPI(
    title="Libya Tourism KPI Platform",
    description="National Tourism Indicators Platform - Libya",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "tourism_2025.json"


def load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def calculate_city_metrics(city, national_total_guests):
    total = city.get("total_guests", 0)
    accommodation_total = city.get("accommodation_total", 0)

    return {
        **city,
        "share_percent": round(total / national_total_guests * 100, 2) if national_total_guests else 0,
        "domestic_share_percent": round(city.get("libyans", 0) / total * 100, 2) if total else 0,
        "arab_share_percent": round(city.get("arabs", 0) / total * 100, 2) if total else 0,
        "foreign_share_percent": round(city.get("foreigners", 0) / total * 100, 2) if total else 0,
        "accommodation_structure": {
            "hotels_percent": round(city.get("hotels", 0) / accommodation_total * 100, 2) if accommodation_total else 0,
            "hotel_apartments_percent": round(city.get("hotel_apartments", 0) / accommodation_total * 100, 2) if accommodation_total else 0,
            "tourist_villages_percent": round(city.get("tourist_villages", 0) / accommodation_total * 100, 2) if accommodation_total else 0
        }
    }


@app.get("/")
def home():
    return {
        "system": "Libya Tourism KPI Platform",
        "status": "running",
        "version": "1.0.0",
        "documentation": "/docs"
    }


@app.get("/api/kpis")
def get_kpis():
    return load_data()


@app.get("/api/summary")
def get_summary():
    data = load_data()

    cities = data.get("cities", [])
    total_city_guests = sum(city.get("total_guests", 0) for city in cities)

    return {
        "year": data["year"],
        "international_tourists": data["international_tourists"],
        "tourism_trips": data["tourism_trips"],
        "hotel_guests": data["hotel_guests"],
        "total_city_guests": total_city_guests,
        "hotels": data["hotels"],
        "hotel_apartments": data["hotel_apartments"],
        "hotels_and_apartments": data["hotels_and_apartments"],
        "tourist_villages": data["tourist_villages"],
        "tourism_companies": data["tourism_companies"],
        "heritage_visitors": data["heritage_visitors"],
        "summer_revenue_lyd": data["summer_revenue_lyd"]
    }


@app.get("/api/continents")
def get_continents():
    data = load_data()
    continents = data.get("continents", {})
    total = sum(continents.values())

    return {
        "total": total,
        "continents": [
            {
                "name_en": "Europe",
                "name_ar": "أوروبا",
                "value": continents.get("Europe", 0),
                "share_percent": round(continents.get("Europe", 0) / total * 100, 2) if total else 0
            },
            {
                "name_en": "Asia",
                "name_ar": "آسيا",
                "value": continents.get("Asia", 0),
                "share_percent": round(continents.get("Asia", 0) / total * 100, 2) if total else 0
            },
            {
                "name_en": "Africa",
                "name_ar": "أفريقيا",
                "value": continents.get("Africa", 0),
                "share_percent": round(continents.get("Africa", 0) / total * 100, 2) if total else 0
            },
            {
                "name_en": "Americas",
                "name_ar": "الأمريكيتين",
                "value": continents.get("Americas", 0),
                "share_percent": round(continents.get("Americas", 0) / total * 100, 2) if total else 0
            },
            {
                "name_en": "Australia",
                "name_ar": "أستراليا",
                "value": continents.get("Australia", 0),
                "share_percent": round(continents.get("Australia", 0) / total * 100, 2) if total else 0
            }
        ]
    }


@app.get("/api/cities")
def get_all_cities():
    data = load_data()

    cities = data.get("cities", [])
    total_guests = sum(city.get("total_guests", 0) for city in cities)

    result = [
        calculate_city_metrics(city, total_guests)
        for city in cities
    ]

    result = sorted(result, key=lambda item: item["total_guests"], reverse=True)

    return {
        "year": data["year"],
        "total_guests": total_guests,
        "cities_count": len(result),
        "cities": result
    }


@app.get("/api/cities/{city_id}")
def get_city_by_id(city_id: str):
    data = load_data()

    cities = data.get("cities", [])
    total_guests = sum(city.get("total_guests", 0) for city in cities)

    for city in cities:
        if city["id"] == city_id:
            return calculate_city_metrics(city, total_guests)

    raise HTTPException(
        status_code=404,
        detail={
            "error": "City not found",
            "city_id": city_id
        }
    )


@app.get("/api/cities/tripoli/legacy")
def tripoli_dashboard_legacy():
    data = load_data()

    tripoli = data["tripoli"]
    total = tripoli["accommodation_total"]

    return {
        "city": "Tripoli",
        "city_ar": "طرابلس",
        "companies": tripoli["companies"],
        "offices": tripoli["offices"],
        "accommodation_total": total,
        "hotels": tripoli["hotels"],
        "hotel_apartments": tripoli["hotel_apartments"],
        "tourist_villages": tripoli["tourist_villages"],
        "hotel_guests": tripoli["hotel_guests"],
        "shares": {
            "hotels_percent": round(tripoli["hotels"] / total * 100, 1) if total else 0,
            "hotel_apartments_percent": round(tripoli["hotel_apartments"] / total * 100, 1) if total else 0,
            "tourist_villages_percent": round(tripoli["tourist_villages"] / total * 100, 1) if total else 0
        }
    }


@app.get("/api/forecast/2035")
def forecast_2035():
    data = load_data()

    base_year = 2025
    target_year = 2035
    years = target_year - base_year

    international_tourists_growth = 0.08
    hotel_guests_growth = 0.08
    hotels_growth = 0.04
    companies_growth = 0.07
    heritage_growth = 0.06
    summer_revenue_growth = 0.10

    return {
        "base_year": base_year,
        "target_year": target_year,
        "assumptions": {
            "international_tourists_growth": international_tourists_growth,
            "hotel_guests_growth": hotel_guests_growth,
            "hotels_growth": hotels_growth,
            "companies_growth": companies_growth,
            "heritage_growth": heritage_growth,
            "summer_revenue_growth": summer_revenue_growth
        },
        "international_tourists_2035": round(data["international_tourists"] * ((1 + international_tourists_growth) ** years)),
        "hotel_guests_2035": round(data["hotel_guests"] * ((1 + hotel_guests_growth) ** years)),
        "hotels_2035": round(data["hotels"] * ((1 + hotels_growth) ** years)),
        "companies_2035": round(data["tourism_companies"] * ((1 + companies_growth) ** years)),
        "heritage_visitors_2035": round(data["heritage_visitors"] * ((1 + heritage_growth) ** years)),
        "summer_revenue_lyd_2035": round(data["summer_revenue_lyd"] * ((1 + summer_revenue_growth) ** years))
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "data_file": str(DATA_PATH),
        "data_exists": DATA_PATH.exists()
    }
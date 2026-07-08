from fastapi import FastAPI
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

@app.get("/")
def home():
    return {
        "system": "Libya Tourism KPI Platform",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/api/kpis")
def get_kpis():
    with open(DATA_PATH, "r", encoding="utf-8") as file:
        return json.load(file)

@app.get("/api/forecast/2035")
def forecast_2035():
    with open(DATA_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    base_year = 2025
    target_year = 2035
    years = target_year - base_year
    growth_rate = 0.08

    return {
        "base_year": base_year,
        "target_year": target_year,
        "growth_rate": growth_rate,
        "international_tourists_2035": round(data["international_tourists"] * ((1 + growth_rate) ** years)),
        "hotel_guests_2035": round(data["hotel_guests"] * ((1 + growth_rate) ** years)),
        "hotels_2035": round(data["hotels"] * ((1 + 0.04) ** years)),
        "companies_2035": round(data["tourism_companies"] * ((1 + 0.07) ** years))
    }
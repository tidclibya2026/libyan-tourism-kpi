from fastapi import APIRouter, HTTPException
from app.services.data_service import load_tourism_data
from app.services.kpi_engine import city_metrics

router = APIRouter(prefix="/api/cities", tags=["Cities"])

@router.get("")
def get_cities():
    data = load_tourism_data()
    cities = data.get("cities", [])
    total_guests = sum(city["total_guests"] for city in cities)

    return {
        "year": data["year"],
        "total_guests": total_guests,
        "cities_count": len(cities),
        "cities": sorted(
            [city_metrics(city, total_guests) for city in cities],
            key=lambda x: x["total_guests"],
            reverse=True
        )
    }

@router.get("/{city_id}")
def get_city(city_id: str):
    data = load_tourism_data()
    cities = data.get("cities", [])
    total_guests = sum(city["total_guests"] for city in cities)

    for city in cities:
        if city["id"] == city_id:
            return city_metrics(city, total_guests)

    raise HTTPException(status_code=404, detail="City not found")
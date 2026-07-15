"""天气路由"""
from fastapi import APIRouter
from app.models.schemas import WeatherRequest, WeatherResponse
from app.services.weather_service import fetch_weather_forecast

router = APIRouter(prefix="/weather", tags=["天气"])


@router.get("/forecast", response_model=WeatherResponse)
def weather_forecast(city: str):
    forecasts = fetch_weather_forecast(city)
    return WeatherResponse(city=city, forecasts=forecasts)

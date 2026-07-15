"""
天气服务 — 高德天气 API
"""
import httpx
from app.config import AMAP_API_KEY, AMAP_BASE_URL
from app.models.schemas import WeatherForecast


def fetch_weather_forecast(city: str) -> list[WeatherForecast]:
    """
    查询城市未来天气预报。
    返回 WeatherForecast 列表。
    """
    if not AMAP_API_KEY:
        return []

    try:
        resp = httpx.get(
            f"{AMAP_BASE_URL}/weather/weatherInfo",
            params={
                "key": AMAP_API_KEY,
                "city": city,
                "extensions": "all",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "1":
            return []

        forecasts = []
        for cast in data.get("forecasts", [{}])[0].get("casts", []):
            forecasts.append(WeatherForecast(
                date=cast.get("date", ""),
                day_weather=cast.get("dayweather", ""),
                night_weather=cast.get("nightweather", ""),
                day_temp=int(cast.get("daytemp", 0)),
                night_temp=int(cast.get("nighttemp", 0)),
                wind_direction=cast.get("daywind", ""),
                wind_power=cast.get("daypower", ""),
            ))
        return forecasts

    except Exception:
        return []

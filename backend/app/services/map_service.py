"""
地图服务 — 高德地图 API（地理编码 + POI搜索 + 路线）
"""
import httpx
from app.config import AMAP_API_KEY, AMAP_BASE_URL
from app.models.schemas import Location


def geocode_address(address: str, city: str = "") -> Location:
    """地址转经纬度"""
    if not AMAP_API_KEY:
        return Location()

    try:
        params = {"key": AMAP_API_KEY, "address": address}
        if city:
            params["city"] = city

        resp = httpx.get(
            f"{AMAP_BASE_URL}/geocode/geo",
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        geocodes = data.get("geocodes", [])
        if geocodes:
            location_str = geocodes[0].get("location", "")
            if location_str and "," in location_str:
                lng, lat = location_str.split(",")
                return Location(
                    address=geocodes[0].get("formatted_address", address),
                    longitude=float(lng),
                    latitude=float(lat),
                )
    except Exception:
        pass

    return Location()


def search_places(keywords: str, city: str = "", offset: int = 3) -> list[dict]:
    """POI 搜索"""
    if not AMAP_API_KEY:
        return []

    try:
        params = {
            "key": AMAP_API_KEY,
            "keywords": keywords,
            "offset": offset,
            "output": "JSON",
        }
        if city:
            params["city"] = city

        resp = httpx.get(
            f"{AMAP_BASE_URL}/place/text",
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        results = []
        for poi in data.get("pois", []):
            location_str = poi.get("location", "")
            lng, lat = (0.0, 0.0)
            if location_str and "," in location_str:
                parts = location_str.split(",")
                lng, lat = float(parts[0]), float(parts[1])

            photos = poi.get("photos", [])
            image_url = photos[0].get("url", "") if photos else ""

            results.append({
                "name": poi.get("name", keywords),
                "address": poi.get("address", ""),
                "longitude": lng,
                "latitude": lat,
                "poi_id": poi.get("id", ""),
                "image_url": image_url,
            })
        return results

    except Exception:
        return []


def enrich_itinerary_with_map(itinerary):
    """
    给 Itinerary 中每个景点的 Location 补充实地坐标。
    直接修改传入的 itinerary 对象。
    """
    if not AMAP_API_KEY:
        return

    destination = itinerary.destination
    for day in itinerary.days:
        for spot in day.spots:
            if not spot.name:
                continue
            # 尝试用景点名搜索
            loc = geocode_address(spot.name, city=destination)
            if loc.latitude:
                spot.location = loc

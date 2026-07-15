"""
行程服务 — 主编排逻辑
串联 RAG → LLM 生成 → 预算计算 → 组装 Itinerary
"""
import uuid
from datetime import date, datetime, timedelta
from app.agents.trip_planner_agent import generate_planner_draft, edit_day_draft
from typing import Optional
from app.models.schemas import (
    Itinerary, DayPlan, SpotItem, MealItem, HotelItem, BudgetBreakdown,
    Location, TokenUsage, TripRequest,
)
from app.services.map_service import enrich_itinerary_with_map
from app.config import ENABLE_AMAP_ENRICHMENT


def _estimate_ticket_cost(spot_name: str) -> float:
    """估算单个景点门票费用"""
    name_lower = spot_name.lower()
    # 古城类免费
    if any(w in name_lower for w in ["古城", "古镇", "古街", "回民街", "锦里", "宽窄巷子"]):
        return 0
    # 寺庙类
    if any(w in name_lower for w in ["寺", "庙", "塔"]):
        return 60
    # 索道/山
    if any(w in name_lower for w in ["索道", "山"]):
        return 150
    # 博物馆类
    if any(w in name_lower for w in ["博物馆"]):
        return 0
    # 岛屿/离岛
    if any(w in name_lower for w in ["岛"]):
        return 120
    # 一般景点
    return 50


def _format_date(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def generate_trip_itinerary(req: TripRequest) -> Itinerary:
    """
    核心方法：根据请求生成完整行程。

    流程：
    1. 计算天数
    2. 调用 LLM 生成草稿
    3. 组装 DayPlan 列表
    4. 计算预算拆分
    5. 返回完整 Itinerary
    """
    start_date = date.fromisoformat(req.start_date)
    end_date = date.fromisoformat(req.end_date)
    day_count = (end_date - start_date).days + 1
    if day_count <= 0:
        raise ValueError("结束日期必须晚于开始日期")

    trip_id = uuid.uuid4().hex[:12]

    # ① LLM 生成草稿
    draft = generate_planner_draft(
        destination=req.destination,
        day_count=day_count,
        travelers=req.travelers,
        budget=req.budget,
        preferences=req.preferences or "",
        pace=req.pace or "适中",
        special_notes=req.special_notes or "",
        hotel_level=req.hotel_level or "舒适型",
    )

    # ② 组装 DayPlan 列表
    days = []
    current_date = start_date
    total_tickets = 0.0
    total_meals = 0.0
    total_transport = 0.0
    total_hotel = 0.0

    # 住宿单价（按档次估算）
    hotel_price_map = {"经济型": 150, "舒适型": 250, "豪华型": 500}
    hotel_price = hotel_price_map.get(req.hotel_level or "舒适型", 250)

    # 餐费标准（每人每天）
    meal_daily = 80 if (req.preferences and "美食" in req.preferences) else 60

    for day_data in draft.get("days", []):
        day_idx = day_data["day_index"]

        # 景点
        spot = SpotItem(
            name=day_data.get("spot_name", f"{req.destination}游览"),
            description=day_data.get("spot_description", ""),
            estimated_cost=_estimate_ticket_cost(day_data.get("spot_name", "")),
        )
        total_tickets += spot.estimated_cost or 0

        # 餐食
        meal = MealItem(
            type="正餐",
            name=day_data.get("meal_name", "当地特色餐"),
            description=day_data.get("meal_notes", ""),
            estimated_cost=meal_daily * req.travelers,
        )
        total_meals += meal.estimated_cost or 0

        # 交通（首尾日偏高）
        is_first_or_last = day_idx == 0 or day_idx == day_count - 1
        transport_cost = 100 if is_first_or_last else 50
        total_transport += transport_cost

        # 住宿（最后一天不需要）
        hotel = None
        if day_idx < day_count - 1:
            total_hotel += hotel_price * req.travelers
            hotel_name = day_data.get("hotel_name", "")
            hotel_notes = day_data.get("hotel_notes", "")
            if hotel_name:
                hotel = HotelItem(
                    name=hotel_name,
                    level=req.hotel_level or "舒适型",
                    estimated_cost=hotel_price * req.travelers,
                    notes=hotel_notes,
                )

        day_plan = DayPlan(
            day_index=day_idx,
            date=_format_date(current_date),
            theme=day_data.get("theme", f"第{day_idx+1}天"),
            spots=[spot],
            meals=[meal],
            hotel=hotel,
            notes=day_data.get("daily_note", ""),
        )
        days.append(day_plan)
        current_date += timedelta(days=1)

    # ③ 预算拆分
    remaining = (req.budget or 0) - total_tickets - total_meals - total_transport - total_hotel
    budget_breakdown = BudgetBreakdown(
        transport=round(total_transport, 2),
        hotel=round(total_hotel, 2),
        meals=round(total_meals, 2),
        tickets=round(total_tickets, 2),
        other=round(max(remaining, 0), 2),
        total=round(req.budget or 0, 2),
    )

    # ④ 组装完整 Itinerary
    itinerary = Itinerary(
        trip_id=trip_id,
        destination=req.destination,
        summary=draft.get("summary", f"{req.destination}{day_count}日游"),
        days=days,
        estimated_budget=req.budget or 0,
        budget_breakdown=budget_breakdown,
        tips=draft.get("tips", []),
        source_notes=[f"基于 {len(draft.get('days',[]))} 天模板 + RAG 攻略生成"],
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )

    # ⑤ 高德地图坐标补全（如果启用）
    if ENABLE_AMAP_ENRICHMENT:
        try:
            enrich_itinerary_with_map(itinerary)
        except Exception:
            pass

    return itinerary


def _build_location(loc) -> Optional[Location]:
    """从 LLM 返回的 dict 构造 Location（无有效信息返回 None）"""
    if not isinstance(loc, dict):
        return None
    lat = loc.get("latitude")
    lng = loc.get("longitude")
    addr = loc.get("address")
    if lat is None and lng is None and not addr:
        return None
    return Location(
        address=addr or "",
        latitude=lat,
        longitude=lng,
        poi_id=loc.get("poi_id") or "",
    )


def edit_itinerary_day(itinerary: Itinerary, day_index: int, instruction: str) -> Itinerary:
    """
    智能编辑：用自然语言指令修改某一天的行程。

    LLM 返回的是与 DayPlan 一致的嵌套结构（spots 数组 / meals 数组 / hotel 对象），
    这里正确解析嵌套结构，同时兼容扁平的 spot_name / meal_name / hotel_name 兜底。

    返回修改后的完整 Itinerary。
    """
    if day_index < 0 or day_index >= len(itinerary.days):
        raise ValueError(f"day_index {day_index} 超出范围 (0~{len(itinerary.days)-1})")

    target_day = itinerary.days[day_index]

    # 将当前 DayPlan 转为 JSON 喂给 LLM
    current_day_json = target_day.model_dump_json()

    # 调用 LLM 编辑
    edited = edit_day_draft(
        destination=itinerary.destination,
        current_day_json=current_day_json,
        instruction=instruction,
    )

    # 主题 / 备注
    if edited.get("theme"):
        target_day.theme = edited["theme"]
    notes = edited.get("notes")
    if notes is None:
        notes = edited.get("daily_note")
    if notes is not None:
        target_day.notes = notes

    # 景点：优先解析嵌套 spots 数组，兜底解析扁平 spot_name
    new_spots = edited.get("spots")
    if isinstance(new_spots, list) and new_spots:
        target_day.spots = [
            SpotItem(
                name=s.get("name", "景点"),
                description=s.get("description", ""),
                estimated_cost=_estimate_ticket_cost(s.get("name", "")),
                location=_build_location(s.get("location")),
            )
            for s in new_spots
        ]
    elif edited.get("spot_name"):
        if target_day.spots:
            target_day.spots[0].name = edited["spot_name"]
            if edited.get("spot_description"):
                target_day.spots[0].description = edited["spot_description"]
            target_day.spots[0].estimated_cost = _estimate_ticket_cost(edited["spot_name"])
        else:
            target_day.spots = [SpotItem(
                name=edited["spot_name"],
                description=edited.get("spot_description", ""),
                estimated_cost=_estimate_ticket_cost(edited["spot_name"]),
            )]

    # 餐食
    new_meals = edited.get("meals")
    if isinstance(new_meals, list) and new_meals:
        target_day.meals = [
            MealItem(
                type=m.get("type", "正餐"),
                name=m.get("name", "餐饮"),
                description=m.get("description", ""),
                estimated_cost=m.get("estimated_cost"),
            )
            for m in new_meals
        ]
    elif edited.get("meal_name"):
        if target_day.meals:
            target_day.meals[0].name = edited["meal_name"]
            if edited.get("meal_notes"):
                target_day.meals[0].description = edited["meal_notes"]
        else:
            target_day.meals = [MealItem(
                name=edited["meal_name"],
                description=edited.get("meal_notes", ""),
            )]

    # 住宿
    new_hotel = edited.get("hotel")
    if isinstance(new_hotel, dict) and new_hotel.get("name"):
        target_day.hotel = HotelItem(
            name=new_hotel["name"],
            level=new_hotel.get("level", target_day.hotel.level if target_day.hotel else "舒适型"),
            estimated_cost=new_hotel.get("estimated_cost"),
            location=_build_location(new_hotel.get("location")),
            notes=new_hotel.get("notes", ""),
        )
    elif edited.get("hotel_name"):
        target_day.hotel = HotelItem(
            name=edited["hotel_name"],
            level=target_day.hotel.level if target_day.hotel else "舒适型",
            notes=edited.get("hotel_notes", ""),
        )

    # 重新补地图坐标
    if ENABLE_AMAP_ENRICHMENT:
        try:
            enrich_itinerary_with_map(itinerary)
        except Exception:
            pass

    itinerary.updated_at = datetime.now().isoformat()
    return itinerary

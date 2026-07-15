"""
数据模型 — Pydantic schemas
定义请求体、响应体、行程结构
"""
import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ═══════════════════════════════════════════
# 请求模型
# ═══════════════════════════════════════════

class TripRequest(BaseModel):
    """生成行程的请求"""
    destination: str = Field(..., description="目的地，如'大理'")
    start_date: str = Field(..., description="出发日期，如'2026-08-01'")
    end_date: str = Field(..., description="结束日期，如'2026-08-03'")
    travelers: int = Field(default=1, ge=1, description="出行人数")
    budget: Optional[float] = Field(default=None, ge=0, description="总预算(元)")
    preferences: Optional[str] = Field(default="", description="偏好，如'偏爱自然风光'")
    pace: Optional[str] = Field(default="适中", description="节奏：轻松/适中/紧凑")
    dietary_preferences: Optional[str] = Field(default="", description="饮食偏好")
    hotel_level: Optional[str] = Field(default="舒适型", description="住宿档次")
    special_notes: Optional[str] = Field(default="", description="额外要求")


class TripEditRequest(BaseModel):
    """智能编辑请求"""
    trip_id: str = Field(..., description="行程ID")
    day_index: int = Field(..., description="要编辑的天数(从0开始)")
    instruction: str = Field(..., description="编辑指令，如'把下午的行程换成逛古城'")


class TripSaveRequest(BaseModel):
    """保存行程请求"""
    trip_id: str
    destination: str
    summary: str
    itinerary_json: str = Field(..., description="完整Itinerary的JSON字符串")


# ═══════════════════════════════════════════
# 行程实体模型
# ═══════════════════════════════════════════

class Location(BaseModel):
    """地理位置"""
    address: Optional[str] = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    poi_id: Optional[str] = ""


class SpotItem(BaseModel):
    """单个景点"""
    name: str
    start_time: Optional[str] = ""
    end_time: Optional[str] = ""
    description: Optional[str] = ""
    estimated_cost: Optional[float] = 0.0
    location: Optional[Location] = Field(default_factory=Location)
    image_url: Optional[str] = ""


class MealItem(BaseModel):
    """餐饮安排"""
    type: str = Field(default="正餐", description="早餐/午餐/晚餐/小吃")
    name: str
    description: Optional[str] = ""
    estimated_cost: Optional[float] = 0.0


class HotelItem(BaseModel):
    """住宿安排"""
    name: str
    level: Optional[str] = "舒适型"
    estimated_cost: Optional[float] = 0.0
    location: Optional[Location] = Field(default_factory=Location)
    notes: Optional[str] = ""


class TransportItem(BaseModel):
    """单段交通"""
    from_place: str = Field(default="", alias="from")
    to_place: str = Field(default="", alias="to")
    mode: Optional[str] = "驾车"
    distance_km: Optional[float] = None
    duration_min: Optional[int] = None
    estimated_cost: Optional[float] = 0.0

    class Config:
        populate_by_name = True


class BudgetBreakdown(BaseModel):
    """预算拆分"""
    transport: float = 0.0
    hotel: float = 0.0
    meals: float = 0.0
    tickets: float = 0.0
    other: float = 0.0
    total: float = 0.0


class DayPlan(BaseModel):
    """单日行程"""
    day_index: int
    date: Optional[str] = ""
    theme: Optional[str] = ""
    spots: list[SpotItem] = Field(default_factory=list)
    meals: list[MealItem] = Field(default_factory=list)
    hotel: Optional[HotelItem] = None
    transport: list[TransportItem] = Field(default_factory=list)
    notes: Optional[str] = ""


class TokenUsage(BaseModel):
    """各阶段 Token 消耗统计"""
    rewrite_prompt: int = 0
    rewrite_completion: int = 0
    embedding_total: int = 0
    planner_prompt: int = 0
    planner_completion: int = 0
    rerank_total: int = 0


class Itinerary(BaseModel):
    """完整行程"""
    trip_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    destination: str
    summary: str = ""
    days: list[DayPlan] = Field(default_factory=list)
    estimated_budget: float = 0.0
    budget_breakdown: BudgetBreakdown = Field(default_factory=BudgetBreakdown)
    tips: list[str] = Field(default_factory=list)
    source_notes: list[str] = Field(default_factory=list)
    token_usage: Optional[TokenUsage] = None
    created_at: Optional[str] = ""
    updated_at: Optional[str] = ""


# ═══════════════════════════════════════════
# 响应模型
# ═══════════════════════════════════════════

class TripGenerateResponse(BaseModel):
    """行程生成响应"""
    trip_id: str
    itinerary: Itinerary
    token_usage: Optional[TokenUsage] = None


class TripEditResponse(BaseModel):
    """编辑响应"""
    trip_id: str
    itinerary: Itinerary


class TripSummaryItem(BaseModel):
    """历史列表中的摘要项"""
    trip_id: str
    destination: str
    summary: str
    created_at: str
    updated_at: str


class TripListResponse(BaseModel):
    """历史列表响应"""
    trips: list[TripSummaryItem]


class TripSaveResponse(BaseModel):
    """保存响应"""
    trip_id: str
    message: str = "保存成功"


class TokenStatsResponse(BaseModel):
    """Token统计响应"""
    total_trips: int
    total_prompt_tokens: int
    total_completion_tokens: int
    details: list[dict] = Field(default_factory=list)


class WeatherRequest(BaseModel):
    """天气查询请求"""
    city: str = Field(..., description="城市名，如'大理'")


class WeatherForecast(BaseModel):
    """天气信息"""
    date: str
    day_weather: str = ""
    night_weather: str = ""
    day_temp: int = 0
    night_temp: int = 0
    wind_direction: str = ""
    wind_power: str = ""


class WeatherResponse(BaseModel):
    """天气响应"""
    city: str
    forecasts: list[WeatherForecast] = Field(default_factory=list)

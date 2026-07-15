"""
行程路由 — /trip 相关接口
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config import get_db
from app.models.schemas import (
    TripRequest, TripEditRequest, TripSaveRequest,
    TripGenerateResponse, TripListResponse, TripSaveResponse, TripEditResponse,
)
from app.services.trip_service import generate_trip_itinerary, edit_itinerary_day
from app.services.storage_service import (
    save_itinerary, get_itinerary_by_trip_id,
    list_saved_itineraries, delete_itinerary,
)

router = APIRouter(prefix="/trip", tags=["行程"])


@router.post("/generate", response_model=TripGenerateResponse)
def generate_trip(req: TripRequest, db: Session = Depends(get_db)):
    """生成旅行行程（并自动保存到数据库）"""
    itinerary = generate_trip_itinerary(req)
    # 自动保存，确保导出等功能立即可用
    save_itinerary(db, itinerary)
    return TripGenerateResponse(
        trip_id=itinerary.trip_id,
        itinerary=itinerary,
    )


@router.post("/save", response_model=TripSaveResponse)
def save_trip(req: TripSaveRequest, db: Session = Depends(get_db)):
    """保存行程到数据库"""
    from app.models.schemas import Itinerary
    itinerary = Itinerary.model_validate_json(req.itinerary_json)
    trip_id = save_itinerary(db, itinerary)
    return TripSaveResponse(trip_id=trip_id)


@router.post("/edit")
def edit_trip(req: TripEditRequest, db: Session = Depends(get_db)):
    """智能编辑某天行程"""
    itinerary = get_itinerary_by_trip_id(db, req.trip_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="行程不存在")

    edited = edit_itinerary_day(itinerary, req.day_index, req.instruction)
    save_itinerary(db, edited)
    return {"trip_id": edited.trip_id, "itinerary": edited.model_dump()}


@router.get("", response_model=TripListResponse)
def list_trips(db: Session = Depends(get_db)):
    """列出所有已保存行程"""
    trips = list_saved_itineraries(db)
    return TripListResponse(trips=trips)


@router.get("/{trip_id}")
def get_trip(trip_id: str, db: Session = Depends(get_db)):
    """查询单个行程详情"""
    itinerary = get_itinerary_by_trip_id(db, trip_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="行程不存在")
    return itinerary


@router.delete("/{trip_id}")
def delete_trip(trip_id: str, db: Session = Depends(get_db)):
    """删除行程"""
    ok = delete_itinerary(db, trip_id)
    if not ok:
        raise HTTPException(status_code=404, detail="行程不存在")
    return {"message": "删除成功"}

"""
存储服务 — SQLite 持久化
"""
import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.db_models import TripRecord
from app.models.schemas import Itinerary, TripSummaryItem


def save_itinerary(db: Session, itinerary: Itinerary) -> str:
    """保存行程（UPSERT）"""
    existing = db.query(TripRecord).filter(
        TripRecord.trip_id == itinerary.trip_id
    ).first()

    itinerary_json = itinerary.model_dump_json()
    now = datetime.utcnow()

    if existing:
        existing.destination = itinerary.destination
        existing.summary = itinerary.summary
        existing.itinerary_json = itinerary_json
        existing.updated_at = now
    else:
        record = TripRecord(
            trip_id=itinerary.trip_id,
            destination=itinerary.destination,
            summary=itinerary.summary,
            itinerary_json=itinerary_json,
            created_at=now,
            updated_at=now,
        )
        db.add(record)

    db.commit()
    return itinerary.trip_id


def get_itinerary_by_trip_id(db: Session, trip_id: str) -> Itinerary | None:
    """查询单个行程"""
    record = db.query(TripRecord).filter(
        TripRecord.trip_id == trip_id
    ).first()
    if not record:
        return None
    return Itinerary.model_validate_json(record.itinerary_json)


def list_saved_itineraries(db: Session) -> list[TripSummaryItem]:
    """列出所有已保存行程摘要"""
    records = db.query(TripRecord).order_by(
        TripRecord.updated_at.desc()
    ).all()

    return [
        TripSummaryItem(
            trip_id=r.trip_id,
            destination=r.destination,
            summary=r.summary,
            created_at=r.created_at.isoformat() if r.created_at else "",
            updated_at=r.updated_at.isoformat() if r.updated_at else "",
        )
        for r in records
    ]


def delete_itinerary(db: Session, trip_id: str) -> bool:
    """删除行程"""
    record = db.query(TripRecord).filter(
        TripRecord.trip_id == trip_id
    ).first()
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True

"""
数据库模型 — SQLAlchemy ORM
"""
from datetime import datetime
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.config import Base


class TripRecord(Base):
    """保存的行程记录"""
    __tablename__ = "trip_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    trip_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, comment="行程唯一ID")
    destination: Mapped[str] = mapped_column(String(100), comment="目的地")
    summary: Mapped[str] = mapped_column(Text, default="", comment="行程概要")
    itinerary_json: Mapped[str] = mapped_column(Text, comment="完整行程JSON")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    def __repr__(self):
        return f"<TripRecord(trip_id={self.trip_id}, destination={self.destination})>"

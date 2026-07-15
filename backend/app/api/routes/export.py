"""导出路由 — Markdown / PDF"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, PlainTextResponse
from sqlalchemy.orm import Session
from app.config import get_db
from app.services.storage_service import get_itinerary_by_trip_id
from app.services.export_service import itinerary_to_markdown, itinerary_to_pdf_bytes

router = APIRouter(prefix="/export", tags=["导出"])


@router.get("/{trip_id}/markdown")
def export_markdown(trip_id: str, db: Session = Depends(get_db)):
    itinerary = get_itinerary_by_trip_id(db, trip_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="行程不存在")
    md = itinerary_to_markdown(itinerary)
    return PlainTextResponse(
        content=md,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={trip_id}.md"},
    )


@router.get("/{trip_id}/pdf")
def export_pdf(trip_id: str, db: Session = Depends(get_db)):
    itinerary = get_itinerary_by_trip_id(db, trip_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="行程不存在")
    pdf_bytes = itinerary_to_pdf_bytes(itinerary)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={trip_id}.pdf"},
    )

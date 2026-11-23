from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database.session import get_db
from backend.app.models.license_plate import LicensePlate
from backend.app.models.vehicle_detection import VehicleDetection

router = APIRouter()


@router.get("/plates", summary="Search and Filter Recognized Plates")
def list_plates(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    query: Optional[str] = None,
    validation_status: Optional[str] = None,
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
):
    q = db.query(LicensePlate)

    if query:
        q = q.filter(LicensePlate.normalized_text.ilike(f"%{query.strip().upper()}%"))
    if validation_status:
        q = q.filter(LicensePlate.validation_status == validation_status)
    if min_confidence is not None:
        q = q.filter(LicensePlate.ocr_confidence >= min_confidence)

    total = q.count()
    records = q.order_by(desc(LicensePlate.created_at)).offset(skip).limit(limit).all()

    items = []
    for p in records:
        v = db.query(VehicleDetection).filter(VehicleDetection.id == p.vehicle_detection_id).first()
        items.append({
            "id": p.id,
            "vehicle_detection_id": p.vehicle_detection_id,
            "tracking_id": v.tracking_id if v else None,
            "vehicle_type": v.vehicle_type if v else "unknown",
            "raw_text": p.raw_text,
            "normalized_text": p.normalized_text,
            "ocr_confidence": p.ocr_confidence,
            "plate_confidence": p.plate_confidence,
            "validation_status": p.validation_status,
            "plate_image_path": p.plate_image_path,
            "created_at": p.created_at,
        })

    return {"total": total, "items": items, "skip": skip, "limit": limit}


@router.get("/plates/{id}", summary="Get License Plate by ID")
def get_plate(id: int, db: Session = Depends(get_db)):
    plate = db.query(LicensePlate).filter(LicensePlate.id == id).first()
    if not plate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License plate record not found.")

    v = db.query(VehicleDetection).filter(VehicleDetection.id == plate.vehicle_detection_id).first()
    return {
        "id": plate.id,
        "vehicle_detection_id": plate.vehicle_detection_id,
        "vehicle_type": v.vehicle_type if v else "unknown",
        "tracking_id": v.tracking_id if v else None,
        "raw_text": plate.raw_text,
        "normalized_text": plate.normalized_text,
        "ocr_confidence": plate.ocr_confidence,
        "plate_confidence": plate.plate_confidence,
        "validation_status": plate.validation_status,
        "plate_image_path": plate.plate_image_path,
        "created_at": plate.created_at,
    }

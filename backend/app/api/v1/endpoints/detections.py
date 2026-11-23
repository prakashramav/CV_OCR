from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database.session import get_db
from backend.app.models.vehicle_detection import VehicleDetection
from backend.app.models.license_plate import LicensePlate
from backend.app.schemas.detection_schema import VehicleDetectionResponse

router = APIRouter()


@router.get("/detections", summary="Query Vehicle Detections")
def list_detections(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    vehicle_type: Optional[str] = None,
    source_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(VehicleDetection)
    if vehicle_type:
        query = query.filter(VehicleDetection.vehicle_type == vehicle_type.lower())
    if source_type:
        query = query.filter(VehicleDetection.source_type == source_type.lower())

    total = query.count()
    records = query.order_by(desc(VehicleDetection.detected_at)).offset(skip).limit(limit).all()

    items = []
    for r in records:
        plate = db.query(LicensePlate).filter(LicensePlate.vehicle_detection_id == r.id).first()
        items.append({
            "id": r.id,
            "tracking_id": r.tracking_id,
            "vehicle_type": r.vehicle_type,
            "vehicle_confidence": r.vehicle_confidence,
            "detected_at": r.detected_at,
            "source_type": r.source_type,
            "source_name": r.source_name,
            "plate_number": plate.normalized_text if plate else None,
            "ocr_confidence": plate.ocr_confidence if plate else None,
            "plate_image_path": plate.plate_image_path if plate else None,
        })

    return {"total": total, "items": items, "skip": skip, "limit": limit}


@router.get("/detections/{id}", summary="Get Vehicle Detection by ID")
def get_detection(id: int, db: Session = Depends(get_db)):
    det = db.query(VehicleDetection).filter(VehicleDetection.id == id).first()
    if not det:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle detection not found.")

    plates = db.query(LicensePlate).filter(LicensePlate.vehicle_detection_id == det.id).all()
    return {
        "id": det.id,
        "tracking_id": det.tracking_id,
        "vehicle_type": det.vehicle_type,
        "vehicle_confidence": det.vehicle_confidence,
        "detected_at": det.detected_at,
        "source_type": det.source_type,
        "source_name": det.source_name,
        "plates": [
            {
                "id": p.id,
                "raw_text": p.raw_text,
                "normalized_text": p.normalized_text,
                "ocr_confidence": p.ocr_confidence,
                "validation_status": p.validation_status,
                "plate_image_path": p.plate_image_path,
            }
            for p in plates
        ],
    }

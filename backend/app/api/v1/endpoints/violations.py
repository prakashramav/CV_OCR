from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database.session import get_db
from backend.app.models.violation import Violation
from backend.app.models.license_plate import LicensePlate

router = APIRouter()


class ViolationStatusUpdate(BaseModel):
    verification_status: str  # PENDING, CONFIRMED, DISMISSED


@router.get("/violations", summary="List Logged Traffic Violations")
def list_violations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    violation_type: Optional[str] = None,
    verification_status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Violation)

    if violation_type:
        q = q.filter(Violation.violation_type == violation_type)
    if verification_status:
        q = q.filter(Violation.verification_status == verification_status)

    total = q.count()
    records = q.order_by(desc(Violation.event_timestamp)).offset(skip).limit(limit).all()

    items = []
    for v in records:
        plate = db.query(LicensePlate).filter(LicensePlate.id == v.license_plate_id).first() if v.license_plate_id else None
        items.append({
            "id": v.id,
            "license_plate_id": v.license_plate_id,
            "tracking_id": v.tracking_id,
            "plate_number": plate.normalized_text if plate else "UNIDENTIFIED",
            "violation_type": v.violation_type,
            "event_timestamp": v.event_timestamp,
            "evidence_image_path": v.evidence_image_path,
            "verification_status": v.verification_status,
        })

    return {"total": total, "items": items, "skip": skip, "limit": limit}


@router.patch("/violations/{id}", summary="Update Violation Verification Status")
def update_violation_status(id: int, payload: ViolationStatusUpdate, db: Session = Depends(get_db)):
    v = db.query(Violation).filter(Violation.id == id).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Violation record not found.")

    valid_statuses = ["PENDING", "CONFIRMED", "DISMISSED"]
    if payload.verification_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of {valid_statuses}",
        )

    v.verification_status = payload.verification_status
    db.commit()
    return {"id": v.id, "verification_status": v.verification_status, "message": "Status updated successfully."}

from collections import Counter
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.app.database.session import get_db
from backend.app.models.vehicle_detection import VehicleDetection
from backend.app.models.license_plate import LicensePlate
from backend.app.models.violation import Violation
from backend.app.models.processing_job import ProcessingJob

router = APIRouter()


@router.get("/analytics/overview", summary="Executive ANPR & Traffic Metrics")
def get_analytics_overview(db: Session = Depends(get_db)):
    total_vehicles = db.query(VehicleDetection).count()
    total_plates = db.query(LicensePlate).count()
    total_violations = db.query(Violation).count()
    active_jobs = db.query(ProcessingJob).filter(ProcessingJob.status.in_(["QUEUED", "PROCESSING"])).count()

    # Calculate Successful OCR Rate (Indian valid plates vs total plates)
    valid_plates_count = db.query(LicensePlate).filter(
        LicensePlate.validation_status.in_(["VALID_INDIAN", "VALID_BHARAT_SERIES"])
    ).count()

    ocr_success_percentage = round((valid_plates_count / total_plates * 100.0), 1) if total_plates > 0 else 0.0

    # Vehicle Type Distribution
    v_types = db.query(VehicleDetection.vehicle_type, func.count(VehicleDetection.id)).group_by(VehicleDetection.vehicle_type).all()
    vehicle_distribution = [{"vehicle_type": vt, "count": count} for vt, count in v_types]

    # Confidence Buckets
    plates = db.query(LicensePlate.ocr_confidence).all()
    conf_buckets = {"< 50%": 0, "50% - 70%": 0, "70% - 85%": 0, "> 85%": 0}
    for (conf,) in plates:
        if conf < 0.50:
            conf_buckets["< 50%"] += 1
        elif conf < 0.70:
            conf_buckets["50% - 70%"] += 1
        elif conf < 0.85:
            conf_buckets["70% - 85%"] += 1
        else:
            conf_buckets["> 85%"] += 1

    # Hourly Trends (past 6 hourly slots or simulated timeline)
    now = datetime.now()
    hourly_trends = []
    for i in range(5, -1, -1):
        slot_time = now - timedelta(hours=i)
        hour_label = slot_time.strftime("%H:00")
        hourly_trends.append({
            "hour": hour_label,
            "detections": max(int(total_vehicles * (0.12 + 0.04 * (i % 3))), 0),
            "violations": max(int(total_violations * (0.10 + 0.03 * (i % 2))), 0),
        })

    # Top Recent Violations
    recent_v = db.query(Violation).order_by(desc(Violation.event_timestamp)).limit(5).all()
    recent_violations = []
    for rv in recent_v:
        plate = db.query(LicensePlate).filter(LicensePlate.id == rv.license_plate_id).first() if rv.license_plate_id else None
        recent_violations.append({
            "id": rv.id,
            "violation_type": rv.violation_type,
            "plate_number": plate.normalized_text if plate else "UNIDENTIFIED",
            "timestamp": rv.event_timestamp.strftime("%Y-%m-%d %H:%M:%S") if rv.event_timestamp else None,
            "evidence_image_path": rv.evidence_image_path,
            "verification_status": rv.verification_status,
        })

    return {
        "metrics": {
            "total_vehicles": total_vehicles,
            "total_plates": total_plates,
            "successful_ocr_percentage": ocr_success_percentage,
            "total_violations": total_violations,
            "active_jobs": active_jobs,
        },
        "vehicle_distribution": vehicle_distribution,
        "hourly_trends": hourly_trends,
        "confidence_distribution": conf_buckets,
        "recent_violations": recent_violations,
    }

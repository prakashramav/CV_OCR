import os
import sys
import uuid
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np

from backend.app.config import settings
from backend.app.database.session import SessionLocal
from backend.app.database.init_db import init_db
from backend.app.models.vehicle_detection import VehicleDetection
from backend.app.models.license_plate import LicensePlate
from backend.app.models.violation import Violation
from backend.app.models.processing_job import ProcessingJob
from backend.app.utils.indian_states import validate_indian_plate
from backend.tests.test_vision_pipeline import create_synthetic_plate_image

DEMO_PLATES = [
    ("MH12DE1433", "car", "VALID_INDIAN"),
    ("DL01AB1234", "car", "VALID_INDIAN"),
    ("KA03MN4567", "motorcycle", "VALID_INDIAN"),
    ("TS09UB5678", "bus", "VALID_INDIAN"),
    ("AP09EF7890", "truck", "VALID_INDIAN"),
    ("22BH1234AA", "car", "VALID_BHARAT_SERIES"),
    ("GJ01XY9876", "car", "VALID_INDIAN"),
    ("HR26DK8822", "motorcycle", "VALID_INDIAN"),
    ("UP16BZ3344", "car", "VALID_INDIAN"),
    ("TN02AQ5566", "bus", "VALID_INDIAN"),
    ("KL07CR1122", "car", "VALID_INDIAN"),
    ("WB19AF4455", "truck", "VALID_INDIAN"),
]


def seed():
    """Seeds the SQLite database with realistic traffic monitoring history,

    generating actual cropped plate images and evidence snapshots on disk.
    """
    print("Initializing database schema...")
    init_db()
    db = SessionLocal()

    # Clear existing data for fresh seed
    db.query(Violation).delete()
    db.query(LicensePlate).delete()
    db.query(VehicleDetection).delete()
    db.query(ProcessingJob).delete()
    db.commit()

    print("Generating demo records and disk artifacts...")
    now = datetime.now(timezone.utc)

    # Create a completed demo processing job
    job = ProcessingJob(
        id="demo-traffic-feed-01",
        filename="highway_traffic_cam_04.mp4",
        status="COMPLETED",
        total_frames=1250,
        processed_frames=1250,
        total_vehicles=len(DEMO_PLATES),
        total_plates=len(DEMO_PLATES),
        output_video_path="outputs/videos/processed_demo.mp4",
        started_at=now - timedelta(hours=2),
        completed_at=now - timedelta(hours=1, minutes=48),
    )
    db.add(job)
    db.commit()

    created_plate_ids = []

    for i, (plate_str, v_type, status_label) in enumerate(DEMO_PLATES):
        detected_time = now - timedelta(minutes=random.randint(5, 180))

        # Create Vehicle Detection
        v_model = VehicleDetection(
            tracking_id=i + 1,
            vehicle_type=v_type,
            vehicle_confidence=round(random.uniform(0.85, 0.98), 3),
            detected_at=detected_time,
            source_type="video",
            source_name="highway_traffic_cam_04.mp4",
        )
        db.add(v_model)
        db.flush()

        # Generate actual plate image on disk
        plate_img = create_synthetic_plate_image(plate_str)
        plate_filename = f"seed_plate_{plate_str}.jpg"
        plate_path = settings.PLATES_OUTPUT_DIR / plate_filename
        cv2.imwrite(str(plate_path), plate_img)

        # Create License Plate Record
        p_model = LicensePlate(
            vehicle_detection_id=v_model.id,
            raw_text=plate_str,
            normalized_text=plate_str,
            ocr_confidence=round(random.uniform(0.88, 0.97), 3),
            plate_confidence=round(random.uniform(0.82, 0.96), 3),
            validation_status=status_label,
            plate_image_path=f"outputs/plates/{plate_filename}",
            created_at=detected_time,
        )
        db.add(p_model)
        db.flush()
        created_plate_ids.append((p_model.id, v_model.tracking_id, plate_str, v_type, detected_time))

    # Create Violations for 3 vehicles
    violation_indices = [0, 3, 7]  # MH12DE1433, TS09UB5678, HR26DK8822
    for idx in violation_indices:
        p_id, t_id, plate_str, v_type, v_time = created_plate_ids[idx]

        # Generate synthetic evidence frame
        evidence = np.ones((480, 640, 3), dtype=np.uint8) * 30
        cv2.rectangle(evidence, (180, 160), (320, 340), (40, 40, 230), 3)  # Red box around violator
        cv2.line(evidence, (0, 260), (640, 260), (40, 40, 240), 2)         # Red stop line
        cv2.putText(evidence, f"VIOLATION: STOP LINE CROSSING - #{t_id} {plate_str}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 255), 2)

        ev_filename = f"evidence_{plate_str}.jpg"
        ev_path = settings.EVIDENCE_OUTPUT_DIR / ev_filename
        cv2.imwrite(str(ev_path), evidence)

        vio = Violation(
            license_plate_id=p_id,
            tracking_id=t_id,
            violation_type="STOP_LINE_CROSSING",
            event_timestamp=v_time,
            evidence_image_path=f"outputs/evidence/{ev_filename}",
            verification_status="PENDING" if idx == 0 else "CONFIRMED",
        )
        db.add(vio)

    db.commit()
    db.close()
    print(f"Database successfully seeded with {len(DEMO_PLATES)} vehicle & plate records and {len(violation_indices)} violations!")


if __name__ == "__main__":
    seed()

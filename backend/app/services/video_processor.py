import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List
import cv2
import numpy as np

from backend.app.config import settings
from backend.app.core.logger import logger
from backend.app.database.session import SessionLocal
from backend.app.models.processing_job import ProcessingJob
from backend.app.models.vehicle_detection import VehicleDetection
from backend.app.models.license_plate import LicensePlate
from backend.app.models.violation import Violation

from backend.app.services.vehicle_detector import VehicleDetector
from backend.app.services.plate_detector import PlateDetector
from backend.app.services.image_preprocessor import ImagePreprocessor
from backend.app.services.ocr_engine import OCREngine
from backend.app.services.vehicle_tracker import VehicleTracker
from backend.app.services.violation_detector import ViolationDetector
from backend.app.utils.drawing import (
    draw_styled_box,
    draw_stop_line,
    draw_hud,
    COLORS,
)


class VideoProcessor:
    """End-to-end background video processing pipeline orchestrator."""

    def __init__(self):
        self.vehicle_detector = VehicleDetector()
        self.plate_detector = PlateDetector()
        self.ocr_engine = OCREngine()

    def process_video_sync(
        self,
        job_id: str,
        input_video_path: str,
        stop_line_y_ratio: Optional[float] = None,
        frame_stride: int = 1,
    ):
        """Processes an entire video file in a background thread and persists state updates to the database."""
        db = SessionLocal()
        job: Optional[ProcessingJob] = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()

        if not job:
            logger.error(f"Processing job {job_id} not found in database.")
            db.close()
            return

        logger.info(f"Starting background video processing for Job: {job_id} | File: {input_video_path}")
        job.status = "PROCESSING"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            error_msg = f"Failed to open video file: {input_video_path}"
            logger.error(error_msg)
            job.status = "FAILED"
            job.error_message = error_msg
            db.commit()
            db.close()
            return

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        orig_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        job.total_frames = total_frames
        db.commit()

        # Output video configuration
        output_filename = f"processed_{job_id}.mp4"
        output_filepath = settings.VIDEOS_OUTPUT_DIR / output_filename
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(output_filepath), fourcc, orig_fps, (width, height))

        # Local tracker and violation detector instances per video stream
        tracker = VehicleTracker(max_stale_frames=30)
        violation_detector = ViolationDetector(stop_line_y_ratio=stop_line_y_ratio)

        frame_idx = 0
        fps_timer = time.time()
        current_fps = orig_fps
        total_unique_plates = 0

        # Maintain created DB records
        created_violations: List[Dict[str, Any]] = []

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret or frame is None:
                    break

                frame_idx += 1

                # Calculate instantaneous processing FPS
                if frame_idx % 10 == 0:
                    now = time.time()
                    elapsed = now - fps_timer
                    current_fps = 10.0 / elapsed if elapsed > 0 else orig_fps
                    fps_timer = now

                # Step 1: Detect Vehicles
                vehicle_dets = self.vehicle_detector.detect(frame)

                # Step 2: Track Vehicles across frames
                tracked_vehicles = tracker.update_tracks(vehicle_dets, frame_idx)

                # Step 3: Detect License Plates inside vehicles
                detected_plates = self.plate_detector.detect_plates(
                    frame=frame,
                    vehicle_detections=tracked_vehicles,
                    save_crops=True,
                )

                # Step 4: Run OCR on newly localized plates and associate with tracks
                for p in detected_plates:
                    v_info = p.get("vehicle_info")
                    crop = p["plate_crop"]
                    ocr_res = self.ocr_engine.recognize(crop)

                    # Augment plate record
                    p["text"] = ocr_res["normalized_text"]
                    p["raw_text"] = ocr_res["raw_text"]
                    p["ocr_confidence"] = ocr_res["ocr_confidence"]
                    p["is_valid"] = ocr_res["is_valid"]
                    p["validation_status"] = ocr_res["validation_status"]
                    p["state_name"] = ocr_res["state_name"]

                    if v_info and "tracking_id" in v_info:
                        tid = v_info["tracking_id"]
                        track = tracker.get_track(tid)
                        if track:
                            track.add_plate_observation({
                                "plate_crop": crop,
                                "plate_image_path": p["plate_image_path"],
                                "bbox": p["bbox"],
                                "plate_confidence": p["confidence"],
                                "raw_text": p["raw_text"],
                                "normalized_text": p["text"],
                                "ocr_confidence": p["ocr_confidence"],
                                "is_valid": p["is_valid"],
                                "validation_status": p["validation_status"],
                                "state_name": p["state_name"],
                            })

                # Step 5: Evaluate Traffic Violations
                active_tracks = [det["track"] for det in tracked_vehicles if "track" in det]
                violations = violation_detector.evaluate_frame(
                    frame=frame,
                    tracks=active_tracks,
                    frame_idx=frame_idx,
                )
                created_violations.extend(violations)

                # Step 6: Render overlays on output frame
                annotated = frame.copy()
                # Draw stop line
                draw_stop_line(annotated, violation_detector.stop_line_y_ratio)
                # Draw tracked vehicles
                for det in tracked_vehicles:
                    bbox = det["bbox"]
                    cname = det["class_name"]
                    tid = det.get("tracking_id")
                    track = det.get("track")
                    label = f"{cname.upper()}"
                    if track and track.best_plate:
                        label += f" | {track.best_plate['normalized_text']}"
                    draw_styled_box(annotated, bbox, COLORS.get(cname, COLORS["vehicle"]), label=label, track_id=tid)

                # Draw plates with gold frame
                annotated = self.plate_detector.draw_plates(annotated, detected_plates)

                # Draw HUD
                total_unique_vehicles = len(tracker.tracks)
                recognized_plates_count = sum(1 for t in tracker.tracks.values() if t.best_plate)
                draw_hud(
                    img=annotated,
                    fps=current_fps,
                    vehicle_count=total_unique_vehicles,
                    plate_count=recognized_plates_count,
                    violation_count=len(created_violations),
                )

                out.write(annotated)

                # Periodic database progress sync (every 25 frames)
                if frame_idx % 25 == 0 or frame_idx == total_frames:
                    job.processed_frames = frame_idx
                    job.total_vehicles = total_unique_vehicles
                    job.total_plates = recognized_plates_count
                    db.commit()

            # Video processing loop completed
            cap.release()
            out.release()

            # Step 7: Persist finalized unique vehicle detections & license plates to DB
            for tid, track in tracker.tracks.items():
                v_model = VehicleDetection(
                    tracking_id=tid,
                    vehicle_type=track.vehicle_type,
                    vehicle_confidence=0.85,
                    detected_at=track.first_seen_time,
                    source_type="video",
                    source_name=job.filename,
                )
                db.add(v_model)
                db.flush()

                track.db_vehicle_id = v_model.id

                if track.best_plate:
                    bp = track.best_plate
                    plate_model = LicensePlate(
                        vehicle_detection_id=v_model.id,
                        raw_text=bp.get("raw_text", ""),
                        normalized_text=bp.get("normalized_text", ""),
                        ocr_confidence=bp.get("ocr_confidence", 0.0),
                        plate_confidence=bp.get("plate_confidence", 0.0),
                        validation_status=bp.get("validation_status", "INVALID"),
                        plate_image_path=bp.get("plate_image_path"),
                        created_at=track.first_seen_time,
                    )
                    db.add(plate_model)
                    db.flush()
                    track.best_plate["db_id"] = plate_model.id

            # Persist captured violations
            for vio in created_violations:
                tid = vio.get("tracking_id")
                track = tracker.get_track(tid) if tid else None
                plate_id = track.best_plate.get("db_id") if (track and track.best_plate) else None

                vio_model = Violation(
                    license_plate_id=plate_id,
                    tracking_id=tid,
                    violation_type=vio["violation_type"],
                    event_timestamp=vio["event_timestamp"],
                    evidence_image_path=vio["evidence_image_path"],
                    verification_status="PENDING",
                )
                db.add(vio_model)

            # Finalize Job Status
            job.status = "COMPLETED"
            job.processed_frames = frame_idx
            job.total_vehicles = len(tracker.tracks)
            job.total_plates = sum(1 for t in tracker.tracks.values() if t.best_plate)
            job.output_video_path = f"outputs/videos/{output_filename}"
            job.completed_at = datetime.now(timezone.utc)
            db.commit()

            logger.info(
                f"Job {job_id} successfully completed! Vehicles: {job.total_vehicles}, Plates: {job.total_plates}, Violations: {len(created_violations)}"
            )

        except Exception as e:
            logger.exception(f"Unhandled error during video processing job {job_id}: {e}")
            job.status = "FAILED"
            job.error_message = str(e)
            db.commit()
        finally:
            if cap.isOpened():
                cap.release()
            db.close()

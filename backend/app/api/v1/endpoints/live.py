import time
import cv2
import numpy as np
from typing import Generator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.app.services.vehicle_detector import VehicleDetector
from backend.app.services.plate_detector import PlateDetector
from backend.app.services.ocr_engine import OCREngine
from backend.app.services.vehicle_tracker import VehicleTracker
from backend.app.services.violation_detector import ViolationDetector
from backend.app.utils.drawing import draw_styled_box, draw_stop_line, draw_hud, COLORS

router = APIRouter()

# Global stream control state
is_streaming = True


def generate_synthetic_traffic_frame(frame_idx: int) -> np.ndarray:
    """Generates an aesthetic animated traffic test frame with moving vehicles

    when no physical webcam is plugged in.
    """
    h, w = 480, 640
    frame = np.ones((h, w, 3), dtype=np.uint8) * 35  # Dark road background

    # Road lanes
    cv2.line(frame, (w // 2, 0), (w // 2, h), (200, 200, 200), 2, lineType=cv2.LINE_AA)
    cv2.line(frame, (100, 0), (100, h), (120, 120, 120), 1)
    cv2.line(frame, (w - 100, 0), (w - 100, h), (120, 120, 120), 1)

    # Simulated Vehicle 1: Car moving down left lane
    v1_y = int((frame_idx * 6) % (h + 120)) - 80
    v1_x = 180
    if -80 < v1_y < h:
        cv2.rectangle(frame, (v1_x, v1_y), (v1_x + 90, v1_y + 130), (180, 100, 30), -1)
        # Windshield
        cv2.rectangle(frame, (v1_x + 10, v1_y + 25), (v1_x + 80, v1_y + 55), (60, 60, 60), -1)
        # License Plate
        cv2.rectangle(frame, (v1_x + 15, v1_y + 105), (v1_x + 75, v1_y + 122), (255, 255, 255), -1)
        cv2.putText(frame, "MH12DE", (v1_x + 18, v1_y + 118), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)

    # Simulated Vehicle 2: Truck moving down right lane
    v2_y = int(((frame_idx * 4) + 180) % (h + 180)) - 120
    v2_x = 370
    if -120 < v2_y < h:
        cv2.rectangle(frame, (v2_x, v2_y), (v2_x + 110, v2_y + 160), (40, 130, 220), -1)
        cv2.rectangle(frame, (v2_x + 20, v2_y + 135), (v2_x + 90, v2_y + 155), (255, 255, 255), -1)
        cv2.putText(frame, "KA03MN", (v2_x + 24, v2_y + 150), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)

    return frame


def frame_generator() -> Generator[bytes, None, None]:
    """Generates MJPEG multipart frame stream with live ANPR inference pipeline."""
    vehicle_detector = VehicleDetector()
    plate_detector = PlateDetector()
    ocr_engine = OCREngine()
    tracker = VehicleTracker(max_stale_frames=20)
    violation_detector = ViolationDetector(stop_line_y_ratio=0.65)

    # Try opening webcam 0
    cap = cv2.VideoCapture(0)
    has_webcam = cap.isOpened()

    frame_idx = 0
    fps_timer = time.time()
    current_fps = 25.0

    try:
        while True:
            frame_idx += 1
            if has_webcam:
                ret, frame = cap.read()
                if not ret or frame is None:
                    frame = generate_synthetic_traffic_frame(frame_idx)
            else:
                frame = generate_synthetic_traffic_frame(frame_idx)

            # Calculate FPS
            if frame_idx % 10 == 0:
                now = time.time()
                elapsed = now - fps_timer
                current_fps = 10.0 / elapsed if elapsed > 0 else 25.0
                fps_timer = now

            # Step 1: Detect Vehicles
            vehicles = vehicle_detector.detect(frame)

            # Step 2: Track Vehicles
            tracked = tracker.update_tracks(vehicles, frame_idx)

            # Step 3: Detect Plates
            plates = plate_detector.detect_plates(frame=frame, vehicle_detections=tracked, save_crops=False)

            # Step 4: OCR (sample every 3rd frame to conserve live stream frame rate)
            if frame_idx % 3 == 0:
                for p in plates:
                    ocr_res = ocr_engine.recognize(p["plate_crop"])
                    p["text"] = ocr_res["normalized_text"]

            # Step 5: Violations
            active_tracks = [d["track"] for d in tracked if "track" in d]
            violations = violation_detector.evaluate_frame(frame, active_tracks, frame_idx)

            # Step 6: Render overlays
            annotated = frame.copy()
            draw_stop_line(annotated, violation_detector.stop_line_y_ratio, is_violated=len(violations) > 0)
            for det in tracked:
                bbox = det["bbox"]
                cname = det["class_name"]
                tid = det.get("tracking_id")
                track = det.get("track")
                label = f"{cname.upper()}"
                if track and track.best_plate:
                    label += f" | {track.best_plate['normalized_text']}"
                draw_styled_box(annotated, bbox, COLORS.get(cname, COLORS["vehicle"]), label=label, track_id=tid)

            annotated = plate_detector.draw_plates(annotated, plates)

            total_v = len(tracker.tracks)
            plates_c = sum(1 for t in tracker.tracks.values() if t.best_plate)
            draw_hud(
                img=annotated,
                fps=current_fps,
                vehicle_count=total_v,
                plate_count=plates_c,
                violation_count=0,
            )

            # Encode frame to JPEG
            ret, buffer = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ret:
                continue

            frame_bytes = buffer.tobytes()
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )

            # Limit rate to ~25 FPS to keep CPU/GPU utilization balanced
            time.sleep(0.04)
    finally:
        if cap.isOpened():
            cap.release()


@router.get("/live/stream", summary="Live ANPR MJPEG Video Feed")
def live_stream():
    """Streams live webcam or simulated traffic camera with real-time bounding boxes and OCR overlay."""
    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )

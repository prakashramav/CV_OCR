import cv2
import numpy as np
import pytest
from pathlib import Path

from backend.app.services.image_preprocessor import ImagePreprocessor
from backend.app.services.ocr_engine import OCREngine
from backend.app.services.vehicle_tracker import VehicleTracker
from backend.app.services.violation_detector import ViolationDetector
from backend.app.utils.indian_states import (
    normalize_plate_text,
    validate_indian_plate,
    INDIAN_STATE_CODES,
)


def create_synthetic_plate_image(text: str = "MH12DE1433") -> np.ndarray:
    """Generates a clean synthetic Indian high-security license plate image for deterministic testing."""
    h, w = 80, 280
    plate = np.ones((h, w, 3), dtype=np.uint8) * 255  # White background

    # Yellow or White plate with black border
    cv2.rectangle(plate, (2, 2), (w - 3, h - 3), (0, 0, 0), 3)

    # Blue IND badge band on the left
    cv2.rectangle(plate, (5, 5), (35, h - 5), (180, 50, 20), -1)
    cv2.putText(plate, "IND", (8, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    # Black registration characters
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.1
    th = 3
    cv2.putText(plate, text, (48, 54), font, font_scale, (10, 10, 10), th, lineType=cv2.LINE_AA)

    return plate


def test_plate_normalization_and_validation():
    # Valid Standard Plates
    assert normalize_plate_text("mh 12 de 1433") == "MH12DE1433"
    assert normalize_plate_text("DL-01-AB-1234") == "DL01AB1234"
    assert normalize_plate_text("  TS 09 UB 5678  ") == "TS09UB5678"

    is_valid, status, state = validate_indian_plate("MH12DE1433")
    assert is_valid is True
    assert status == "VALID_INDIAN"
    assert state == "Maharashtra"

    is_valid, status, state = validate_indian_plate("DL01AB1234")
    assert is_valid is True
    assert state == "Delhi"

    # Valid Bharat (BH) Series
    is_valid, status, state = validate_indian_plate("22BH1234AA")
    assert is_valid is True
    assert status == "VALID_BHARAT_SERIES"

    # Invalid Formats
    is_valid, status, _ = validate_indian_plate("XYZ123")
    assert is_valid is False


def test_image_preprocessor_pipeline():
    test_plate = create_synthetic_plate_image("KA03MN4567")
    preprocessed = ImagePreprocessor.preprocess_pipeline(test_plate)

    assert preprocessed is not None
    assert preprocessed.shape[0] == 90  # Target height
    assert len(preprocessed.shape) == 2  # Grayscale / 2D matrix

    variants = ImagePreprocessor.generate_all_variants(test_plate)
    assert "clahe_enhanced" in variants
    assert "bilateral_denoised" in variants
    assert "adaptive_threshold" in variants

    grid = ImagePreprocessor.create_comparison_grid(test_plate)
    assert grid is not None
    assert len(grid.shape) == 3


def test_ocr_engine_synthetic_recognition():
    test_plate = create_synthetic_plate_image("DL01AB1234")
    ocr = OCREngine()
    result = ocr.recognize(test_plate)

    assert result is not None
    assert "normalized_text" in result
    assert "ocr_confidence" in result
    assert "raw_text" in result
    # Text should contain DL and 1234 or match registration
    assert len(result["normalized_text"]) >= 4


def test_vehicle_tracker_and_duplicate_prevention():
    tracker = VehicleTracker(max_stale_frames=10)

    # Frame 1: Vehicle detected
    det_f1 = [{"bbox": [100, 100, 250, 250], "confidence": 0.9, "class_name": "car"}]
    res_f1 = tracker.update_tracks(det_f1, frame_idx=1)
    assert len(res_f1) == 1
    tid = res_f1[0]["tracking_id"]
    assert tid == 1

    # Frame 2: Vehicle moved slightly
    det_f2 = [{"bbox": [105, 105, 255, 255], "confidence": 0.92, "class_name": "car"}]
    res_f2 = tracker.update_tracks(det_f2, frame_idx=2)
    assert len(res_f2) == 1
    # Tracking ID must remain consistent!
    assert res_f2[0]["tracking_id"] == tid

    # Simulate plate observation
    track = tracker.get_track(tid)
    track.add_plate_observation({
        "normalized_text": "MH12DE1433",
        "ocr_confidence": 0.92,
        "is_valid": True,
        "raw_text": "MH12DE1433",
    })
    assert track.best_plate is not None
    assert track.best_plate["normalized_text"] == "MH12DE1433"


def test_violation_detector_stop_line_crossing():
    vd = ViolationDetector(stop_line_y_ratio=0.5)  # Middle of 400px height = 200px
    tracker = VehicleTracker()

    # Frame 1: Vehicle centroid at (150, 180), which is above stop line y=200
    det_f1 = [{"bbox": [100, 140, 200, 220], "confidence": 0.9, "class_name": "car"}]
    tracked_f1 = tracker.update_tracks(det_f1, frame_idx=1)
    dummy_frame = np.zeros((400, 600, 3), dtype=np.uint8)

    violations_f1 = vd.evaluate_frame(dummy_frame, [d["track"] for d in tracked_f1], frame_idx=1)
    assert len(violations_f1) == 0  # No violation yet

    # Frame 2: Vehicle moves across stop line to centroid (150, 220), which is below stop line y=200
    # Overlapping bounding boxes maintain track association under IoU matching
    det_f2 = [{"bbox": [100, 180, 200, 260], "confidence": 0.9, "class_name": "car"}]
    tracked_f2 = tracker.update_tracks(det_f2, frame_idx=2)

    violations_f2 = vd.evaluate_frame(dummy_frame, [d["track"] for d in tracked_f2], frame_idx=2)
    assert len(violations_f2) == 1
    assert violations_f2[0]["violation_type"] == "STOP_LINE_CROSSING"
    assert violations_f2[0]["tracking_id"] == 1
    assert Path(violations_f2[0]["evidence_image_path"]).name.startswith("evidence_")

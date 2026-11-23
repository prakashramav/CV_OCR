import os
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import cv2
import torch
import numpy as np
from ultralytics import YOLO

from backend.app.config import settings
from backend.app.core.logger import logger
from backend.app.core.exceptions import ModelLoadError
from backend.app.utils.drawing import draw_styled_box, COLORS


class PlateDetector:
    """Dedicated YOLOv8-based License Plate Detection service.

    Localizes license plates within frames or vehicle crops, extracts cropped plate ROIs,
    and saves them for OCR and audit records.
    """

    _instance: Optional["PlateDetector"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_path: Optional[str] = None, conf_threshold: Optional[float] = None):
        if getattr(self, "_initialized", False):
            return

        self.conf_threshold = conf_threshold or settings.PLATE_CONF_THRESHOLD
        self.model_path = model_path or str(settings.MODEL_DIR / "license_plate_detector.pt")

        self.device = "cuda" if torch.cuda.is_available() and settings.PREFERRED_DEVICE == "cuda" else "cpu"
        self.use_half = self.device == "cuda"

        logger.info(f"Initializing PlateDetector on device '{self.device}' with weights: {self.model_path}")
        try:
            self.model = YOLO(self.model_path)
            self.model.to(self.device)
            self._initialized = True
            logger.info("PlateDetector successfully initialized.")
        except Exception as e:
            logger.error(f"Failed to load license plate detector model: {e}")
            raise ModelLoadError(f"License plate detector model loading failed: {e}")

    def detect_plates(
        self,
        frame: np.ndarray,
        vehicle_detections: Optional[List[Dict[str, Any]]] = None,
        conf: Optional[float] = None,
        save_crops: bool = True,
    ) -> List[Dict[str, Any]]:
        """Detects license plates in the frame.

        If `vehicle_detections` are provided, performs hierarchical inference within vehicle ROIs
        to minimize false alarms in urban backgrounds. Otherwise, scans the full frame.

        Returns list of plate dictionaries:
            - bbox: [x1, y1, x2, y2] (full frame coordinates)
            - confidence: float
            - plate_crop: np.ndarray
            - plate_image_path: Optional[str]
            - vehicle_info: Optional[Dict]
        """
        if frame is None or frame.size == 0:
            return []

        active_conf = conf if conf is not None else self.conf_threshold
        plate_records = []

        if vehicle_detections:
            # Hierarchical Detection: search inside each detected vehicle ROI
            for v_det in vehicle_detections:
                vx1, vy1, vx2, vy2 = v_det["bbox"]
                # Bound coordinates within frame dimensions
                h, w = frame.shape[:2]
                vx1, vy1 = max(0, vx1), max(0, vy1)
                vx2, vy2 = min(w, vx2), min(h, vy2)

                if (vx2 - vx1) < 20 or (vy2 - vy1) < 20:
                    continue

                v_crop = frame[vy1:vy2, vx1:vx2]
                v_plates = self._predict_plates_in_crop(v_crop, active_conf)

                for p in v_plates:
                    # Offset crop coordinates back to frame coordinates
                    px1, py1, px2, py2 = p["bbox"]
                    fx1, fy1 = vx1 + px1, vy1 + py1
                    fx2, fy2 = vx1 + px2, vy1 + py2

                    plate_record = self._build_plate_record(
                        frame=frame,
                        bbox=[fx1, fy1, fx2, fy2],
                        confidence=p["confidence"],
                        save_crop=save_crops,
                        vehicle_info=v_det,
                    )
                    if plate_record:
                        plate_records.append(plate_record)
        else:
            # Full Frame Inference
            raw_plates = self._predict_plates_in_crop(frame, active_conf)
            for p in raw_plates:
                plate_record = self._build_plate_record(
                    frame=frame,
                    bbox=p["bbox"],
                    confidence=p["confidence"],
                    save_crop=save_crops,
                    vehicle_info=None,
                )
                if plate_record:
                    plate_records.append(plate_record)

        return plate_records

    def _predict_plates_in_crop(self, crop: np.ndarray, conf: float) -> List[Dict[str, Any]]:
        """Runs model inference on an image region and returns raw bounding boxes."""
        results = self.model.predict(
            source=crop,
            conf=conf,
            device=self.device,
            half=self.use_half,
            verbose=False,
        )

        plates = []
        if not results:
            return plates

        for r in results:
            for box in r.boxes:
                score = float(box.conf[0].item())
                xyxy = box.xyxy[0].cpu().numpy().astype(int).tolist()
                plates.append({"bbox": xyxy, "confidence": round(score, 3)})

        return plates

    def _build_plate_record(
        self,
        frame: np.ndarray,
        bbox: List[int],
        confidence: float,
        save_crop: bool,
        vehicle_info: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """Crops plate region, validates aspect ratio, optionally saves crop image, and returns dictionary."""
        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        pw = x2 - x1
        ph = y2 - y1

        # Reject degenerate boxes or invalid plate dimensions
        if pw < 15 or ph < 8:
            return None

        aspect_ratio = pw / float(ph)
        # Indian license plates generally have aspect ratio between 1.2 (square 2-row) and 6.0 (standard 1-row)
        if aspect_ratio < 1.0 or aspect_ratio > 7.0:
            return None

        # Add modest 3% margin around plate crop for better OCR character edge capture
        mx = int(pw * 0.03)
        my = int(ph * 0.03)
        crop_x1 = max(0, x1 - mx)
        crop_y1 = max(0, y1 - my)
        crop_x2 = min(w, x2 + mx)
        crop_y2 = min(h, y2 + my)

        plate_crop = frame[crop_y1:crop_y2, crop_x1:crop_x2].copy()

        crop_path_str = None
        if save_crop and plate_crop.size > 0:
            filename = f"plate_{uuid.uuid4().hex[:12]}.jpg"
            full_path = settings.PLATES_OUTPUT_DIR / filename
            cv2.imwrite(str(full_path), plate_crop)
            crop_path_str = f"outputs/plates/{filename}"

        return {
            "bbox": [x1, y1, x2, y2],
            "confidence": confidence,
            "plate_crop": plate_crop,
            "plate_image_path": crop_path_str,
            "vehicle_info": vehicle_info,
        }

    def draw_plates(self, frame: np.ndarray, plates: List[Dict[str, Any]]) -> np.ndarray:
        """Renders license plate bounding boxes and confidence on frame."""
        canvas = frame.copy()
        for p in plates:
            bbox = p["bbox"]
            conf = p["confidence"]
            text = p.get("text")
            label = f"PLATE {text}" if text else f"PLATE {conf:.2f}"
            draw_styled_box(canvas, bbox, COLORS["plate"], label=label, thickness=2)
        return canvas

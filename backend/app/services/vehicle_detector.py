import os
from typing import List, Dict, Any, Optional
import torch
import numpy as np
from ultralytics import YOLO

from backend.app.config import settings
from backend.app.core.logger import logger
from backend.app.core.exceptions import ModelLoadError
from backend.app.utils.drawing import draw_styled_box, COLORS

# Ensure Ultralytics local cache avoids restricted system roaming paths
os.environ["YOLO_CONFIG_DIR"] = str(settings.BASE_DIR / ".ultralytics")


class VehicleDetector:
    """YOLOv8-based vehicle detection service.

    Extracts bounding boxes, classes, and confidence scores for cars, motorcycles, buses, and trucks.
    """

    # COCO Class mapping for traffic monitoring
    TARGET_VEHICLE_CLASSES = {
        2: "car",
        3: "motorcycle",
        5: "bus",
        7: "truck",
    }

    _instance: Optional["VehicleDetector"] = None

    def __new__(cls, *args, **kwargs):
        """Singleton pattern to avoid reloading model weights on each invocation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_path: Optional[str] = None, conf_threshold: Optional[float] = None):
        if getattr(self, "_initialized", False):
            return

        self.conf_threshold = conf_threshold or settings.VEHICLE_CONF_THRESHOLD
        self.model_path = model_path or str(settings.MODEL_DIR / "yolov8n.pt")

        # Determine optimal compute device
        self.device = "cuda" if torch.cuda.is_available() and settings.PREFERRED_DEVICE == "cuda" else "cpu"
        self.use_half = self.device == "cuda"

        logger.info(f"Initializing VehicleDetector on device '{self.device}' with weights: {self.model_path}")
        try:
            self.model = YOLO(self.model_path)
            self.model.to(self.device)
            self._initialized = True
            logger.info("VehicleDetector successfully initialized.")
        except Exception as e:
            logger.error(f"Failed to load vehicle detection model: {e}")
            raise ModelLoadError(f"Vehicle detector model loading failed: {e}")

    def detect(self, frame: np.ndarray, conf: Optional[float] = None) -> List[Dict[str, Any]]:
        """Runs vehicle detection on an input BGR image.

        Args:
            frame: OpenCV image matrix (BGR).
            conf: Optional override for confidence threshold.

        Returns:
            List of detected vehicle dictionaries containing bbox, class_name, class_id, confidence.
        """
        if frame is None or frame.size == 0:
            return []

        active_conf = conf if conf is not None else self.conf_threshold

        try:
            results = self.model.predict(
                source=frame,
                conf=active_conf,
                device=self.device,
                half=self.use_half,
                classes=list(self.TARGET_VEHICLE_CLASSES.keys()),
                verbose=False,
            )

            detections = []
            if not results:
                return detections

            for r in results:
                boxes = r.boxes
                for box in boxes:
                    cls_id = int(box.cls[0].item())
                    score = float(box.conf[0].item())
                    xyxy = box.xyxy[0].cpu().numpy().astype(int).tolist()

                    class_name = self.TARGET_VEHICLE_CLASSES.get(cls_id, "vehicle")

                    detections.append({
                        "bbox": xyxy,  # [x1, y1, x2, y2]
                        "confidence": round(score, 3),
                        "class_id": cls_id,
                        "class_name": class_name,
                    })

            return detections
        except Exception as e:
            logger.error(f"Error during vehicle inference: {e}")
            return []

    def draw_detections(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
        """Renders bounding boxes and labels for detected vehicles on the frame."""
        canvas = frame.copy()
        for det in detections:
            bbox = det["bbox"]
            cname = det["class_name"]
            conf = det["confidence"]
            color = COLORS.get(cname, COLORS["vehicle"])
            label = f"{cname.upper()} {conf:.2f}"
            track_id = det.get("tracking_id")
            draw_styled_box(canvas, bbox, color, label=label, track_id=track_id)
        return canvas

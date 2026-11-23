import re
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import torch
import easyocr

from backend.app.config import settings
from backend.app.core.logger import logger
from backend.app.core.exceptions import OCRError
from backend.app.services.image_preprocessor import ImagePreprocessor
from backend.app.utils.indian_states import (
    normalize_plate_text,
    validate_indian_plate,
)


class OCREngine:
    """EasyOCR-based license plate recognition engine customized for Indian registration formats.

    Preserves raw audit text, performs alphanumeric normalization, computes granular confidence scores,
    and validates format compliance against the Motor Vehicles Act.
    """

    # Latin alphanumeric character set valid on vehicle license plates
    ALLOWED_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    _instance: Optional["OCREngine"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, conf_threshold: Optional[float] = None):
        if getattr(self, "_initialized", False):
            return

        self.conf_threshold = conf_threshold or settings.OCR_CONF_THRESHOLD
        self.device = "cuda" if torch.cuda.is_available() and settings.PREFERRED_DEVICE == "cuda" else "cpu"

        model_dir = str(settings.MODEL_DIR / "easyocr" / "model")
        user_network_dir = str(settings.MODEL_DIR / "easyocr" / "user_network")

        logger.info(f"Initializing EasyOCR Engine on device '{self.device}' with model dir: {model_dir}")
        try:
            self.reader = easyocr.Reader(
                ["en"],
                gpu=(self.device == "cuda"),
                model_storage_directory=model_dir,
                user_network_directory=user_network_dir,
                download_enabled=False,
                verbose=False,
            )
            self._initialized = True
            logger.info("EasyOCR Engine initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR Engine: {e}")
            raise OCRError(f"EasyOCR initialization failed: {e}")

    def recognize(self, plate_crop: np.ndarray, multi_pass: bool = True) -> Dict[str, Any]:
        """Performs character recognition on a license plate crop.

        Args:
            plate_crop: BGR image matrix of cropped plate.
            multi_pass: If True, evaluates preprocessed and raw variants to find the highest-confidence valid parse.

        Returns:
            Dictionary containing:
                - raw_text: Unaltered OCR string for audit.
                - normalized_text: Alphanumeric uppercase string.
                - ocr_confidence: float (0.0 to 1.0).
                - is_valid: bool (format compliance).
                - validation_status: str (e.g. VALID_INDIAN).
                - state_name: str (e.g. Maharashtra, Delhi).
                - needs_manual_review: bool.
        """
        if plate_crop is None or plate_crop.size == 0:
            return self._empty_result("EMPTY_IMAGE")

        # Primary pass: Optimized preprocessed pipeline
        try:
            preprocessed = ImagePreprocessor.preprocess_pipeline(plate_crop)
            result = self._ocr_pass(preprocessed)

            # If multi-pass enabled and primary pass is not a valid Indian plate or has low confidence,
            # evaluate alternative representations (raw color and CLAHE) to find the best signal
            if multi_pass and (not result["is_valid"] or result["ocr_confidence"] < self.conf_threshold):
                # Try raw color crop resized
                raw_resized = ImagePreprocessor.resize_for_ocr(plate_crop, target_height=90)
                alt_result = self._ocr_pass(raw_resized)

                if alt_result["is_valid"] or (alt_result["ocr_confidence"] > result["ocr_confidence"]):
                    result = alt_result

            # Determine manual review necessity
            result["needs_manual_review"] = (
                not result["is_valid"] or result["ocr_confidence"] < self.conf_threshold
            )

            return result
        except Exception as e:
            logger.error(f"OCR recognition error: {e}")
            return self._empty_result(f"ERROR: {str(e)}")

    def _ocr_pass(self, img: np.ndarray) -> Dict[str, Any]:
        """Runs EasyOCR text extraction and validates result."""
        raw_outputs = self.reader.readtext(
            img,
            allowlist=self.ALLOWED_CHARS,
            detail=1,
            paragraph=False,
        )

        if not raw_outputs:
            return self._empty_result("NO_TEXT_DETECTED")

        # Combine detected text segments in reading order (top to bottom, left to right)
        # EasyOCR returns: (bbox, text, prob)
        segments = []
        confidences = []

        # Sort by vertical top coordinate first (for 2-row plates), then horizontal
        sorted_outputs = sorted(raw_outputs, key=lambda x: (x[0][0][1], x[0][0][0]))

        for _, text, prob in sorted_outputs:
            cleaned_segment = text.strip()
            if cleaned_segment:
                segments.append(cleaned_segment)
                confidences.append(float(prob))

        if not segments:
            return self._empty_result("NO_CHARACTERS")

        raw_text = " ".join(segments)
        normalized_text = normalize_plate_text(raw_text)
        avg_confidence = round(float(np.mean(confidences)), 3) if confidences else 0.0

        is_valid, validation_status, state_name = validate_indian_plate(normalized_text)

        return {
            "raw_text": raw_text,
            "normalized_text": normalized_text,
            "ocr_confidence": avg_confidence,
            "is_valid": is_valid,
            "validation_status": validation_status,
            "state_name": state_name,
            "needs_manual_review": False,
        }

    def _empty_result(self, status_reason: str) -> Dict[str, Any]:
        """Returns standard structure for empty or unreadable detections."""
        return {
            "raw_text": "",
            "normalized_text": "",
            "ocr_confidence": 0.0,
            "is_valid": False,
            "validation_status": status_reason,
            "state_name": "Unknown",
            "needs_manual_review": True,
        }

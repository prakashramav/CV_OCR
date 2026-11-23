import uuid
from typing import Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, status
import cv2
import numpy as np

from backend.app.config import settings
from backend.app.services.vehicle_detector import VehicleDetector
from backend.app.services.plate_detector import PlateDetector
from backend.app.services.ocr_engine import OCREngine
from backend.app.utils.drawing import COLORS, draw_styled_box

router = APIRouter()


@router.post("/images/analyze", summary="Analyze Single Image Snapshot")
async def analyze_image(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Uploads and analyzes an image snapshot:

    Detects vehicles, identifies license plates, extracts registration text via OCR,
    and returns annotated detection metadata and cropped image paths.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a valid image format (JPEG, PNG, WebP).",
        )

    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not decode image.")

    vehicle_detector = VehicleDetector()
    plate_detector = PlateDetector()
    ocr_engine = OCREngine()

    # Step 1: Detect Vehicles
    vehicles = vehicle_detector.detect(frame)

    # Step 2: Detect License Plates
    plates = plate_detector.detect_plates(frame=frame, vehicle_detections=vehicles, save_crops=True)

    # Step 3: OCR on each plate
    recognized_plates = []
    for p in plates:
        ocr_res = ocr_engine.recognize(p["plate_crop"])
        recognized_plates.append({
            "bbox": p["bbox"],
            "confidence": p["confidence"],
            "plate_image_path": p["plate_image_path"],
            "raw_text": ocr_res["raw_text"],
            "normalized_text": ocr_res["normalized_text"],
            "ocr_confidence": ocr_res["ocr_confidence"],
            "is_valid": ocr_res["is_valid"],
            "validation_status": ocr_res["validation_status"],
            "state_name": ocr_res["state_name"],
            "vehicle_type": p["vehicle_info"]["class_name"] if p.get("vehicle_info") else "unknown",
        })

    # Step 4: Render annotated full image
    annotated = vehicle_detector.draw_detections(frame, vehicles)
    annotated = plate_detector.draw_plates(annotated, plates)

    annotated_filename = f"annotated_{uuid.uuid4().hex[:12]}.jpg"
    annotated_path = settings.OUTPUT_DIR / annotated_filename
    cv2.imwrite(str(annotated_path), annotated)

    return {
        "filename": file.filename,
        "annotated_image_path": f"outputs/{annotated_filename}",
        "total_vehicles": len(vehicles),
        "total_plates": len(recognized_plates),
        "vehicles": vehicles,
        "plates": recognized_plates,
    }

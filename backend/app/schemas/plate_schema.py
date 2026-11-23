from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class LicensePlateBase(BaseModel):
    raw_text: str = Field(..., description="Raw unfiltered text recognized by OCR")
    normalized_text: str = Field(..., description="Normalized alphanumeric license plate string")
    ocr_confidence: float = Field(..., ge=0.0, le=1.0)
    plate_confidence: float = Field(..., ge=0.0, le=1.0)
    validation_status: str = Field(default="INVALID")
    plate_image_path: Optional[str] = None


class LicensePlateCreate(LicensePlateBase):
    vehicle_detection_id: Optional[int] = None


class LicensePlateResponse(LicensePlateBase):
    id: int
    vehicle_detection_id: Optional[int]
    created_at: datetime
    vehicle_type: Optional[str] = None
    tracking_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

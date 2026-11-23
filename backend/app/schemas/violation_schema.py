from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ViolationBase(BaseModel):
    violation_type: str = Field(..., description="Type of violation: STOP_LINE_CROSSING, RESTRICTED_ZONE_ENTRY")
    tracking_id: Optional[int] = None
    evidence_image_path: str = Field(..., description="Relative or absolute path to evidence frame")
    verification_status: str = Field(default="PENDING")


class ViolationCreate(ViolationBase):
    license_plate_id: Optional[int] = None


class ViolationResponse(ViolationBase):
    id: int
    license_plate_id: Optional[int]
    event_timestamp: datetime
    plate_number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

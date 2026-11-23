from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class VehicleDetectionBase(BaseModel):
    vehicle_type: str = Field(..., description="Detected vehicle category: car, motorcycle, bus, truck")
    vehicle_confidence: float = Field(..., ge=0.0, le=1.0)
    source_type: str = Field(default="video")
    source_name: Optional[str] = None
    tracking_id: Optional[int] = None


class VehicleDetectionCreate(VehicleDetectionBase):
    pass


class VehicleDetectionResponse(VehicleDetectionBase):
    id: int
    detected_at: datetime

    model_config = ConfigDict(from_attributes=True)

from typing import Dict, List, Optional
from pydantic import BaseModel


class OverviewMetrics(BaseModel):
    total_vehicles: int
    total_plates: int
    successful_ocr_percentage: float
    total_violations: int
    active_jobs: int


class VehicleTypeCount(BaseModel):
    vehicle_type: str
    count: int


class HourlyActivity(BaseModel):
    hour: str
    detections: int
    violations: int


class AnalyticsOverviewResponse(BaseModel):
    metrics: OverviewMetrics
    vehicle_distribution: List[VehicleTypeCount]
    hourly_trends: List[HourlyActivity]
    confidence_distribution: Dict[str, int]
    recent_violations: List[dict]

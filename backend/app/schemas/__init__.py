from backend.app.schemas.detection_schema import (
    VehicleDetectionCreate,
    VehicleDetectionResponse,
)
from backend.app.schemas.plate_schema import (
    LicensePlateCreate,
    LicensePlateResponse,
)
from backend.app.schemas.violation_schema import (
    ViolationCreate,
    ViolationResponse,
)
from backend.app.schemas.analytics_schema import (
    OverviewMetrics,
    AnalyticsOverviewResponse,
)

__all__ = [
    "VehicleDetectionCreate",
    "VehicleDetectionResponse",
    "LicensePlateCreate",
    "LicensePlateResponse",
    "ViolationCreate",
    "ViolationResponse",
    "OverviewMetrics",
    "AnalyticsOverviewResponse",
]

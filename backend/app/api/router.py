from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    health,
    images,
    videos,
    detections,
    plates,
    violations,
    analytics,
    live,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health & Hardware Telemetry"])
api_router.include_router(images.router, tags=["Image Analysis"])
api_router.include_router(videos.router, tags=["Video Analytics & Ingestion"])
api_router.include_router(detections.router, tags=["Vehicle Detections"])
api_router.include_router(plates.router, tags=["License Plates"])
api_router.include_router(violations.router, tags=["Traffic Violations"])
api_router.include_router(analytics.router, tags=["Analytics & KPIs"])
api_router.include_router(live.router, tags=["Live Webcam Monitoring"])

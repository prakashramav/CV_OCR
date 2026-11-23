import io
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database.init_db import init_db
from backend.tests.test_vision_pipeline import create_synthetic_plate_image

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    init_db()


def test_api_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "compute" in data
    assert "device" in data["compute"]


def test_api_analytics_overview():
    response = client.get("/api/v1/analytics/overview")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "total_vehicles" in data["metrics"]
    assert "vehicle_distribution" in data
    assert "hourly_trends" in data


def test_api_plates_and_detections_empty():
    res_plates = client.get("/api/v1/plates")
    assert res_plates.status_code == 200
    assert "items" in res_plates.json()

    res_dets = client.get("/api/v1/detections")
    assert res_dets.status_code == 200
    assert "items" in res_dets.json()


def test_api_image_analysis():
    # Create test synthetic plate image and encode to JPEG bytes
    img = create_synthetic_plate_image("KA03MN4567")
    _, img_bytes = cv2.imencode(".jpg", img)

    response = client.post(
        "/api/v1/images/analyze",
        files={"file": ("test_plate.jpg", img_bytes.tobytes(), "image/jpeg")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_plates" in data
    assert "annotated_image_path" in data

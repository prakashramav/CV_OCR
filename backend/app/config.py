import os
from pathlib import Path

# Ensure Ultralytics and libraries use local workspace directory for configuration
_BASE_DIR = Path(__file__).resolve().parent.parent
os.environ["YOLO_CONFIG_DIR"] = str(_BASE_DIR / ".ultralytics")

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Powered Automatic Number Plate Recognition System"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Production-Grade Traffic Monitoring, Vehicle Tracking, License Plate Localization & OCR Pipeline"
    API_V1_STR: str = "/api/v1"

    # Server settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True

    # Hardware & Inference settings
    # Default to "cuda" if available, dynamically validated in detector initialization
    PREFERRED_DEVICE: str = "cuda"
    VEHICLE_CONF_THRESHOLD: float = 0.45
    PLATE_CONF_THRESHOLD: float = 0.35
    OCR_CONF_THRESHOLD: float = 0.40

    # Paths resolution
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    ROOT_DIR: Path = BASE_DIR.parent
    MODEL_DIR: Path = ROOT_DIR / "model_weights"
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    OUTPUT_DIR: Path = BASE_DIR / "outputs"
    PLATES_OUTPUT_DIR: Path = OUTPUT_DIR / "plates"
    EVIDENCE_OUTPUT_DIR: Path = OUTPUT_DIR / "evidence"
    VIDEOS_OUTPUT_DIR: Path = OUTPUT_DIR / "videos"

    # Database
    DATABASE_URL: str = "sqlite:///./anpr.db"

    # Traffic Violation Default Thresholds
    VIOLATION_STOP_LINE_Y_RATIO: float = 0.65
    VIOLATION_ZONE_POLYGON: list = []

    # Retention Policy
    DATA_RETENTION_DAYS: int = 30

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()

# Ensure directories exist
for folder in [
    settings.UPLOAD_DIR,
    settings.OUTPUT_DIR,
    settings.PLATES_OUTPUT_DIR,
    settings.EVIDENCE_OUTPUT_DIR,
    settings.VIDEOS_OUTPUT_DIR,
    settings.MODEL_DIR,
]:
    folder.mkdir(parents=True, exist_ok=True)

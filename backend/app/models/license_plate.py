from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database.session import Base


class LicensePlate(Base):
    __tablename__ = "license_plates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vehicle_detection_id = Column(Integer, ForeignKey("vehicle_detections.id", ondelete="CASCADE"), nullable=True)
    raw_text = Column(String(64), nullable=False)               # Unfiltered OCR output
    normalized_text = Column(String(32), index=True, nullable=False) # Normalized alphanumeric text
    ocr_confidence = Column(Float, nullable=False)              # OCR confidence (0.0 to 1.0)
    plate_confidence = Column(Float, nullable=False)            # YOLO detector confidence for plate box
    validation_status = Column(String(32), default="INVALID")    # VALID_INDIAN, SUSPICIOUS, INVALID, MANUAL_REVIEW
    plate_image_path = Column(String(512), nullable=True)       # Cropped plate image file path
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    vehicle_detection = relationship("VehicleDetection", back_populates="license_plates")
    violations = relationship("Violation", back_populates="license_plate")

    def __repr__(self):
        return f"<LicensePlate(id={self.id}, text='{self.normalized_text}', status='{self.validation_status}', conf={self.ocr_confidence:.2f})>"

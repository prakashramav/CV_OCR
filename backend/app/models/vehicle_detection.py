from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from backend.app.database.session import Base


class VehicleDetection(Base):
    __tablename__ = "vehicle_detections"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tracking_id = Column(Integer, index=True, nullable=True)  # Assigned by ByteTrack
    vehicle_type = Column(String(50), nullable=False)        # car, motorcycle, bus, truck
    vehicle_confidence = Column(Float, nullable=False)       # 0.0 to 1.0
    detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    source_type = Column(String(50), default="video")        # video, webcam, image
    source_name = Column(String(255), nullable=True)

    # Relationships
    license_plates = relationship("LicensePlate", back_populates="vehicle_detection", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<VehicleDetection(id={self.id}, track_id={self.tracking_id}, type='{self.vehicle_type}', conf={self.vehicle_confidence:.2f})>"

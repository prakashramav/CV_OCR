from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database.session import Base


class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    license_plate_id = Column(Integer, ForeignKey("license_plates.id", ondelete="SET NULL"), nullable=True)
    tracking_id = Column(Integer, index=True, nullable=True)
    violation_type = Column(String(64), nullable=False)         # STOP_LINE_CROSSING, RESTRICTED_ZONE_ENTRY
    event_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    evidence_image_path = Column(String(512), nullable=False)   # Full evidence frame with overlaid bounding boxes
    verification_status = Column(String(32), default="PENDING") # PENDING, CONFIRMED, DISMISSED

    # Relationships
    license_plate = relationship("LicensePlate", back_populates="violations")

    def __repr__(self):
        return f"<Violation(id={self.id}, type='{self.violation_type}', track_id={self.tracking_id}, status='{self.verification_status}')>"

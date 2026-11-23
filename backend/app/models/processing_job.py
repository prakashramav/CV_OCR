from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime
from backend.app.database.session import Base


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(String(64), primary_key=True, index=True)       # UUID string
    filename = Column(String(255), nullable=False)
    status = Column(String(32), default="QUEUED", index=True)   # QUEUED, PROCESSING, COMPLETED, FAILED
    total_frames = Column(Integer, default=0)
    processed_frames = Column(Integer, default=0)
    total_vehicles = Column(Integer, default=0)
    total_plates = Column(Integer, default=0)
    output_video_path = Column(String(512), nullable=True)
    error_message = Column(String(512), nullable=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    @property
    def progress_percentage(self) -> float:
        if self.total_frames == 0:
            return 0.0
        return round((self.processed_frames / self.total_frames) * 100.0, 1)

    def __repr__(self):
        return f"<ProcessingJob(id='{self.id}', filename='{self.filename}', status='{self.status}', progress={self.progress_percentage}%)>"

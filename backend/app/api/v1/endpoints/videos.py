import uuid
import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database.session import get_db
from backend.app.models.processing_job import ProcessingJob
from backend.app.services.video_processor import VideoProcessor

router = APIRouter()
video_processor = VideoProcessor()


@router.post("/videos/upload", summary="Upload Traffic Video for Processing")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    auto_process: bool = True,
    db: Session = Depends(get_db),
):
    """Uploads an MP4/AVI/MOV traffic video and optionally kicks off asynchronous background processing."""
    ext = Path(file.filename).suffix.lower()
    if ext not in [".mp4", ".avi", ".mov", ".mkv"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid video format. Supported formats: .mp4, .avi, .mov, .mkv",
        )

    job_id = str(uuid.uuid4())
    stored_filename = f"{job_id}{ext}"
    destination_path = settings.UPLOAD_DIR / stored_filename

    with open(destination_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Initialize Job Record
    job = ProcessingJob(
        id=job_id,
        filename=file.filename,
        status="QUEUED",
    )
    db.add(job)
    db.commit()

    if auto_process:
        background_tasks.add_task(
            video_processor.process_video_sync,
            job_id=job_id,
            input_video_path=str(destination_path),
        )

    return {
        "job_id": job_id,
        "filename": file.filename,
        "status": "QUEUED" if auto_process else "UPLOADED",
        "message": "Video successfully uploaded and queued for processing.",
    }


@router.post("/videos/{job_id}/process", summary="Manually Trigger Video Processing")
def start_processing(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    if job.status in ["PROCESSING", "COMPLETED"]:
        return {"job_id": job_id, "status": job.status, "message": f"Job is already {job.status}."}

    # Find matching file in uploads
    matches = list(settings.UPLOAD_DIR.glob(f"{job_id}.*"))
    if not matches:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video source file missing.")

    background_tasks.add_task(
        video_processor.process_video_sync,
        job_id=job_id,
        input_video_path=str(matches[0]),
    )

    job.status = "QUEUED"
    db.commit()

    return {"job_id": job_id, "status": "QUEUED", "message": "Background processing triggered."}


@router.get("/videos/{job_id}/status", summary="Poll Video Processing Job Status")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    return {
        "job_id": job.id,
        "filename": job.filename,
        "status": job.status,
        "progress_percentage": job.progress_percentage,
        "processed_frames": job.processed_frames,
        "total_frames": job.total_frames,
        "total_vehicles": job.total_vehicles,
        "total_plates": job.total_plates,
        "output_video_path": job.output_video_path,
        "error_message": job.error_message,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
    }


@router.get("/videos/{job_id}/results", summary="Get Detections from Processed Video")
def get_job_results(job_id: str, db: Session = Depends(get_db)):
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    detections = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    return {
        "job_id": job_id,
        "status": job.status,
        "output_video_path": job.output_video_path,
        "metrics": {
            "total_vehicles": job.total_vehicles,
            "total_plates": job.total_plates,
            "processed_frames": job.processed_frames,
        },
    }

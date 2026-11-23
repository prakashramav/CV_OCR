import torch
import psutil
from fastapi import APIRouter
from backend.app.config import settings

router = APIRouter()


@router.get("/health", summary="System Health and Compute Telemetry")
def get_health():
    """Returns server runtime status, CPU/RAM utilization, and CUDA accelerator status."""
    cuda_available = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if cuda_available else "CPU (Host fallback)"
    vram_allocated_mb = round(torch.cuda.memory_allocated(0) / (1024 * 1024), 1) if cuda_available else 0.0

    return {
        "status": "HEALTHY",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "compute": {
            "device": "cuda" if cuda_available else "cpu",
            "device_name": device_name,
            "cuda_available": cuda_available,
            "vram_allocated_mb": vram_allocated_mb,
            "cpu_percent": psutil.cpu_percent(),
            "ram_percent": psutil.virtual_memory().percent,
        },
    }

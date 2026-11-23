"""Automatic Model Weights Downloader for ANPR System.

Downloads:
1. Ultralytics YOLOv8n (Vehicle Detector)
2. Dedicated YOLOv8 License Plate Detector
3. EasyOCR CRAFT & CRNN Text Recognition Models
"""

import os
import sys
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT_DIR / "model_weights"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def download_all_weights():
    print("=" * 60)
    print("Downloading AI Models for ANPR System...")
    print("=" * 60)

    # 1. Download YOLOv8n vehicle detector
    yolo_vehicle_dest = MODEL_DIR / "yolov8n.pt"
    if not yolo_vehicle_dest.exists():
        print("\n[1/3] Downloading YOLOv8n vehicle detection model...")
        from ultralytics import YOLO
        model = YOLO("yolov8n.pt")
        # Ultralytics downloads to current directory, move to model_weights
        if Path("yolov8n.pt").exists():
            shutil.move("yolov8n.pt", str(yolo_vehicle_dest))
        print(f"Vehicle detector saved to: {yolo_vehicle_dest}")
    else:
        print(f"\n[1/3] YOLOv8n already exists at: {yolo_vehicle_dest}")

    # 2. Download Dedicated License Plate Model
    plate_dest = MODEL_DIR / "license_plate_detector.pt"
    if not plate_dest.exists():
        print("\n[2/3] Downloading dedicated license plate detector from HuggingFace...")
        try:
            from huggingface_hub import hf_hub_download
            downloaded = hf_hub_download(
                repo_id="FarAwayFer/yolov8n_license_plate_recognition",
                filename="best_yolov8n.pt",
            )
            shutil.copy(downloaded, str(plate_dest))
            print(f"Dedicated plate model saved to: {plate_dest}")
        except Exception as e:
            print(f"Warning: Could not fetch from HuggingFace ({e}).")
    else:
        print(f"\n[2/3] License plate model already exists at: {plate_dest}")

    # 3. Download EasyOCR recognition weights
    easyocr_model_dir = MODEL_DIR / "easyocr" / "model"
    easyocr_model_dir.mkdir(parents=True, exist_ok=True)
    craft_file = easyocr_model_dir / "craft_mlt_25k.pth"
    english_file = easyocr_model_dir / "english_g2.pth"

    if not craft_file.exists() or not english_file.exists():
        print("\n[3/3] Initializing and caching EasyOCR models...")
        import easyocr
        easyocr.Reader(
            ["en"],
            gpu=False,
            model_storage_directory=str(easyocr_model_dir),
            download_enabled=True,
            verbose=True,
        )
        print(f"EasyOCR models cached in: {easyocr_model_dir}")
    else:
        print(f"\n[3/3] EasyOCR models already present in: {easyocr_model_dir}")

    print("\n" + "=" * 60)
    print("All AI Model Weights Verified Successfully!")
    print("=" * 60)


if __name__ == "__main__":
    download_all_weights()

import json
import os
import cv2
import numpy as np
from pathlib import Path

# Add project root to path
import sys
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.tests.test_vision_pipeline import create_synthetic_plate_image

GROUND_TRUTH_SAMPLES = [
    {
        "filename": "sample_01_MH12DE1433.jpg",
        "ground_truth_text": "MH12DE1433",
        "state": "Maharashtra",
        "vehicle_type": "car",
        "plate_bbox": [15, 10, 265, 70],
    },
    {
        "filename": "sample_02_DL01AB1234.jpg",
        "ground_truth_text": "DL01AB1234",
        "state": "Delhi",
        "vehicle_type": "car",
        "plate_bbox": [15, 10, 265, 70],
    },
    {
        "filename": "sample_03_KA03MN4567.jpg",
        "ground_truth_text": "KA03MN4567",
        "state": "Karnataka",
        "vehicle_type": "motorcycle",
        "plate_bbox": [15, 10, 265, 70],
    },
    {
        "filename": "sample_04_TS09UB5678.jpg",
        "ground_truth_text": "TS09UB5678",
        "state": "Telangana",
        "vehicle_type": "bus",
        "plate_bbox": [15, 10, 265, 70],
    },
    {
        "filename": "sample_05_22BH1234AA.jpg",
        "ground_truth_text": "22BH1234AA",
        "state": "Bharat Series",
        "vehicle_type": "car",
        "plate_bbox": [15, 10, 265, 70],
    },
    {
        "filename": "sample_06_GJ01XY9876.jpg",
        "ground_truth_text": "GJ01XY9876",
        "state": "Gujarat",
        "vehicle_type": "car",
        "plate_bbox": [15, 10, 265, 70],
    },
    {
        "filename": "sample_07_UP16BZ3344.jpg",
        "ground_truth_text": "UP16BZ3344",
        "state": "Uttar Pradesh",
        "vehicle_type": "truck",
        "plate_bbox": [15, 10, 265, 70],
    },
    {
        "filename": "sample_08_TN02AQ5566.jpg",
        "ground_truth_text": "TN02AQ5566",
        "state": "Tamil Nadu",
        "vehicle_type": "bus",
        "plate_bbox": [15, 10, 265, 70],
    },
]


def generate_benchmark_dataset():
    sample_dir = ROOT_DIR / "datasets" / "sample_plates"
    gt_dir = ROOT_DIR / "datasets" / "ground_truth"
    sample_dir.mkdir(parents=True, exist_ok=True)
    gt_dir.mkdir(parents=True, exist_ok=True)

    manifest = []
    print("Generating ground-truth test dataset...")

    for item in GROUND_TRUTH_SAMPLES:
        text = item["ground_truth_text"]
        img = create_synthetic_plate_image(text)

        img_path = sample_dir / item["filename"]
        cv2.imwrite(str(img_path), img)

        manifest.append({
            "image_path": str(img_path.relative_to(ROOT_DIR)).replace("\\", "/"),
            "filename": item["filename"],
            "ground_truth_text": text,
            "vehicle_type": item["vehicle_type"],
            "state": item["state"],
            "plate_bbox": item["plate_bbox"],
            "image_width": img.shape[1],
            "image_height": img.shape[0],
        })

    gt_file = gt_dir / "annotations.json"
    with open(gt_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated {len(manifest)} annotated ground-truth test samples at {gt_file}!")


if __name__ == "__main__":
    generate_benchmark_dataset()

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple
import cv2
import numpy as np

# Add project root to path
import sys
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.services.plate_detector import PlateDetector
from backend.app.services.ocr_engine import OCREngine
from backend.app.services.vehicle_tracker import VehicleTracker


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculates minimal character edit operations (insertions, deletions, substitutions)."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def run_benchmark():
    annotations_path = ROOT_DIR / "datasets" / "ground_truth" / "annotations.json"
    if not annotations_path.exists():
        print(f"Annotations not found at {annotations_path}. Run generate_dataset.py first.")
        return

    with open(annotations_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    print(f"Starting Model Evaluation Benchmark on {len(samples)} Ground-Truth Samples...")
    plate_detector = PlateDetector()
    ocr_engine = OCREngine()

    results = []
    latencies = []
    exact_matches = 0
    total_cer = 0.0
    tp_plate = 0
    fp_plate = 0
    fn_plate = 0
    ious = []

    confusion_pairs = {}

    for item in samples:
        img_rel_path = item["image_path"]
        img_full_path = ROOT_DIR / img_rel_path
        gt_text = item["ground_truth_text"]
        gt_bbox = item["plate_bbox"]

        frame = cv2.imread(str(img_full_path))
        if frame is None:
            continue

        start_t = time.perf_counter()

        # Step 1: Plate Detection
        detected_plates = plate_detector.detect_plates(frame=frame, save_crops=False)

        # Step 2: OCR Recognition
        if detected_plates:
            best_det = detected_plates[0]
            pred_bbox = best_det["bbox"]
            iou = VehicleTracker.compute_iou(pred_bbox, gt_bbox)
            ious.append(iou)

            if iou >= 0.50:
                tp_plate += 1
            else:
                fp_plate += 1

            ocr_res = ocr_engine.recognize(best_det["plate_crop"])
            pred_text = ocr_res["normalized_text"]
            ocr_conf = ocr_res["ocr_confidence"]
            val_status = ocr_res["validation_status"]
        else:
            fn_plate += 1
            pred_bbox = []
            iou = 0.0
            pred_text = ""
            ocr_conf = 0.0
            val_status = "NOT_DETECTED"

        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        latencies.append(elapsed_ms)

        # CER Calculation
        edit_dist = levenshtein_distance(gt_text, pred_text)
        cer = edit_dist / float(max(len(gt_text), 1))
        total_cer += cer

        is_exact = (pred_text == gt_text)
        if is_exact:
            exact_matches += 1
        else:
            # Track character confusion
            for g_char, p_char in zip(gt_text, pred_text):
                if g_char != p_char:
                    pair = f"{g_char}->{p_char}"
                    confusion_pairs[pair] = confusion_pairs.get(pair, 0) + 1

        results.append({
            "filename": item["filename"],
            "ground_truth": gt_text,
            "predicted": pred_text,
            "exact_match": is_exact,
            "edit_distance": edit_dist,
            "cer": round(cer, 3),
            "iou": round(iou, 3),
            "ocr_confidence": ocr_conf,
            "validation_status": val_status,
            "latency_ms": round(elapsed_ms, 1),
        })

    # Summary Metrics
    n = len(samples)
    precision_plate = tp_plate / float(tp_plate + fp_plate) if (tp_plate + fp_plate) > 0 else 0.0
    recall_plate = tp_plate / float(tp_plate + fn_plate) if (tp_plate + fn_plate) > 0 else 0.0
    f1_plate = 2 * (precision_plate * recall_plate) / (precision_plate + recall_plate) if (precision_plate + recall_plate) > 0 else 0.0

    mean_iou = float(np.mean(ious)) if ious else 0.0
    mean_cer = float(total_cer / n) if n > 0 else 0.0
    exact_accuracy = (exact_matches / float(n)) * 100.0 if n > 0 else 0.0
    mean_latency = float(np.mean(latencies)) if latencies else 0.0
    fps = 1000.0 / mean_latency if mean_latency > 0 else 0.0

    summary = {
        "total_samples": n,
        "exact_match_accuracy_percent": round(exact_accuracy, 1),
        "mean_character_error_rate_cer": round(mean_cer, 4),
        "plate_detection_precision": round(precision_plate, 3),
        "plate_detection_recall": round(recall_plate, 3),
        "plate_detection_f1": round(f1_plate, 3),
        "mean_iou": round(mean_iou, 3),
        "mean_pipeline_latency_ms": round(mean_latency, 1),
        "pipeline_fps": round(fps, 1),
        "character_confusion_pairs": confusion_pairs,
        "detailed_results": results,
    }

    out_file = ROOT_DIR / "evaluation" / "sample_results" / "benchmark_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n================== BENCHMARK SUMMARY ==================")
    print(f"Total Ground-Truth Samples: {n}")
    print(f"Plate Detection Precision:  {precision_plate:.3f} | Recall: {recall_plate:.3f} | F1: {f1_plate:.3f}")
    print(f"Mean Detection IoU:         {mean_iou:.3f}")
    print(f"Exact Plate Match Accuracy: {exact_accuracy:.1f}%")
    print(f"Mean Character Error Rate:  {mean_cer:.4f}")
    print(f"Mean Latency per Frame:     {mean_latency:.1f} ms (~{fps:.1f} FPS)")
    print(f"Saved complete benchmark results to: {out_file}\n")


if __name__ == "__main__":
    run_benchmark()

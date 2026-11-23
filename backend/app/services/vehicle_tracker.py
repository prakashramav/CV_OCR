from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Any
import numpy as np

from backend.app.core.logger import logger


class VehicleTrack:
    """Represents the temporal state and historical observations of a single tracked vehicle."""

    def __init__(self, track_id: int, vehicle_type: str, initial_bbox: List[int], frame_idx: int):
        self.track_id: int = track_id
        self.vehicle_type: str = vehicle_type
        self.current_bbox: List[int] = initial_bbox
        self.trajectory: List[Tuple[int, int]] = [self._calculate_centroid(initial_bbox)]

        self.first_seen_frame: int = frame_idx
        self.last_seen_frame: int = frame_idx
        self.first_seen_time: datetime = datetime.now(timezone.utc)
        self.last_seen_time: datetime = datetime.now(timezone.utc)

        # Plate recognition voting pool
        self.plate_candidates: List[Dict[str, Any]] = []
        self.best_plate: Optional[Dict[str, Any]] = None

        # State flags
        self.is_persisted_in_db: bool = False
        self.db_vehicle_id: Optional[int] = None
        self.violation_triggered: bool = False

    @staticmethod
    def _calculate_centroid(bbox: List[int]) -> Tuple[int, int]:
        x1, y1, x2, y2 = bbox
        return int((x1 + x2) / 2), int((y1 + y2) / 2)

    def update(self, bbox: List[int], frame_idx: int, vehicle_type: Optional[str] = None):
        """Updates vehicle position and temporal timestamps."""
        self.current_bbox = bbox
        self.trajectory.append(self._calculate_centroid(bbox))
        self.last_seen_frame = frame_idx
        self.last_seen_time = datetime.now(timezone.utc)
        if vehicle_type:
            self.vehicle_type = vehicle_type

    def add_plate_observation(self, plate_result: Dict[str, Any]):
        """Adds a license plate detection to this vehicle's temporal voting pool

        and dynamically selects the highest-quality candidate.
        """
        text = plate_result.get("normalized_text", "").strip()
        if not text:
            return

        self.plate_candidates.append(plate_result)

        # Candidate ranking score:
        # Heavily reward format validity (+10.0), then sort by OCR confidence * plate detection confidence
        def score_candidate(cand: Dict[str, Any]) -> float:
            base_score = cand.get("ocr_confidence", 0.0) * cand.get("plate_confidence", 0.5)
            if cand.get("is_valid", False):
                base_score += 10.0
            return base_score

        best = max(self.plate_candidates, key=score_candidate)
        self.best_plate = best

    @property
    def current_centroid(self) -> Tuple[int, int]:
        return self.trajectory[-1]

    @property
    def previous_centroid(self) -> Optional[Tuple[int, int]]:
        if len(self.trajectory) >= 2:
            return self.trajectory[-2]
        return None


class VehicleTracker:
    """Multi-object vehicle tracker and temporal identity registry.

    Maintains vehicle lifetimes, associates license plates, and prevents duplicate records.
    """

    def __init__(self, max_stale_frames: int = 30, iou_threshold: float = 0.25):
        self.tracks: Dict[int, VehicleTrack] = {}
        self.next_track_id: int = 1
        self.max_stale_frames: int = max_stale_frames
        self.iou_threshold: float = iou_threshold

    @staticmethod
    def compute_iou(boxA: List[int], boxB: List[int]) -> float:
        """Calculates Intersection-over-Union (IoU) between two bounding boxes."""
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        interArea = max(0, xB - xA) * max(0, yB - yA)
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

        denominator = float(boxAArea + boxBArea - interArea)
        if denominator <= 0:
            return 0.0
        return interArea / denominator

    def update_tracks(
        self,
        detections: List[Dict[str, Any]],
        frame_idx: int,
    ) -> List[Dict[str, Any]]:
        """Associates incoming detections with existing tracks via IoU matching or creates new tracks.

        Returns list of updated detection dictionaries populated with persistent `tracking_id`.
        """
        updated_detections = []

        # If detections have upstream ByteTrack IDs from YOLO
        has_upstream_ids = any("tracking_id" in d and d["tracking_id"] is not None for d in detections)

        if has_upstream_ids:
            for det in detections:
                tid = det["tracking_id"]
                if tid in self.tracks:
                    self.tracks[tid].update(det["bbox"], frame_idx, det.get("class_name"))
                else:
                    self.tracks[tid] = VehicleTrack(tid, det.get("class_name", "vehicle"), det["bbox"], frame_idx)
                det["track"] = self.tracks[tid]
                updated_detections.append(det)
        else:
            # Fallback IoU Association Tracker
            unmatched_dets = list(range(len(detections)))
            active_track_ids = [
                tid for tid, track in self.tracks.items()
                if (frame_idx - track.last_seen_frame) <= self.max_stale_frames
            ]

            # Greedy IoU matching
            matched_pairs = []
            for d_idx in unmatched_dets:
                best_iou = 0.0
                best_tid = None
                det_box = detections[d_idx]["bbox"]

                for tid in active_track_ids:
                    track_box = self.tracks[tid].current_bbox
                    iou = self.compute_iou(det_box, track_box)
                    if iou > self.iou_threshold and iou > best_iou:
                        best_iou = iou
                        best_tid = tid

                if best_tid is not None:
                    matched_pairs.append((d_idx, best_tid))

            # Apply matches
            used_dets = set()
            used_tracks = set()
            for d_idx, tid in matched_pairs:
                if d_idx not in used_dets and tid not in used_tracks:
                    used_dets.add(d_idx)
                    used_tracks.add(tid)
                    det = detections[d_idx]
                    det["tracking_id"] = tid
                    self.tracks[tid].update(det["bbox"], frame_idx, det.get("class_name"))
                    det["track"] = self.tracks[tid]
                    updated_detections.append(det)

            # Create new tracks for unmatched detections
            for d_idx in unmatched_dets:
                if d_idx not in used_dets:
                    det = detections[d_idx]
                    tid = self.next_track_id
                    self.next_track_id += 1
                    det["tracking_id"] = tid
                    new_track = VehicleTrack(tid, det.get("class_name", "vehicle"), det["bbox"], frame_idx)
                    self.tracks[tid] = new_track
                    det["track"] = new_track
                    updated_detections.append(det)

        # Cleanup stale tracks older than max_stale_frames
        self._purge_stale_tracks(frame_idx)

        return updated_detections

    def _purge_stale_tracks(self, current_frame_idx: int):
        """Removes tracks that have exited the field of view beyond max_stale_frames threshold."""
        stale_ids = [
            tid for tid, track in self.tracks.items()
            if (current_frame_idx - track.last_seen_frame) > (self.max_stale_frames * 3)
        ]
        for tid in stale_ids:
            del self.tracks[tid]

    def get_track(self, track_id: int) -> Optional[VehicleTrack]:
        return self.tracks.get(track_id)

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import cv2
import numpy as np

from backend.app.config import settings
from backend.app.core.logger import logger
from backend.app.services.vehicle_tracker import VehicleTrack
from backend.app.utils.drawing import draw_styled_box, draw_stop_line, COLORS


class ViolationDetector:
    """Configurable Traffic Violation Detection Service.

    Monitors vehicle trajectory vectors against designated virtual stop lines or restricted zones.
    Captures indisputable visual evidence frames with full metadata overlay upon violation trigger.

    Scientific & Engineering Limitations:
    1. Speed Estimation: Not inferred in this module because accurate speed measurement requires
       rigorous geometric camera calibration (focal length, sensor pitch, height, tilt angle),
       a homography ground-plane perspective transform, and metric distance reference markers.
    2. Red-Light Violations: A stop-line crossing constitutes a red-light infraction only when
       synchronized with an authenticated traffic signal state classifier. In the absence of a
       calibrated signal input, events are strictly recorded as 'STOP_LINE_CROSSING'.
    """

    def __init__(
        self,
        stop_line_y_ratio: Optional[float] = None,
        zone_polygon: Optional[List[Tuple[int, int]]] = None,
    ):
        self.stop_line_y_ratio: float = stop_line_y_ratio or settings.VIOLATION_STOP_LINE_Y_RATIO
        self.zone_polygon: Optional[List[Tuple[int, int]]] = zone_polygon
        logger.info(f"ViolationDetector initialized with stop line Y-ratio: {self.stop_line_y_ratio:.2f}")

    def evaluate_frame(
        self,
        frame: np.ndarray,
        tracks: List[VehicleTrack],
        frame_idx: int,
    ) -> List[Dict[str, Any]]:
        """Evaluates all tracked vehicles in the current frame for crossing violations.

        Returns list of newly triggered violation events with evidence frame snapshots.
        """
        if frame is None or not tracks:
            return []

        h, w = frame.shape[:2]
        stop_line_y = int(h * self.stop_line_y_ratio)
        violations = []

        for track in tracks:
            # Check if this track was already cited for a violation to avoid duplicate fines
            if track.violation_triggered:
                continue

            curr_centroid = track.current_centroid
            prev_centroid = track.previous_centroid

            if prev_centroid is None:
                continue

            # Directional Crossing Condition: Moving downwards in camera FOV across stop line
            # prev_y <= stop_line_y and curr_y > stop_line_y
            has_crossed_stop_line = (
                prev_centroid[1] <= stop_line_y and curr_centroid[1] > stop_line_y
            )

            # Optional polygon restricted zone inclusion test
            in_restricted_zone = False
            if self.zone_polygon and len(self.zone_polygon) >= 3:
                poly = np.array(self.zone_polygon, dtype=np.int32)
                dist = cv2.pointPolygonTest(poly, (float(curr_centroid[0]), float(curr_centroid[1])), False)
                if dist >= 0:
                    in_restricted_zone = True

            if has_crossed_stop_line or in_restricted_zone:
                track.violation_triggered = True
                violation_type = "RESTRICTED_ZONE_ENTRY" if in_restricted_zone else "STOP_LINE_CROSSING"

                # Capture and generate full visual evidence frame
                evidence_path = self._generate_evidence_frame(
                    frame=frame,
                    violating_track=track,
                    violation_type=violation_type,
                    stop_line_y_ratio=self.stop_line_y_ratio,
                )

                best_plate_info = track.best_plate or {}
                plate_text = best_plate_info.get("normalized_text", "UNKNOWN")

                violation_event = {
                    "violation_type": violation_type,
                    "tracking_id": track.track_id,
                    "vehicle_type": track.vehicle_type,
                    "plate_number": plate_text,
                    "plate_candidate": best_plate_info,
                    "event_timestamp": datetime.now(timezone.utc),
                    "evidence_image_path": evidence_path,
                    "verification_status": "PENDING",
                }

                logger.warning(
                    f"Traffic Violation Detected! Type: {violation_type} | Vehicle ID: {track.track_id} | Plate: {plate_text}"
                )
                violations.append(violation_event)

        return violations

    def _generate_evidence_frame(
        self,
        frame: np.ndarray,
        violating_track: VehicleTrack,
        violation_type: str,
        stop_line_y_ratio: float,
    ) -> str:
        """Renders an evidence snapshot with highlighted violation annotations and saves to disk."""
        evidence = frame.copy()
        h, w = evidence.shape[:2]

        # Draw red alert stop line
        draw_stop_line(evidence, stop_line_y_ratio, is_violated=True)

        # Highlight violating vehicle in Crimson Red
        bbox = violating_track.current_bbox
        label = f"VIOLATION: {violating_track.vehicle_type.upper()}"
        draw_styled_box(evidence, bbox, COLORS["violation"], label=label, track_id=violating_track.track_id, thickness=3)

        # Overlay evidentiary metadata card in upper corner
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        plate_str = violating_track.best_plate.get("normalized_text", "UNRESOLVED") if violating_track.best_plate else "UNRESOLVED"

        overlay = evidence.copy()
        cv2.rectangle(overlay, (10, 10), (420, 115), (10, 10, 15), -1)
        cv2.addWeighted(overlay, 0.82, evidence, 0.18, 0, evidence)
        cv2.rectangle(evidence, (10, 10), (420, 115), COLORS["violation"], 1)

        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(evidence, f"EVIDENCE LOG: {violation_type}", (20, 32), font, 0.52, COLORS["violation"], 2, lineType=cv2.LINE_AA)
        cv2.putText(evidence, f"TIMESTAMP: {now_str}", (20, 56), font, 0.45, COLORS["white"], 1, lineType=cv2.LINE_AA)
        cv2.putText(evidence, f"TRACK ID: #{violating_track.track_id} ({violating_track.vehicle_type})", (20, 78), font, 0.45, COLORS["white"], 1, lineType=cv2.LINE_AA)
        cv2.putText(evidence, f"PLATE REF: {plate_str}", (20, 100), font, 0.48, COLORS["plate"], 1, lineType=cv2.LINE_AA)

        # Save image
        evidence_filename = f"evidence_{uuid.uuid4().hex[:12]}.jpg"
        save_path = settings.EVIDENCE_OUTPUT_DIR / evidence_filename
        cv2.imwrite(str(save_path), evidence)

        return f"outputs/evidence/{evidence_filename}"

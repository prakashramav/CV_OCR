import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict, Any

# Aesthetic color palette (BGR format for OpenCV)
COLORS = {
    "car": (240, 150, 40),        # Deep Blue/Cyan
    "motorcycle": (80, 200, 120), # Emerald Green
    "bus": (200, 100, 255),       # Lavender
    "truck": (50, 140, 255),      # Amber
    "vehicle": (200, 180, 50),    # Teal
    "plate": (0, 215, 255),       # Gold
    "violation": (40, 40, 240),   # Crimson Red
    "safe_line": (0, 220, 100),   # Neon Green
    "text_bg": (20, 20, 20),      # Charcoal
    "white": (255, 255, 255),
}


def draw_styled_box(
    img: np.ndarray,
    box: Tuple[int, int, int, int],
    color: Tuple[int, int, int],
    label: Optional[str] = None,
    track_id: Optional[int] = None,
    corner_length: int = 15,
    thickness: int = 2,
) -> np.ndarray:
    """Draws a modern corner-accented bounding box with a high-contrast label tag."""
    x1, y1, x2, y2 = [int(v) for v in box]

    # Draw semi-transparent fill or main rectangle
    cv2.rectangle(img, (x1, y1), (x2, y2), color, 1, lineType=cv2.LINE_AA)

    # Draw solid accent corners for modern aesthetic
    cl = min(corner_length, (x2 - x1) // 3, (y2 - y1) // 3)
    # Top-left
    cv2.line(img, (x1, y1), (x1 + cl, y1), color, thickness, lineType=cv2.LINE_AA)
    cv2.line(img, (x1, y1), (x1, y1 + cl), color, thickness, lineType=cv2.LINE_AA)
    # Top-right
    cv2.line(img, (x2, y1), (x2 - cl, y1), color, thickness, lineType=cv2.LINE_AA)
    cv2.line(img, (x2, y1), (x2, y1 + cl), color, thickness, lineType=cv2.LINE_AA)
    # Bottom-left
    cv2.line(img, (x1, y2), (x1 + cl, y2), color, thickness, lineType=cv2.LINE_AA)
    cv2.line(img, (x1, y2), (x1, y2 - cl), color, thickness, lineType=cv2.LINE_AA)
    # Bottom-right
    cv2.line(img, (x2, y2), (x2 - cl, y2), color, thickness, lineType=cv2.LINE_AA)
    cv2.line(img, (x2, y2), (x2, y2 - cl), color, thickness, lineType=cv2.LINE_AA)

    # Format label tag
    if label or track_id is not None:
        tag = ""
        if track_id is not None:
            tag += f"ID:{track_id} "
        if label:
            tag += label

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        font_thickness = 1
        (tw, th), baseline = cv2.getTextSize(tag, font, font_scale, font_thickness)

        tag_y1 = max(0, y1 - th - 8)
        tag_y2 = y1
        tag_x2 = x1 + tw + 10

        # Background tag rectangle
        cv2.rectangle(img, (x1, tag_y1), (tag_x2, tag_y2), color, -1)
        cv2.putText(
            img,
            tag,
            (x1 + 5, y1 - 4),
            font,
            font_scale,
            COLORS["white"],
            font_thickness,
            lineType=cv2.LINE_AA,
        )

    return img


def draw_stop_line(
    img: np.ndarray,
    y_ratio: float,
    is_violated: bool = False,
    label: str = "RESTRICTED STOP LINE",
) -> np.ndarray:
    """Draws a monitored virtual stop line across the frame."""
    h, w = img.shape[:2]
    y = int(h * y_ratio)
    color = COLORS["violation"] if is_violated else COLORS["safe_line"]

    # Dashed line effect
    step = 25
    for x in range(0, w, step * 2):
        cv2.line(img, (x, y), (min(x + step, w), y), color, 2, lineType=cv2.LINE_AA)

    # Line label tag
    tag = f" {label} "
    cv2.putText(
        img,
        tag,
        (20, y - 8),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        color,
        2,
        lineType=cv2.LINE_AA,
    )
    return img


def draw_hud(
    img: np.ndarray,
    fps: float,
    vehicle_count: int,
    plate_count: int,
    violation_count: int,
) -> np.ndarray:
    """Overlays an executive HUD status bar at the top of the video frame."""
    h, w = img.shape[:2]
    hud_h = 42

    overlay = img.copy()
    cv2.rectangle(overlay, (0, 0), (w, hud_h), (15, 18, 25), -1)
    cv2.addWeighted(overlay, 0.75, img, 0.25, 0, img)

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    th = 1

    stats = [
        f"FPS: {fps:.1f}",
        f"Vehicles: {vehicle_count}",
        f"Plates Recognized: {plate_count}",
        f"Violations: {violation_count}",
    ]

    spacing = w // len(stats)
    for i, s in enumerate(stats):
        x = 25 + i * spacing
        cv2.putText(img, s, (x, 26), font, font_scale, (230, 235, 240), th, lineType=cv2.LINE_AA)

    return img

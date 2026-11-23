import cv2
import numpy as np
from typing import Dict, Tuple, Optional
from backend.app.core.logger import logger
from backend.app.core.exceptions import PreprocessingError


class ImagePreprocessor:
    """OpenCV-based image preprocessing pipeline designed to optimize OCR recognition rates

    on diverse real-world license plate captures.
    """

    @staticmethod
    def resize_for_ocr(img: np.ndarray, target_height: int = 80) -> np.ndarray:
        """Upscales/normalizes plate image so text glyphs have sufficient stroke resolution.

        Uses bicubic interpolation for clean continuous text edges.
        """
        if img is None or img.size == 0:
            return img

        h, w = img.shape[:2]
        if h == 0 or w == 0:
            return img

        scale = target_height / float(h)
        new_w = max(int(w * scale), 16)
        resized = cv2.resize(img, (new_w, target_height), interpolation=cv2.INTER_CUBIC)
        return resized

    @staticmethod
    def to_grayscale(img: np.ndarray) -> np.ndarray:
        """Converts BGR image to single-channel 8-bit grayscale."""
        if len(img.shape) == 3 and img.shape[2] == 3:
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img

    @staticmethod
    def apply_clahe(gray: np.ndarray, clip_limit: float = 2.0, tile_grid_size: Tuple[int, int] = (8, 8)) -> np.ndarray:
        """Applies Contrast Limited Adaptive Histogram Equalization (CLAHE) to amplify local text contrast

        without blowing out bright highlights or dark shadows.
        """
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        return clahe.apply(gray)

    @staticmethod
    def apply_bilateral_filter(gray: np.ndarray, d: int = 7, sigma_color: float = 50, sigma_space: float = 50) -> np.ndarray:
        """Applies bilateral filtering to smooth surface noise, dirt, and compression artifacts

        while strictly preserving high-frequency character boundaries.
        """
        return cv2.bilateralFilter(gray, d, sigma_color, sigma_space)

    @staticmethod
    def sharpen(img: np.ndarray) -> np.ndarray:
        """Applies an unsharp mask / laplacian edge-enhancing convolution kernel."""
        kernel = np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ], dtype=np.float32)
        return cv2.filter2D(img, -1, kernel)

    @staticmethod
    def adaptive_threshold(gray: np.ndarray, block_size: int = 19, c: int = 9) -> np.ndarray:
        """Computes localized adaptive Gaussian thresholding for high-contrast binarization."""
        # Ensure block_size is odd and >= 3
        if block_size % 2 == 0:
            block_size += 1
        return cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            block_size,
            c,
        )

    @classmethod
    def preprocess_pipeline(cls, plate_crop: np.ndarray) -> np.ndarray:
        """Default optimized pipeline:

        1. Bicubic Rescaling to target height 80px
        2. Grayscale Conversion
        3. Bilateral Edge-Preserving Denoising
        4. Contrast Enhancement via CLAHE
        5. Mild Unsharp Sharpening
        """
        if plate_crop is None or plate_crop.size == 0:
            raise PreprocessingError("Empty or invalid plate crop passed to preprocessor")

        # Step 1: Rescale
        resized = cls.resize_for_ocr(plate_crop, target_height=90)
        # Step 2: Grayscale
        gray = cls.to_grayscale(resized)
        # Step 3: Bilateral Filter
        denoised = cls.apply_bilateral_filter(gray, d=7, sigma_color=50, sigma_space=50)
        # Step 4: CLAHE Contrast
        enhanced = cls.apply_clahe(denoised, clip_limit=2.5)
        # Step 5: Sharpen
        sharpened = cls.sharpen(enhanced)

        return sharpened

    @classmethod
    def generate_all_variants(cls, plate_crop: np.ndarray) -> Dict[str, np.ndarray]:
        """Generates all intermediate preprocessing stages for comparative evaluation and OCR fallback."""
        resized = cls.resize_for_ocr(plate_crop, target_height=90)
        gray = cls.to_grayscale(resized)
        denoised = cls.apply_bilateral_filter(gray, d=7, sigma_color=50, sigma_space=50)
        enhanced = cls.apply_clahe(denoised, clip_limit=2.5)
        sharpened = cls.sharpen(enhanced)
        binary = cls.adaptive_threshold(enhanced)

        return {
            "original_resized": resized,
            "grayscale": gray,
            "bilateral_denoised": denoised,
            "clahe_enhanced": enhanced,
            "sharpened": sharpened,
            "adaptive_threshold": binary,
        }

    @classmethod
    def create_comparison_grid(cls, plate_crop: np.ndarray) -> np.ndarray:
        """Stitches preprocessed variants side-by-side into a single annotated demonstration image."""
        variants = cls.generate_all_variants(plate_crop)
        h, w = variants["original_resized"].shape[:2]

        tiles = []
        for name, img in variants.items():
            # Convert single channel to 3-channel BGR for unified stacking
            if len(img.shape) == 2:
                bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            else:
                bgr = img.copy()

            # Ensure uniform height and width
            bgr = cv2.resize(bgr, (w, h))

            # Overlay stage label
            cv2.rectangle(bgr, (0, 0), (w, 20), (20, 20, 20), -1)
            cv2.putText(
                bgr,
                name.replace("_", " ").upper(),
                (5, 14),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.38,
                (0, 220, 255),
                1,
                lineType=cv2.LINE_AA,
            )
            tiles.append(bgr)

        # Stitch 2 rows x 3 columns
        row1 = np.hstack(tiles[:3])
        row2 = np.hstack(tiles[3:])
        grid = np.vstack([row1, row2])
        return grid

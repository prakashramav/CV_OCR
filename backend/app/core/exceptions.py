from typing import Any, Optional
from fastapi import HTTPException, status


class ANPRBaseException(Exception):
    """Base exception class for ANPR domain errors."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.details = details


class ModelLoadError(ANPRBaseException):
    """Raised when an AI model weights file fails to load."""
    pass


class VideoProcessingError(ANPRBaseException):
    """Raised when video stream/file decoding or writing encounters a failure."""
    pass


class PreprocessingError(ANPRBaseException):
    """Raised when image preprocessing fails on invalid frame dimensions."""
    pass


class OCRError(ANPRBaseException):
    """Raised when text recognition encounters unrecoverable errors."""
    pass


class NotFoundHTTPException(HTTPException):
    def __init__(self, detail: str = "Requested resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ValidationHTTPException(HTTPException):
    def __init__(self, detail: str = "Invalid input data"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)

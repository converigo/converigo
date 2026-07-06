"""
Application bootstrap.

Registers all built-in conversion engines.
"""

from app.engines.audio_engine import AudioEngine
from app.engines.document_engine import DocumentEngine
from app.engines.image_engine import ImageEngine
from app.engines.video_engine import VideoEngine

from app.services.conversion_manager import register_engine


def register_all_engines() -> None:
    """Register built-in conversion engines."""

    register_engine(AudioEngine)
    register_engine(VideoEngine)
    register_engine(ImageEngine)
    register_engine(DocumentEngine)
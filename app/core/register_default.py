"""
Project : Convertin
Founder : Pico Lala
Version : 1.0.0

Default Converter Registration
"""

from app.core.registry import (
    ConverterInfo,
    registry,
)


def register_default_converters() -> None:
    """
    Register built-in converters.

    Aman dipanggil berkali-kali saat development
    (misalnya ketika uvicorn --reload aktif).
    """

    defaults = [

        ConverterInfo(
            id="mp4_to_mp3",
            name="MP4 to MP3",
            category="audio",
            source_format="mp4",
            target_format="mp3",
        ),

        ConverterInfo(
            id="mp3_to_wav",
            name="MP3 to WAV",
            category="audio",
            source_format="mp3",
            target_format="wav",
        ),

    ]

    for converter in defaults:

        if registry.get(converter.id) is None:
            registry.register(converter)
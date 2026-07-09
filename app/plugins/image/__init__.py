"""
Image converter plugins.
"""

from app.plugins.image.jpg_to_png import JPGToPNGPlugin
from app.plugins.image.jpg_to_webp import JPGToWEBPPlugin
from app.plugins.image.png_to_jpg import PNGToJPGPlugin
from app.plugins.image.png_to_webp import PNGToWEBPPlugin
from app.plugins.image.webp_to_jpg import WEBPToJPGPlugin

__all__ = [
    "PNGToJPGPlugin",
    "JPGToPNGPlugin",
    "WEBPToJPGPlugin",
    "JPGToWEBPPlugin",
    "PNGToWEBPPlugin",
]
"""
Image converter plugins.
"""

from app.plugins.image.bmp_to_jpg import BMPToJPGPlugin
from app.plugins.image.jpg_to_png import JPGToPNGPlugin
from app.plugins.image.jpg_to_webp import JPGToWEBPPlugin
from app.plugins.image.png_to_ico import PNGToICOPlugin
from app.plugins.image.png_to_jpg import PNGToJPGPlugin
from app.plugins.image.png_to_webp import PNGToWEBPPlugin
from app.plugins.image.webp_to_jpg import WEBPToJPGPlugin
from app.plugins.image.webp_to_png import WEBPToPNGPlugin

__all__ = [
    "BMPToJPGPlugin",
    "PNGToJPGPlugin",
    "JPGToPNGPlugin",
    "WEBPToJPGPlugin",
    "JPGToWEBPPlugin",
    "PNGToWEBPPlugin",
    "WEBPToPNGPlugin",
    "PNGToICOPlugin",
]
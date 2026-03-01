"""Core module for gallery-dl-auto

This module contains core components like ModeManager.
"""

from gallery_dl_auto.core.mode_errors import InvalidModeError
from gallery_dl_auto.core.mode_manager import ModeManager

__all__ = ["ModeManager", "InvalidModeError"]

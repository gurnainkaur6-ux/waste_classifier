"""
Compatibility wrapper: root imports now re-export from the src package.
"""

from src.disposal_guide import DISPOSAL_GUIDE  # noqa: F401

__all__ = ["DISPOSAL_GUIDE"]

"""
Compatibility wrapper: root imports now re-export from the src package.
"""

from src.db import *  # noqa: F401,F403
from src.db import db_path, get_db, close_db, init_db, init_app  # noqa: F401

__all__ = [
    "db_path",
    "get_db",
    "close_db",
    "init_db",
    "init_app",
]

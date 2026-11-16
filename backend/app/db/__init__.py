"""
SAMVAD Database Layer
Unified support for PostgreSQL (production scale) and SQLite (zero-config local dev).
"""

from app.db.connection import DatabaseManager, get_db

__all__ = ["DatabaseManager", "get_db"]


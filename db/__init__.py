"""
Database module for FACEIT Stats application.

This module contains database models and operations for storing
and retrieving recent search data.
"""

from .database import (
    init_database,
    add_recent_search_to_db,
    get_recent_searches_from_db,
    init_test_data_db,
    RecentSearchDB
)

__all__ = [
    "init_database",
    "add_recent_search_to_db", 
    "get_recent_searches_from_db",
    "init_test_data_db",
    "RecentSearchDB"
] 
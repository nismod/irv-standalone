"""
Singleton Helpers
"""

import logging
from os import getenv
import traceback
from typing import Optional

TILEDB_URI = getenv("TILEDB_URI")


def build_driver_path(
    database: str,
    tiledb_uri: Optional[str] = TILEDB_URI,
) -> str:
    """
    Build the Terracotta driver path.
    """

    if tiledb_uri is None:
        raise ValueError("TILEDB_URI is not configured")

    return tiledb_uri + "/" + database


def handle_exception(logger: logging.Logger, err: Exception):
    """
    Handle generic exceptions
    """
    logger.error(
        "%s failed with tb %s, error: %s",
        __name__,
        traceback.format_tb(err.__traceback__),
        err,
    )

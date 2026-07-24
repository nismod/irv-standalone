import logging
from hashlib import sha256
from io import BytesIO
import json
from typing import Any, cast
from django.conf import settings
from django.core.cache import cache
from terracotta import get_settings, get_driver
from terracotta.handlers.colormap import colormap as terracotta_colormap 

from ..internal.helpers import build_driver_path
from ..serializers import ColorMapSerializer

logger = logging.getLogger(__name__)


class MissingExplicitColourMapException(Exception):
    pass


def get_image_size(image):
    if hasattr(image, "getbuffer"):
        return len(cast(Any, image).getbuffer())
    return "unknown"


def _get_colormap(options):
    """
    Retrieve colormap.
    """

    _colormap = terracotta_colormap(**options)
    return ColorMapSerializer({"colormap": _colormap})


def _parse_keys(keys):
    """
    Parse a tile URL key string.
    """

    all_keys = [key for key in keys.split("/") if key]
    if not all_keys:
        raise ValueError("Tile keys path is empty")

    return all_keys


def _get_singleband_image(
    database,
    keys,
    tile_xyz=None,
    options=None,
):
    """
    Generate a singleband tile.
    """

    from ..internal.tiles.singleband import singleband

    driver_path = build_driver_path(database)
    cache_timeout = getattr(settings, "RASTER_TILE_CACHE_TIMEOUT", 0)
    tile_options = options or {}

    logger.debug(
        "parsed_keys: %s, tile_xyz: %s, options: %s",
        keys,
        tile_xyz,
        tile_options,
    )

    if cache_timeout > 0:
        cache_key = _tile_cache_key(
            database=database,
            keys=keys,
            tile_xyz=tile_xyz,
            options=tile_options,
        )
        cached_image = cache.get(cache_key)
        if cached_image is not None:
            return BytesIO(cached_image)

    image = singleband(
        driver_path,
        keys,
        tile_xyz=tile_xyz,
        **tile_options,
    )
    image_bytes = _image_bytes(image)

    if cache_timeout > 0:
        cache.set(cache_key, image_bytes, cache_timeout)

    return BytesIO(image_bytes)


def _image_bytes(image):
    if hasattr(image, "getvalue"):
        return cast(Any, image).getvalue()

    if hasattr(image, "seek"):
        cast(Any, image).seek(0)

    return cast(Any, image).read()


def _tile_cache_key(database, keys, tile_xyz, options):
    payload = json.dumps(
        {
            "database": database,
            "keys": list(keys),
            "tile_xyz": list(tile_xyz) if tile_xyz is not None else None,
            "options": options,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return "raster_tile_png:" + sha256(payload.encode("utf-8")).hexdigest()


def _source_options(source_db, filters=None):
    """
    Gather all URL key combinations available in the given source.
    """

    driver_path = build_driver_path(source_db)
    settings = get_settings()
    driver = get_driver(
        driver_path,
        provider=settings.DRIVER_PROVIDER,
    )

    with driver.connect():
        datasets = driver.get_datasets(where=filters)
        keys = driver.get_keys()

    options = [dict(zip(keys, values)) for values in datasets.keys()]
    return options

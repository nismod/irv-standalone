import logging
from typing import Any, cast
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

    logger.debug(
        "parsed_keys: %s, tile_xyz: %s, options: %s",
        keys,
        tile_xyz,
        options,
    )

    return singleband(driver_path, keys, tile_xyz=tile_xyz, **(options or {}))


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

    datasets = driver.get_datasets()
    keys = driver.get_keys()

    options = [dict(zip(keys, values)) for values in datasets.keys()]
    if filters:
        filtered_options = [
            option
            for option in options
            if all(option.get(key) == value for key, value in filters.items())
        ]
        if filtered_options:
            options = filtered_options
    return options

import logging
from typing import Any, cast
from terracotta import get_settings, get_driver
from terracotta.handlers.colormap import colormap as terracotta_colormap 

from ..internal.helpers import build_driver_path
from ..serializers import ColorMapSerializer

logger = logging.getLogger(__name__)


class SourceDBDoesNotExistException(Exception):
    def __init__(self, source_db):
        super().__init__(source_db)
        self.source_db = source_db


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

    domain = all_keys[0]
    parsed_keys = all_keys[1:]
    return domain, parsed_keys


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


def _tile_db_from_domain(domain):
    """
    Map a tile domain to its Terracotta database name.
    """

    domain_to_db = {
        "default": "terracotta.sqlite",
        "singleband": "terracotta.sqlite",
    }

    try:
        return domain_to_db[domain]
    except KeyError as err:
        raise SourceDBDoesNotExistException(domain) from err


def _source_options(source_db):
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

    return [dict(zip(keys, values)) for values in datasets.keys()]

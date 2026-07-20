"""Discover raster files and ingest them into a Terracotta database."""

from __future__ import annotations

import glob
import os
import re
import string
from pathlib import Path
from typing import Sequence

DEFAULT_PATH_TEMPLATE = (
    "{type}__rp_{rp}__rcp_{rcp}__epoch_{epoch}__conf_{confidence}.tif"
)
SUPPORTED_DATABASE_PROVIDERS = ("sqlite", "mysql", "postgresql")


def infer_database_provider(database: str) -> str:
    """Infer a Terracotta provider name from a database URL or path."""
    scheme = database.partition("://")[0] if "://" in database else ""
    provider = scheme.partition("+")[0]
    if provider == "postgres":
        provider = "postgresql"
    return provider if provider in SUPPORTED_DATABASE_PROVIDERS else "sqlite"


def parse_path_template(
    path_template: str,
) -> tuple[list[str], str, re.Pattern[str]]:
    """Turn a template into key names, a glob, and a regex."""
    keys: list[str] = []
    glob_parts: list[str] = []
    regex_parts: list[str] = []

    try:
        parsed_template = string.Formatter().parse(path_template)
        for literal, field_name, format_spec, conversion in parsed_template:
            glob_parts.append(literal)
            regex_parts.append(re.escape(literal))

            if field_name is None:
                continue
            if format_spec or conversion:
                raise ValueError(
                    "format specifications and conversions "
                    "are not supported"
                )

            glob_parts.append("*")
            if not field_name:
                regex_parts.append(".*?")
            elif field_name in keys:
                regex_parts.append(f"(?P={field_name})")
            else:
                if not field_name.isidentifier():
                    raise ValueError(
                        f"key name {field_name!r} must be a valid "
                        "Python identifier"
                    )
                keys.append(field_name)
                regex_parts.append(f"(?P<{field_name}>[^/]+?)")
    except (IndexError, KeyError) as exc:
        raise ValueError(f"invalid path template: {exc}") from exc

    if not keys:
        raise ValueError(
            "path template must contain at least one named placeholder"
        )

    return keys, "".join(glob_parts), re.compile("".join(regex_parts))


def discover_rasters(
    path_template: str,
) -> tuple[list[str], dict[tuple[str, ...], str]]:
    """Find raster paths and extract their Terracotta key values."""
    absolute_template = os.path.abspath(path_template)
    keys, glob_pattern, regex_pattern = parse_path_template(absolute_template)
    rasters: dict[tuple[str, ...], str] = {}

    for candidate in sorted(glob.glob(glob_pattern)):
        absolute_candidate = os.path.abspath(candidate)
        match = regex_pattern.fullmatch(absolute_candidate)
        if match is None:
            continue

        key_values = tuple(match.group(key) for key in keys)
        if key_values in rasters:
            raise ValueError(
                "path template produces duplicate key values for "
                f"{rasters[key_values]!r} and {absolute_candidate!r}"
            )
        rasters[key_values] = absolute_candidate

    if not rasters:
        raise ValueError(f"path template matches no files: {path_template}")

    return keys, rasters


def move_key_to_end(
    keys: list[str],
    rasters: dict[tuple[str, ...], str],
    key_name: str,
) -> tuple[list[str], dict[tuple[str, ...], str]]:
    """Move the RGB key to Terracotta's expected final position."""
    if key_name not in keys:
        raise ValueError(
            f"RGB key {key_name!r} is not present in the path template"
        )

    index = keys.index(key_name)
    reordered_keys = [*keys[:index], *keys[index + 1:], keys[index]]
    reordered_rasters = {
        (*values[:index], *values[index + 1:], values[index]): path
        for values, path in rasters.items()
    }
    return reordered_keys, reordered_rasters


def get_or_create_driver(
    database: str, database_provider: str | None, keys: Sequence[str]
):
    """Open an initialized Terracotta driver.

    Create its database if needed.
    """
    import terracotta
    from terracotta.exceptions import InvalidDatabaseError

    provider = database_provider
    if provider is None:
        provider = infer_database_provider(database)

    database_existed = provider != "sqlite" or Path(database).is_file()
    driver = terracotta.get_driver(database, provider=provider)

    if not database_existed:
        driver.create(keys)
        return driver

    try:
        driver_keys = driver.key_names
    except InvalidDatabaseError:
        # Server databases are not represented by a local file, so a failed
        # lookup is the only provider-independent way to detect one that
        # still needs creating.
        driver.create(keys)
        driver_keys = driver.key_names

    if tuple(keys) != tuple(driver_keys):
        raise ValueError(
            "database has incompatible keys "
            f"{driver_keys}; expected {tuple(keys)}"
        )
    return driver


def ingest_rasters(
    *,
    path_template: str,
    database: str,
    database_provider: str | None = None,
    rgb_key: str | None = None,
    skip_existing: bool = False,
    skip_metadata: bool = False,
    quiet: bool = False,
) -> int:
    """Discover and ingest rasters, returning the number inserted."""
    from tqdm import tqdm

    keys, rasters = discover_rasters(path_template)
    if rgb_key is not None:
        keys, rasters = move_key_to_end(keys, rasters, rgb_key)

    driver = get_or_create_driver(database, database_provider, keys)
    if skip_existing:
        existing = driver.get_datasets()
        rasters = {
            values: path
            for values, path in rasters.items()
            if values not in existing
        }

    with driver.connect():
        for key_values, raster_path in tqdm(
            rasters.items(),
            desc="Ingesting raster files",
            disable=quiet,
        ):
            driver.insert(key_values, raster_path, skip_metadata=skip_metadata)

    return len(rasters)


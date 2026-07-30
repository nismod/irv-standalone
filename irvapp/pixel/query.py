from dataclasses import dataclass
import logging
from pathlib import Path

import pandas as pd
from pyproj import CRS
from pyproj.transformer import Transformer
import xarray as xr


@dataclass
class RasterStackMetadata:
    """Metadata about each stack of rasters (those sharing a grid)"""

    name: str
    path: Path
    crs: CRS


def point_query(
    datasets: list[RasterStackMetadata],
    layer_metadata: pd.DataFrame,
    lon: float,
    lat: float,
) -> dict[str, list]:
    """
    Query a raster file with multiple bands to extract the values at a
    specific (lon, lat) coordinate.

    Parameters:
        datasets: Metadata about the grids shared by raster layers
        layer_metadata: Metadata about the individual raster layers
        lon: longitude coordinate
        lat: latitude coordinate

    Returns:
        dict: A dictionary of column names to lists of values. `band_data`
            contains the raster values.
    """
    dfs = []
    for dataset in datasets:
        # must be always_xy to handle lon, lat and tx, ty in correct order
        t = Transformer.from_crs("EPSG:4326", dataset.crs, always_xy=True)
        tx, ty = t.transform(lon, lat)
        ds = xr.open_zarr(dataset.path)

        # extract bounds
        xmin, xmax, ymin, ymax = (
            float(ds.x.min()),
            float(ds.x.max()),
            float(ds.y.min()),
            float(ds.y.max()),
        )
        logging.debug(
            f"Query for {lon=}, {lat=} in {dataset.name=} "
            f"{dataset.crs.to_string()} at {tx=}, {ty=} "
            f"bounds {xmin=} {xmax=} {ymin=} {ymax=}"
        )

        if tx < xmin or tx > xmax or ty < ymin or ty > ymax:
            # out of bounds for this dataset
            logging.debug(
                f"Point {lon=}, {lat=} outside bounds for {dataset.name=}")
            continue

        dfs.append(
            ds.sel(x=tx, y=ty, method="nearest")
            .drop_vars(["x", "y"])
            .to_dataframe()
            .reset_index()
        )

    if dfs:
        data = pd.concat(dfs).merge(layer_metadata, on="key")

        # The dimensions of a raster layer are data, not part of the pixel
        # API contract.  Keep the metadata column order from the CSV and add
        # the sampled value at the end.  This allows layers with dimensions
        # such as GWL/RP or SLR/RP to use the same endpoint as the existing
        # RCP/epoch layers.
        metadata_columns = [
            column for column in layer_metadata.columns if column in data.columns
        ]
        columns = [*metadata_columns, "band_data"]
        data = data.loc[:, columns]
        return data.to_dict(orient="list")
    else:
        return {}

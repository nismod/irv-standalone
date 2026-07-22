"""Build Zarr raster stacks for the Django pixel app."""

import importlib.util
from pathlib import Path
import logging

import pandas as pd


DEFAULT_LAYERS_PATH = (
    Path(__file__).resolve().parents[2] / "etl" / "hazard_layers.csv"
)


def read_grids(
    source_path: Path,
    layers: pd.DataFrame,
    *,
    quiet: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read raster grid metadata and assign each layer to a unique grid."""
    import rasterio
    from tqdm.auto import tqdm

    grid_lookup: dict[tuple[object, ...], str] = {}
    grid_metadata: dict[str, dict[str, object]] = {}
    layer_grid_ids: list[str] = []

    for layer in tqdm(
        layers.itertuples(),
        total=len(layers),
        desc="Reading layer metadata",
        disable=quiet,
    ):
        grid_path = source_path / layer.path
        with rasterio.open(grid_path) as dataset:
            grid = (
                str(dataset.crs),
                dataset.width,
                dataset.height,
                tuple(dataset.transform),
            )
            if grid not in grid_lookup:
                grid_id = f"grid_{len(grid_lookup)}"
                grid_lookup[grid] = grid_id
                grid_metadata[grid_id] = {
                    "crs": str(dataset.crs),
                    "width": dataset.width,
                    "height": dataset.height,
                    "transform": tuple(dataset.transform),
                    "grid_id": grid_id,
                }
        layer_grid_ids.append(grid_lookup[grid])

    grids = pd.DataFrame(grid_metadata.values())
    layers = layers.copy()
    layers["grid_id"] = layer_grid_ids

    return layers, grids


def stack(
    source_path: Path,
    target_path: Path,
    layers: pd.DataFrame,
    grids: pd.DataFrame,
):
    """Write one Zarr stack for each unique grid definition."""
    import numpy as np
    import rasterio
    import xarray as xr

    grid_fname_lookup = grids.set_index("grid_id")

    for grid_id, grid_layers in layers.groupby("grid_id"):
        var = xr.Variable("key", grid_layers.key.tolist())
        layer_paths = grid_layers.path.tolist()
        logging.info("Processing %s layers for %s", len(layer_paths), grid_id)
        ds = xr.concat(
            [
                _open_raster_band(source_path / layer_path, rasterio, np, xr)
                for layer_path in layer_paths
            ],
            dim=var,
        )
        if importlib.util.find_spec("dask") is not None:
            ds = ds.chunk({"x": 100, "y": 100, "key": 1000})
        else:
            logging.warning(
                "dask is not installed; writing unchunked stack for %s",
                grid_id,
            )
        dsc = ds.to_dataset()

        grid_fname = grid_fname_lookup.loc[grid_id, "fname"]
        dsc.to_zarr(target_path / grid_fname, mode="w-")


def ingest_pixel_stacks(
    source_path: Path,
    target_path: Path,
    *,
    layers_path: Path = DEFAULT_LAYERS_PATH,
    quiet: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ingest raster layers into Zarr stacks and write stack metadata CSVs."""
    target_path.mkdir(parents=True, exist_ok=True)

    layers = pd.read_csv(layers_path)
    missing = {"path", "key"} - set(layers.columns)
    if missing:
        raise ValueError(
            f"layers CSV at {layers_path} is missing required column(s): {', '.join(sorted(missing))}"
        )
    layers, grids = read_grids(source_path, layers, quiet=quiet)
    grids["fname"] = grids.grid_id.apply(lambda grid_id: f"{grid_id}.zarr")

    stack(source_path, target_path, layers, grids)

    layers.to_csv(target_path / "layers.csv", index=False)
    grids.to_csv(target_path / "stacks.csv", index=False)

    return layers, grids


def _open_raster_band(raster_path: Path, rasterio, np, xr):
    with rasterio.open(raster_path) as dataset:
        band = dataset.read(1)
        x, _ = rasterio.transform.xy(
            dataset.transform,
            np.zeros(dataset.width, dtype=int),
            np.arange(dataset.width),
            offset="center",
        )
        _, y = rasterio.transform.xy(
            dataset.transform,
            np.arange(dataset.height),
            np.zeros(dataset.height, dtype=int),
            offset="center",
        )
        return xr.DataArray(
            band,
            dims=("y", "x"),
            coords={"y": y, "x": x},
            name="band_data",
        )

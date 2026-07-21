import numpy as np
import rasterio
from rasterio.transform import from_origin
import xarray as xr


def create_raster(
    file_path,
    width,
    height,
    value=0,
    crs="EPSG:4326",
):
    """
    Create a single-band raster with constant values.

    Parameters:
        file_path (str): Path to save the raster.
        width (int): Width of the raster.
        height (int): Height of the raster.
        value (int or float): Constant value for the raster.
        crs (str): Coordinate Reference System for the raster.
    """
    transform = from_origin(0, 0, 1, 1)  # Arbitrary transform
    data = np.full((height, width), value, dtype=np.float32)

    with rasterio.open(
        file_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype=np.float32,
        crs=crs,
        transform=transform,
    ) as dst:
        dst.write(data, 1)


def create_stack():
    """Creates a zarr dataset for testing"""
    data = np.arange(16).reshape(2, 2, 4)
    da = xr.DataArray(
        data,
        dims=("x", "y", "key"),
        coords={"x": [0.0, 0.1], "y": [0.0, 0.1], "key": ["a", "b", "c", "d"]},
    )
    ds = xr.Dataset({"band_data": da})
    ds.to_zarr("test.zarr", mode="w-")


if __name__ == "__main__":
    # Generate single-band rasters
    for i, letter in enumerate(["a", "b", "c", "d"]):
        create_raster(f"single_band/{letter}.tif", 10, 10, value=i)

    create_stack()

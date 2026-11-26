# Extract-transform-load

This workflow follows on from the final steps of the `jamaica-infrastructure` analysis workflow,
in particular those [rules which "prepare for visualisation"](https://github.com/nismod/jamaica-infrastructure/blob/development/workflow/7_etl/_etl.smk)

In summary:
- hazard data is input as a set of raster files, output as Cloud-Optimised Geotiffs (for map visualisation, one layer at a time)
  and Zarr datasets (for point query, all layers at a single location)
- infrastructure feature layers are input as parquet files from the end of `jamaica-infrastructure`
  and loaded into a Postgres database (containing the features and full risk/adaptation results)
  and also processed into .mbtiles files (containing the features as vector tiles for map visualisation).

Before and after running this workflow against a staging or live server, it is recommended to backup and archive 
the database and updated files. Here's a script: [`archive-data.sh`](../../archive-data.sh)

Coordinate with system administrators on the best way to access development, staging, and production
servers, for example through University of Oxford, University of the West Indies, or National
Spatial Data Management Branch (NSDMB). No contact information or further details should be 
recorded in this public repository.

There are three categories of data that go in roughly three corresponding
places:

## 1. Features

These are all of the vector layers of infrastructure networks with their
geometries and attributes.

The data files (GeoPackages, some with multiple layers) are listed in
`network_layers.csv`

These are transformed into tilelayers for visualisation on the site, as listed
in `network_tilelayers.csv`

One data layer (e.g. transport_roads_edges) may become one or more tilelayers
(e.g. road_edges_class_a, road_edges_class_b, road_edges_class_c,
road_edges_track, road_edges_metro, road_edges_other).

Feature layers are first loaded into the database, then dumped as line-delimited
GeoJSON, then converted into MBTiles files (these are SQLite database files
containing Mapbox Vector Tiles). 

These MBTiles are then referenced by the vector tileserver `config.json` to
make them accessible in the web application.

## 2. Damages and adaptation results

These are all in parquet files, relating to damage and loss calculations on the
infrastructure feature layers. 

These data are loaded into the database, into each of the corresponding tables, 
in general with a transformation from "fat" (many columns for each of the 
hazard RP/RCP/epoch/... combinations) to "long" or "tidy" (many rows, with RP, 
RCP, epoch, ... columns serving as a multi-column index) table format.

## 3. Hazard rasters

Hazard maps are stored as 2D raster data in GeoTIFFs for analysis. These are
each converted to Cloud-Optimised GeoTIFF format. We also set zero values to
nodata (which is something of a judgement call - nodata values will be
visualised as transparent, which is desirable in the case of flood or wind speed
return period maps).

The files are named on a strict template, which allows the terracotta server to
address each layer with a combination of parameters:
`{hazard_type}__rp_{rp}__rcp_{rcp}__epoch_{epoch}__conf_{confidence}.tif`

### Raster ingestion

There is a following step, not in the Snakefile, to ingest all the prepared
rasters into a metadata database. This includes the absolute path to the file,
so is best to run either within a container (with data mounted to the same path
whether the container is runnin in development or production) or once per host
machine, with the full path changed from `/data` as required:

```
python irvapp/manage.py ingest_rasters /data \
  --path-template '{type}__rp_{rp}__rcp_{rcp}__epoch_{epoch}__conf_{confidence}.tif' \
  --database /data/terracotta.sqlite
```

The database may instead be a PostgreSQL URL, for example
`postgresql://user:password@host/terracotta`. The same values can be supplied
through `RASTER_BASE_PATH`, `RASTER_PATH_TEMPLATE`, `TC_DRIVER_PATH`, and
`TC_DRIVER_PROVIDER`.

## 4. Other

There are a couple of other vector layers that provide supporting information,
and are converted to MBTiles, for example regions and nature-based solutions.


## Requirements

- PostGIS database, potentially running in a local container for development
  - Django models and migrations are in `../irvapp`; configure `PGDATABASE`,
    `PGUSER`, `PGPASSWORD`, `PGHOST`, and `PGPORT` as for the application
- Python, Snakemake and other packages in `environment.yml`
- [`jq`](https://stedolan.github.io/jq/)
- [`geojson-polygon-labels`](https://github.com/andrewharvey/geojson-polygon-labels)
- [`tippecanoe`](https://github.com/mapbox/tippecanoe)


### Jamaica database import

The Jamaica feature, damage, adaptation and vector-export loaders use the
Django models and PostGIS connection. They retain the Jamaica RCP/epoch input
conventions; Mauritius and St Lucia formats have not been assessed. The NPV
model and its ETL target have been removed. The migrated workflow has not yet
been rehearsed with representative Jamaica files or a staging database. Do not
use it on production until that validation is complete.

Create the environment from the `etl` directory with
`micromamba create -f environment.yml`, activate it, and apply the application
migrations with `python ../irvapp/manage.py migrate`. Check the database and
connection settings before importing. From `etl`, run:

```sh
python ../irvapp/manage.py migrate --check
snakemake --cores 1 logs/feature_layers.txt
python ../irvapp/manage.py link_feature_layers
```

The importer creates missing feature identities and layers atomically, rejects
raster ID collisions and conflicting CSV definitions, and leaves existing
metadata and ordering intact. It reports differing metadata and layers without
a dataset. `link_feature_layers` assigns matching dataset IDs only; review
remaining assignments in Django admin. Tree and style links are not reconciled
by this importer and must be reviewed separately. Unassigned layers are not
available through the application.

Run `snakemake --cores 1 load_to_database` to load the standard feature,
expected-damage, return-period and adaptation targets. Coastal adaptation is a
separate, optional target: run `snakemake --cores 1 all_coastal_adaptation_to_db`
after confirming that its source files and protector mappings exist. The rules
express feature-before-result dependencies, including coastal protectors. Export
tile layers after feature import; tiles carry the database UID and use the
scenario-aware API for damage attributes.

Each feature source reload is atomic. Existing UIDs and their results are
preserved; the reload rejects duplicate or foreign UIDs and refuses to remove a
feature referenced by a result or as a protector. Each result file is imported
atomically in batches using its composite key; repeated keys update values and
duplicate keys in one input fail. Duplicate detection uses a temporary SQLite
index on disk, removed on success or failure; ensure the temporary directory
(`TMPDIR`, when set) has space proportional to the number of result keys.
Parameter sets are cached in memory. Profile the complete import with a
representative Jamaica file and the intended worker limits before staging. An
existing adaptation key with a different protector is rejected. A failed
transaction leaves the prior database state.
Results are upserted, not replaced: rows that disappear from an input, including
values changed to zero, remain in the database. Use a fresh disposable database
for changed-input rehearsals; do not rely on a rerun to remove stale results.
The existing Jamaica parsers retain their positive-value filter, so zero-only
scenarios are not discoverable. Return-period files must have the same UID order
and length; their confidence is retained when present. Validate source counts,
scenario values and totals, and protector mappings before accepting an import.

Snakemake logs are completion markers for the database and inputs used at the
time, not proof of current database state. After changing databases or restoring
a backup, force the relevant rules to rerun; for example:

```sh
snakemake --cores 1 --forcerun feature_layers_to_db logs/feature_layers.txt
```

Use a disposable PostGIS database for initial and repeated imports, changed-input
and interruption tests. Rehearse against a staging copy before production.
Review unassigned datasets, tree and style links, raster access and pixel-stack
catalogues separately; these steps are not handled by the Jamaica loaders.

### GDAL tools

[ogr2ogr](https://www.gdal.org/ogr2ogr.html) and other GDAL programs are used
for spatial data processing. On Ubuntu, run:

    sudo apt-get install gdal-bin


### Tippecanoe

The data preparation steps use
[Mapbox tippecanoe](https://github.com/mapbox/tippecanoe) to build vector tiles
from large feature sets.

The easiest way to install tippecanoe on OSX is with Homebrew:

    brew install tippecanoe

On Ubuntu it will usually be easiest to build from the source repository:

    sudo apt-get install build-essential g++ libsqlite3-dev zlib1g-dev
    git clone https://github.com/mapbox/tippecanoe
    cd tippecanoe
    make -j
    make

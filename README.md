# Infrastructure Risk Visualisation Tool

This project provides interactive data visualisations of risk analysis results.

The tool presents the infrastructure systems and hazards considered in the
analysis, then presents results as modelled for the whole system at a fine
scale.

Other functionality:

- Zoom in to see networks in detail.
- See an overview of hazard data.
- Inspect details of hazard layers.
- Query attributes of elements of the system.
- Range of potential economic impacts of failure, consisting of direct damages
  to infrastructure assets and indirect economic losses resulting from
  infrastructure service disruption (loss of power, loss of access).
- Explore a cost-benefit analysis of adaptation measures.

This README covers requirements and steps through how to prepare data for
visualisation and how to run the tool.

1. Data preparation
2. Build and run
3. Deployment

## Data preparation

The visualisation tool runs using prepared versions of analysis data and results:

- Rasters stored as Cloud-Optimised GeoTIFFs, with metadata ingested into a
  SQLite database
- Vector (asset or feature) data stored in a PostgreSQL database
- Vector data preprocessed into Mapbox Vector Tiles

See `./etl` directory for details.

### App currency

After applying Django migrations, edit the `currency` entry under **Map configs**
in Django admin. Set its type to **String** and its value to a three-letter ISO
currency code, such as `MUR`, `GBP`, or `USD`, then reload the app. The default is
`JMD`.

The frontend exposes this as `mapViewConfig.app.currency`. Asset damage and
adaptation field specs carry a display `unit`, such as `MUR` or `MUR/day`, which
their legend, tooltip, and list formatters use. Damage chart and table headings
use the configured currency's symbol, retaining `J$` for `JMD`. Number formatting
follows the browser locale.
The data must already be expressed in that currency; this setting does not
convert values. Raster financial layers retain their dataset-specific units.

## Build and run

Running the application requires several server processes: the vector and raster
tileservers, the app backend, and the app frontend.

To run all of these through docker compose on a local machine, run:

```bash
docker compose -f docker-compose.dev.yml up
```

The following sections describe the dependencies and dev setup for each service.


### Node and npm

The build and run steps use [node.js](https://nodejs.org/) - this provides the
`npm` command.

Install required packages. Run from the `frontend` directory:

```bash
npm install
```

### Run the vector tileserver

Run the tileserver directly (from the root of the project) using docker:

```bash
docker compose -f docker-compose.dev.yml up vector-tileserver -d
```

### Run the raster tileserver

Install the raster tileserver either in a local environment, or as a docker container.

For example, installing using conda:

```bash
conda create --name infrariskvis python=3.8 numpy rasterio shapely crick
conda activate infrariskvis
pip install terracotta[recommended]
```

Or build using docker:

```bash
docker compose -f docker-compose.dev.yml build raster-tileserver
```

Prepare the raster tileserver database:

```bash
docker compose -f docker-compose.dev.yml run --rm raster-tile-ingester
```

Prepare the pixel stack data:

```bash
python irvapp/manage.py ingest_pixel_stacks \
  /path/to/jamaica-infrastructure/processed_data \
  tileserver/stacks
```

The ingester reads `RASTER_BASE_PATH`, `RASTER_PATH_TEMPLATE`, `TC_DRIVER_PATH`,
and optionally `TC_DRIVER_PROVIDER`. For example, a PostgreSQL-backed ingest can
be run with:

```bash
python irvapp/manage.py ingest_rasters tileserver/raster/data \
  --path-template '{type}__rp_{rp}__rcp_{rcp}__epoch_{epoch}__conf_{confidence}.tif' \
  --database 'postgresql://user:password@localhost/terracotta'
```

Run the raster tileserver:

```bash
docker compose -f docker-compose.dev.yml up raster-tileserver -d
```

### Run the backend Django app

Run `docker-compose` to run the Django app, Postgres database, and tile servers in containers (behind a Traefik proxy.) The Django app runs in development mode, picking up any local changes that you make to the code in the `irvapp/` directory.

```bash
docker compose -f docker-compose.dev.yml up -d
```

Run the Django database migrations inside the `django` container, to create the backend database tables (or apply any database changes since you last ran the app):

```bash
docker compose -f docker-compose.dev.yml exec django python manage.py migrate
```

If this is your first time running the Django app, you'll need to create an admin user.

```bash
docker compose -f docker-compose.dev.yml exec django python manage.py createsuperuser
```

#### Populating the database

Model scenarios used by the map and asset list are discovered from result rows at
`GET /api/map/model-scenarios/{field_group}`, where `field_group` is
`damages_expected` or `adaptation`. The endpoint accepts repeated `layer` filters,
asset filters (`sector`, `subsector`, `asset_type`), and an optional `hazard`.
Adaptation scenarios can also be scoped by `protector_id`. Each row contains a
complete `parameters` object alongside fixed result dimensions such as protection
standard or adaptation option. The controls preserve these combinations and value
types. “All hazards” offers only scenarios shared by the hazards in the selected
asset scope. Flexible damage scenarios use the bulk attributes API; existing
Jamaica tiles remain a fast path for their supported RCP/year scenarios.

The first time that you run the Django app, the backend database will be empty.
The next step runs `pg_restore` to load data to the database from a backup.
This runs `pg_restore` on the host against the database running in
docker, which is available through `postgresql-client` packages
([various routes to download](https://www.postgresql.org/download/)) or through
[conda-forge](https://anaconda.org/channels/conda-forge/packages/postgresql/overview).

```
PGPORT=5432 \
PGHOST=localhost \
PGUSER=docker \
PGPASSWORD=docker \
PGDATABASE=jamaicadev \
pg_restore -cC -j 8 -d jamaicadev ./archive/jamaicadev_2023-05-16.dump
```

### Run the frontend app in development mode

Start the app server (from the `frontend`  directory):

```bash
npm start
```

This should automatically open a browser tab. If not, open:

    firefox http://localhost:5173/

See `./deploy` directory for details.


## Acknowledgements

This tool has been developed through several projects.

- [v0.1](https://github.com/oi-analytics/oi-risk-vis/releases/tag/v0.1-argentina)
  was developed by Oxford Infrastructure Analytics for the Government of
  Argentina with funding support from the World Bank Group and Global Facility
  for Disaster Reduction and Recovery (GFDRR).
- [v0.2](https://github.com/oi-analytics/oi-risk-vis/releases/tag/v0.2.0-seasia)
  was developed by Oxford Infrastructure Analytics for the Disaster Risk
  Financing and Insurance Program (DRFIP) of the World Bank with support from
  the Japan&mdash;World Bank Program for Mainstreaming DRM in Developing
  Countries, which is financed by the Government of Japan and managed by the
  Global Facility for Disaster Reduction and Recovery (GFDRR) through the Tokyo
  Disaster Risk Management Hub.
- [v0.3..v0.4](https://github.com/nismod/irv-jamaica/releases/tag/0.4.32)
  was developed by the Oxford Programme for Sustainable Infrastructure
  Systems in the Environmental Change Institute, University of Oxford, for the
  Government of Jamaica (GoJ) as part of a project funded by UK Aid (FCDO). The
  initiative formed part of the Coalition for Climate Resilient Investment’s
  (CCRI) collaboration with the GoJ, which also includes analysis of
  nature-based approaches to build resilience in Jamaica to be procured and
  funded by the Green Climate Fund (GCF). Subsequently the Climate Studies Group
  Mona at the University of the West Indies contributed to further development
  funded by UK International Development (FCDO).
- the current version is under development by the Oxford Programme for Sustainable
  Infrastructure Systems, University of Oxford, again funded by UK International
  Development (FCDO).

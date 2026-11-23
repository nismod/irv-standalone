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

### Populating the database

#### Infrastructure tree

Infrastructure tree leaves can be linked to feature layers in Django admin.
Each layer can be linked to at most one node, and nodes with children must not
have a layer. Migration 0026 links leaves whose node IDs match existing layer
names and warns about unmatched leaves. Review those warnings and set the links
in admin after the relevant layers have been loaded. Unlinked leaves are
disabled in the map. They remain allowed during this transition;
model validation is applied by Django forms, not by direct database writes.

#### Feature layers and datasets

Feature layers belong to datasets through their layer identities and inherit
their access groups. Assign the dataset on the identity in Django admin. Set their
stacking and display order on the feature layer in Django admin; display order
orders linked siblings in the infrastructure tree. Migration 0029 links layers whose IDs match
dataset IDs and copies their order values. It warns about unmatched layers,
which remain unlinked and unavailable through the vector tile proxy until an
administrator assigns a dataset. Layer IDs continue to identify vector tiles.
After loading feature layers, run `python manage.py link_feature_layers` in the
Django environment. It links unassigned layers whose IDs match dataset IDs and
reports any remaining layers for manual assignment. Existing assignments are
left intact.
Feature and result APIs also restrict their responses to layers in datasets that
the signed-in user can access. Unlinked layers are excluded. Inaccessible
feature and result detail URLs return 404, and aggregate lookups exclude their
data.

Feature and raster layers share a single ID namespace. Migration 0031 stops
and reports any IDs already used by both types so they can be resolved before
retrying. The database enforces uniqueness for later writes. Stacking order is
shared across both types when drawing the map; equal values retain their
existing relative order. Display order uses the same values while the current
sidebar sections and feature-tree hierarchy remain separate.

Each feature or raster layer has a one-to-one identity as its primary key.
Feature- and raster-layer saves create an unassigned identity when needed.
Both can remain unassigned until datasets are available; unassigned layers are
not accessible through the app. Direct database inserts
must create a matching `layer_identities` row first. Deleting a layer leaves its
identity available for review or explicit deletion. The existing ETL does not
yet create identity records for new feature layers.

#### Raster layers and datasets

A dataset controls access for its raster layers through its access groups. Each
raster layer's identity can belong to one dataset and the layer references one
raster tile source; multiple layers can use the same source. Assign the dataset
on the identity in Django admin. Configure layer labels, units, colours,
and display order on the raster layer in Django admin. Datasets continue to
support non-raster data as well.

Unassigned raster layers appear in the hazard catalogue as disabled until a
dataset is assigned. Raster layers assigned to an inaccessible hazard dataset
also remain visible but disabled. Once assigned to a non-hazard dataset, a
layer no longer appears in the hazard catalogue.

Because raster keys are supplied by the caller, access to a shared raster
database requires access to every dataset whose layers use that database. This
applies to tile and domain requests and also to separate source records pointing
to the same database. To provide different access rights, use separate raster
databases; otherwise a user who lacks access to any one dataset on the shared
database cannot use its raster layers.

Migration 0027 creates a raster layer for each existing dataset with a tile
source, preserving its ID and display settings. Review the resulting layers and
move them into shared datasets as needed. Moving a layer changes its access to
the permissions of its new dataset. Raster layer metadata is available at
`/api/map/raster-layers`; raster tile and domain URLs use the layer ID.

#### Model Scenarios

Model scenarios used by the map and asset list are discovered from result rows at
`GET /api/map/model-scenarios/{field_group}`, where `field_group` is
`damages_expected` or `adaptation`. The endpoint accepts repeated `layer` filters,
asset filters (`sector`, `subsector`, `asset_type`), and an optional `hazard`.
Adaptation scenarios can also be scoped by `protector_id`. Each row contains a
complete `parameters` object alongside fixed result dimensions such as protection
standard or adaptation option. The controls preserve these combinations and value
types. “All Hazards” combines the available parameters in the selected asset
scope: for example, coastal SLR and river/surface GWL can be selected together.
The damage hazard radio group selects one hazard or “All Hazards”. The scenario
logic also supports subsets supplied through state, such as river and surface
flooding without coastal flooding; controls, totals, and matching raster layers
continue to follow those selections.
Shared parameter values and protection standards must agree across hazards.
Damage requests use the bulk attributes API, which sums exactly one selected
scenario per accessible hazard. The optional `hazard_parameters` dimension maps
each selected hazard to its parameter object for subsets or differing schemas; `parameters`
contains the combined control values. Partial selections omit `hazard`; full
selections use `hazard: "all"`. Full selections with a shared parameter object
continue to work without this mapping.

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

##### Synthetic development results

Once feature geometries and hazard rasters have been imported, the optional
`seed_synthetic_results` command creates **synthetic UI fixtures**, not risk
estimates. It samples existing features and reads complete climate scenarios
from each hazard's raster catalogue. Return period and confidence are excluded
from the model parameters; return-period damage rows use only periods actually
available for that scenario. No raster files or vector tiles are changed.

Apply migrations, then preview a small run:

```bash
docker compose -f docker-compose.dev.yml exec django python manage.py migrate
docker compose -f docker-compose.dev.yml exec django python manage.py seed_synthetic_results --layer road_edges_class_a --layer elec_edges_high --hazard fluvial --hazard pluvial --dry-run
```

Remove `--dry-run` to generate the results. By default the command samples up to
25 positive-ID features per layer using `--seed 42`. Repeat `--layer` or
`--hazard` to choose a scope, or omit them to use all feature layers and hazard
rasters. `--limit-per-layer` changes the sample size. The seed determines both
the sample and the values, independently of Python's process hash seed.

For every feature in the selected layers, use `--all-features` instead of
`--limit-per-layer`. This uses database-side generation and compact ownership
intervals to handle full networks without keeping every result ID in memory.
Each coverage mode is reproducible with the same seed and options.

To discard **all existing damage and adaptation results** before generation,
add `--replace`. This empties all four result tables and their synthetic run
records, including results outside the selected layers/hazards. It preserves
feature records and raster/dataset configuration. Preview with `--dry-run` first.
Replacement and generation run in one transaction: a failure restores the old
results. Large replacements hold locks on result tables until they commit.

The command creates expected annual damage at protection standards 0 and 100,
return-period damage, NPV fixtures (15 times annual values), and three visibly
named synthetic adaptation options with positive costs. Larger samples include
zero and missing values. The first sampled feature in each layer acts as a
synthetic protector, including a self-protection result; the output lists its
ID. Full-network runs use one default protector per 100 features to keep
protected-feature responses manageable. Alternatively, repeat `--protector-id`
to use specified existing features.
Select a protector feature and switch to Protected Features to inspect its links.

Runs are named (`--name development` by default). Repeating the same ordinary
run is a no-op; `--replace` always regenerates. Without `--replace`, existing
result keys are skipped, never overwritten. New result IDs (or their exact
ownership intervals) are recorded transactionally in `synthetic_data_runs`, so
cleanup removes only that run's rows and any parameter sets it created that are
still unreferenced:

```bash
docker compose -f docker-compose.dev.yml exec django python manage.py seed_synthetic_results --name development --clear --dry-run
docker compose -f docker-compose.dev.yml exec django python manage.py seed_synthetic_results --name development --clear
```

Writes and cleanup require `DEBUG=True`; dry runs are read-only. The command
does not change dataset permissions. Different raster schemas (for example,
river GWL versus coastal SLR) can have no shared “All Hazards” scenario; select
an individual hazard in that case. Legacy RCP/year map values embedded in vector
tiles are not replaced by this command, whereas bulk-API GWL/SLR values use the
generated rows. Feature geometry, tile feature IDs, and the selected country
must already agree for map values and asset-list locations to agree.

### Run the frontend app in development mode

Start the app server (from the `frontend`  directory):

```bash
npm start
```

This should automatically open a browser tab. If not, open:

    firefox http://localhost:5173/

See `./deploy` directory for details.

#### Numeric scenario controls

Scenario controls use selects by default. Set `numericControl="slider"` on
`ModelParameterControls`, `DamageSourceControl`, or `FieldSpecControl` to render
finite numeric options as sliders, including GWL, SLR, and protection standards.
Sliders stop only at available catalogue values and preserve valid scenario
combinations. Categorical values and numeric strings remain selects; controls
with a single available value are disabled.
The network-layer damage panel enables slider mode for its numeric parameters.
It also shows a disabled return-period control at the maximum available for the
matching hazard rasters. Hazards with different return periods have separate
controls. This describes the displayed hazard maps; damage values remain
expected annual estimates.


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

# Pixel driller

Ingest raster layers and save their data as Zarr stacks, for use by the Django `pixel` app.

## Usage

### Ingest

Supplied rasters are ingested and saved in chunked Zarr format as a 'stack' for
rapid retrieval.

```bash
mkdir -p ../tileserver/stacks
python ingest.py /path/to/jamaica-infrastructure/processed_data/ ../tileserver/stacks
```

### Backup

To backup ingested stacks, run:

```bash
tar cvf $(date --iso-8601)_jamaica.infrastructureresilience.org_tileserver_stacks.tar tileserver/stacks
```

## Testing

First, create test fixtures (e.g. sample stacks):

```bash
pushd tests/fixtures
python make_fixtures.py
popd
```

To run the tests:

```bash
python -m unittest tests/test_*.py
```
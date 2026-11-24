# ADR 0002: Raster layer access

- Status: Accepted
- Date: 2026-11-24

## Context

Raster datasets need layer-specific presentation and access controls while
allowing multiple layers to use a common tile source. Raster keys are supplied
by callers, so authorizing a request requires considering the source database,
not only the requested key.

## Decision

Each raster layer references one raster tile source; multiple layers may share
that source. Its identity belongs to one dataset, whose access groups govern
the layer. A layer can be assigned to any dataset, including datasets used for
non-raster data. Labels, units, colours, and display order belong to the raster
layer.

Every layer using a raster database must have a dataset assignment, and the
requester must have access to every associated dataset. An unassigned layer
blocks tile and domain access to that entire database for all users, including
superusers, until it is assigned or moved. This applies across separate source
records pointing at the same database. Separate raster databases are required
when datasets need different access rights.

Unassigned layers and layers in inaccessible hazard datasets remain visible in
the hazard catalogue as disabled. Layers assigned to non-hazard datasets are
omitted from that catalogue. Raster metadata is served at
`/api/map/raster-layers`; tile and domain URLs use the layer ID.

## Consequences

Migration 0027 creates a raster layer for each existing dataset with a tile
source while preserving its ID and display settings. Administrators should
review these layers and move them into shared datasets as appropriate. Moving
a layer changes the set of datasets governing access to every layer that shares
its database; the effective access of the moved layer and its database peers may
change.

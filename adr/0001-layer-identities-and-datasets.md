# ADR 0001: Layer identities and datasets

- Status: Accepted
- Date: 2026-11-24

## Context

Feature and raster layers need stable identifiers, shared map ordering, and
dataset-based access control. Feature tree hierarchy and sidebar presentation
remain distinct concerns. Layers may be loaded before their datasets are ready.

## Decision

Each feature or raster layer has a one-to-one `LayerIdentity` whose primary key
is the layer ID. The identity links to at most one dataset and inherits that
dataset's access groups. Layers may remain unassigned during data preparation,
but unassigned layers are unavailable through the application. Layer saves
create an unassigned identity when needed; direct database inserts must create
the identity first. Deleting a layer leaves its identity available for review
or explicit deletion.

Feature and raster layers use one shared ID namespace. The database enforces
uniqueness, and migration 0031 reports existing collisions for resolution.
Layer IDs continue to identify vector tiles. Stacking order is shared across
feature and raster layers, with existing relative order retained for ties.
Feature and raster layers use a common display-order scale, while sidebar
sections and feature-tree hierarchy remain separate. Stacking order and display
order are independent fields. Feature layer display order orders linked
siblings in the tree.

Feature and result data endpoints expose only layers in datasets the signed-in
user can access. Unlinked layers are excluded; inaccessible feature and result
detail requests return 404, and aggregate lookups exclude inaccessible data.
Layer metadata catalogues can still list inaccessible or unassigned layers with
`has_access: false`; metadata detail requests return 403.

## Consequences

Dataset assignment is managed on the identity in Django admin; layer display
and ordering settings remain on the layer. Migration 0029 links matching layer
and dataset IDs and copies order values. `link_feature_layers` can perform the
matching for unassigned layers after import and reports remaining assignments.
The current ETL does not create identity records for new feature layers.

Migration 0026 links infrastructure leaves whose IDs match layer names and
warns about unmatched leaves. The one-to-one layer link is enforced by database
uniqueness and form validation. The rule that a node with children has no layer
is enforced by model and form validation, not by direct database writes.

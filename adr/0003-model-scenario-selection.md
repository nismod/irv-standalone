# ADR 0003: Model scenario selection

- Status: Accepted
- Date: 2026-11-24

## Context

Results can describe multiple hazards with different parameter schemas. The
map and asset list must expose combinations present in the data without
conflating parameter values or summing multiple scenarios for one hazard.

## Decision

Discover scenarios from result rows through
`GET /api/map/model-scenarios/{field_group}`, where `field_group` is
`damages_expected` or `adaptation`. The endpoint accepts repeated `layer`
filters, asset filters (`sector`, `subsector`, `asset_type`), and optional
`hazard`; adaptation may also be scoped by `protector_id`. Each row includes a
complete `parameters` object and fixed result dimensions such as protection
standard or adaptation option. Controls preserve these combinations and value
types.

“All Hazards” combines available parameters in the selected asset scope,
including schemas such as coastal SLR and river/surface GWL. Hazard selection
can also represent a subset of hazards. Shared parameter values and protection
standards must agree across hazards. Damage requests use the bulk attributes
API and sum exactly one selected scenario per accessible hazard.

For subsets or differing parameter schemas, `hazard_parameters` maps each
selected hazard to its parameter object while `parameters` contains combined
control values. Partial selections omit `hazard`; full selections use
`hazard: "all"`. Full selections with a shared parameter object may omit
`hazard_parameters`.

## Consequences

Scenario controls, totals, and matching raster layers follow the selected
hazards and parameter combinations. A shared “All Hazards” scenario is not
available when the selected hazards have incompatible values for a shared
parameter or protection standard; those hazards must be selected separately
or with a compatible subset.

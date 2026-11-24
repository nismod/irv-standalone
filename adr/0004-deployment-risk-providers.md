# ADR 0004: Deployment risk providers

- Status: Accepted
- Date: 2026-11-24

## Context

Countries run separate instances from a shared codebase. Their risk datasets
may differ in dimensions, measures, storage, and query behavior. The existing
map risk endpoints assume the schema used for Jamaica.

## Decision

Select the implementation of the risk endpoints per deployment using the
Django setting `RISK_PROVIDER`, a dotted path to a class with a no-argument
constructor. The default is `map.risk.jamaica.JamaicaRiskProvider`. The URL
configuration loads the provider at startup; changing it requires a restart.

The provider supplies these DRF view classes:

| Attribute | Endpoint |
| --- | --- |
| `feature_viewset` | `features` (including feature detail) |
| `adaptation_viewset` | `adaptation-cost-benefits` |
| `expected_damages_viewset` | `damages-expected` |
| `return_period_damages_viewset` | `damages-rp` |
| `scenarios_view` | `model-scenarios/<field_group>` |
| `sorted_features_view` | `features/sorted-by/<field_group>` |
| `protected_features_view` | `features/<protector_id>/protected-by` |
| `attribute_lookup_view` | `attributes/<field_group>` |

An implementation may subclass the default provider and replace individual
views, or supply all of them. Providers can use models and migrations in
additional installed Django apps and their own import commands.

## Consequences

Provider views must enforce feature-layer and hazard access permissions and
preserve the response contract expected by the frontend, or the deployment
must provide corresponding frontend changes. The existing map risk models and
migrations remain installed; selecting a provider does not remove their tables
or migrate existing data.

The default endpoints expose fixed Jamaica-shaped fields and dimensions. This
interface permits replacement of that behavior; it does not yet provide a
metadata-driven frontend or a shared generic risk query contract.

# Database entity relationship diagram

This diagram reflects the current Django model definitions in `irvapp/map/models/`, `irvapp/raster/models.py`, and `irvapp/content/models.py`. Django's built-in `auth.Group` is shown because datasets reference it. Unmanaged/external tables and implicit tree-query fields are omitted. Entity attributes are abbreviated to keep the diagram readable.

```mermaid
erDiagram
    LAYER_IDENTITY ||--o| FEATURE_LAYER : "identity (PK/FK)"
    LAYER_IDENTITY ||--o| RASTER_LAYER : "identity (PK/FK)"
    DATASET o|--o{ LAYER_IDENTITY : dataset
    RASTER_TILE_SOURCE ||--o{ RASTER_LAYER : tile_source
    FEATURE_LAYER ||--o{ FEATURE : layer
    FEATURE_LAYER o|--o| FEATURE_LAYER_STYLE : feature_layer
    INFRASTRUCTURE_NODE o|--o| FEATURE_LAYER : feature_layer
    INFRASTRUCTURE_NODE o|--o{ INFRASTRUCTURE_NODE : parent
    DATASET }o--o{ AUTH_GROUP : access_groups

    MODEL_PARAMETER_SET ||--o{ MODEL_PARAMETER : parameters
    FEATURE ||--o{ ADAPTATION_COST_BENEFIT : feature
    MODEL_PARAMETER_SET ||--o{ ADAPTATION_COST_BENEFIT : parameter_set
    FEATURE ||--o{ DAMAGES_EXPECTED : feature
    MODEL_PARAMETER_SET ||--o{ DAMAGES_EXPECTED : parameter_set
    FEATURE ||--o{ DAMAGES_RP : feature
    MODEL_PARAMETER_SET ||--o{ DAMAGES_RP : parameter_set

    PAGE ||--o{ MARKDOWN_BLOCK : page
    PAGE ||--o{ LOGO : page

    LAYER_IDENTITY {
        string id PK
        string kind
        string dataset_id
    }
    FEATURE_LAYER {
        string layer_name PK
        string identity_kind
        string sector
        string subsector
        string asset_type
        int stacking_order
        int display_order
    }
    RASTER_LAYER {
        string id PK
        string identity_kind
        bigint tile_source_id
        string label
        string quantity
        string unit
        string license
        string color_scheme
        json color_range
        int stacking_order
        int display_order
    }
    FEATURE {
        bigint id PK
        string string_id
        string layer
        string sublayer
        json properties
        geometry geom
    }
    DATASET {
        string id PK
        string label
        string group
        string license
    }
    AUTH_GROUP {
        int id PK
        string name
    }
    RASTER_TILE_SOURCE {
        bigint id PK
        string description
        json keys
        string database
        string path_template
    }
    INFRASTRUCTURE_NODE {
        string node_id PK
        string node_name
        string parent_id
        string feature_layer_id
    }
    MODEL_PARAMETER {
        bigint id PK
        bigint parameter_set_id
        string name
        json value
    }
    MODEL_PARAMETER_SET {
        bigint id PK
        string model_type
        text canonical_key
    }
    ADAPTATION_COST_BENEFIT {
        bigint id
        bigint parameter_set_id PK
        bigint feature_id PK
        string hazard PK
        string adaptation_name PK
        float adaptation_protection_level PK
        float adaptation_cost
    }
    DAMAGES_EXPECTED {
        bigint id
        bigint parameter_set_id PK
        bigint feature_id PK
        string hazard PK
        int protection_standard PK
        float ead_mean
    }
    DAMAGES_RP {
        bigint id
        bigint parameter_set_id PK
        bigint feature_id PK
        string hazard PK
        int rp PK
        float exposure
    }
    SYNTHETIC_DATA_RUN {
        string name PK
        datetime created_at
        json config
        json result_ids
        json parameter_set_ids
    }
    MAP_CONFIG {
        string config_name PK
        string config_value
        string config_type
    }
    FEATURE_LAYER_STYLE {
        string layer_id PK
        string feature_layer_id
        string label
        string style_type
        string color
        int min_zoom
    }
    PAGE {
        string name PK
        string title
        string background_image
        text background_credit
    }
    MARKDOWN_BLOCK {
        bigint id PK
        string page_id
        string slot
        string title
        text markdown
    }
    LOGO {
        bigint id PK
        string page_id
        string slot
        string name
        string image
        string link
        int height
        int position
    }
```

Notes: layer identities are shared IDs with one-to-one subtype rows; `identity_kind` is constrained to the corresponding subtype. Feature layer styles retain their original ID until a matching feature layer is available; linked IDs must match. Result tables use composite primary keys (shown with `PK` on each constituent) and also have unique sequence-backed `id` values. `ModelParameterSet` has a unique constraint on `(model_type, canonical_key)`; `ModelParameter` on `(parameter_set_id, name)`; `MarkdownBlock` on `(page_id, slot)`. `SyntheticDataRun` stores IDs in JSON, not relational foreign keys.

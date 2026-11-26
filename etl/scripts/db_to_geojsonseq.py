"""Write database features as GeoJSONSeq with stable vector tile IDs."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path("scripts").resolve()))
import django_runtime  # noqa: F401
from map.models import Feature


def feature_as_geojson(feature):
    # Damage values are obtained through the scenario-aware API. Embedding
    # them in tiles would collapse distinct parameter sets and protection levels.
    return {
        "type": "Feature",
        "id": feature.pk,
        "geometry": json.loads(feature.geom.geojson),
        "properties": {
            "uid": feature.pk,
            "asset_id": feature.properties.get("asset_id"),
            "asset_type": feature.properties.get("asset_type"),
        },
    }


if __name__ == "__main__":
    layer = snakemake.wildcards.layer
    with open(str(snakemake.output[0]), "w", encoding="utf-8") as output:
        for feature in Feature.objects.filter(layer_id=layer).order_by("pk").iterator(chunk_size=1000):
            output.write(json.dumps(feature_as_geojson(feature), ensure_ascii=False) + "\n")

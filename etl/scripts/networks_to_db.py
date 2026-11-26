"""Load network features from a single source file-layer to database."""

import fiona
import pandas

from pyproj import CRS, Transformer
from shapely.geometry import shape
from shapely.ops import transform
import sys
from pathlib import Path

sys.path.insert(0, str(Path("scripts").resolve()))
import django_runtime  # noqa: F401
from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from map.models import AdaptationCostBenefit, DamagesExpected, DamagesRp, Feature


def yield_features(layer, network_tilelayer, analysis_data_dir):
    """Read from file layer to modelled Features"""
    with fiona.open(
        get_network_layer_path(layer, analysis_data_dir),
        layer=layer.gpkg_layer,
    ) as src:
        from_crs = src.crs
        to_crs = CRS.from_epsg(4326)
        t = Transformer.from_crs(from_crs, to_crs, always_xy=True).transform

        def to_2d(x, y, z=None):
            return (x, y)

        rename = {
            layer.asset_id_column: "asset_id",
            layer.asset_type_column: "asset_type",
            layer.asset_min_cost_column: "cost_min",
            layer.asset_max_cost_column: "cost_max",
            layer.asset_mean_cost_column: "cost_mean",
            layer.asset_cost_unit_column: "cost_unit",
            layer.asset_reopen_cost_column: "cost_reopen",
            layer.asset_reopen_cost_unit_column: "cost_reopen_unit",
        }

        for feature in src:
            geom = transform(t, shape(feature["geometry"]))
            if geom.has_z:
                geom = transform(to_2d, geom)
            props = clean_props(feature["properties"], rename)
            # FIXME in the data
            if layer.ref == "transport_rail_edges":
                props["asset_type"] = "track"
            if layer.ref == "roads_nodes" and not props["asset_type"]:
                props["asset_type"] = "junction"
            tilelayer_details = get_tilelayer_by_asset_type(
                layer.ref, props, network_tilelayer
            )
            props["sector"] = tilelayer_details.sector
            props["subsector"] = tilelayer_details.subsector

            yield Feature(
                id=props["uid"],
                string_id=props["asset_id"],
                layer_id=tilelayer_details.layer,
                properties=props,
                geom=GEOSGeometry(geom.wkt, srid=4326),
            )


def clean_props(props, rename):
    clean = {}
    for k, v in props.items():
        if k in rename:
            clean[rename[k]] = v
        elif k in rename.values():
            clean[f"_{k}"] = v
        else:
            clean[k] = v
    return clean


def get_network_layer(
    layer_name,
    network_layers,
    network_layers_areal_protection,
):
    if not network_layers_areal_protection.empty:
        if set(network_layers.columns) == set(
            network_layers_areal_protection.columns
        ):
            network_layers = pandas.concat(
                [network_layers, network_layers_areal_protection],
                ignore_index=True,
            )
        else:
            raise ValueError(
                "network_layers_areal_protection could not be appended "
                "to network_layers. DataFrames have different fields"
            )
    try:
        return network_layers[network_layers.ref == layer_name].iloc[0]
    except IndexError as e:
        print(f"Could not find {layer_name} in network layers.")
        raise e


def get_network_layer_path(layer, analysis_data_dir):
    return f"{analysis_data_dir}/processed_data/networks_uids/{layer.path}"


def get_tilelayer_by_asset_type(layer_ref, props, network_tilelayers):
    try:
        return network_tilelayers[
            (network_tilelayers.asset_type == props["asset_type"])
            & (network_tilelayers.ref == layer_ref)
        ].iloc[0]
    except IndexError as e:
        print(f"Could not find {props['asset_type']} in tilelayers.")
        raise e


def get_tilelayers_by_network_source(network_source, network_tilelayers):
    try:
        return network_tilelayers[
            network_tilelayers.ref == network_source.ref
        ].layer
    except IndexError as e:
        print(f"Could not find {network_source} in tilelayers.")
        raise e


def reload_features(features, tilelayers):
    # Preserve existing feature IDs and their results. The whole source reload
    # rolls back on a malformed feature, collision, or unsafe removal.
    if not tilelayers:
        raise ValueError("No tile layers configured for this source")
    with transaction.atomic():
        seen = set()
        for feature in features:
            if feature.pk is None or feature.pk in seen:
                raise ValueError(f"Missing or duplicate feature UID: {feature.pk}")
            seen.add(feature.pk)
            existing = Feature.objects.filter(pk=feature.pk).first()
            if existing and existing.layer_id not in tilelayers:
                raise ValueError(f"Feature UID {feature.pk} already belongs to {existing.layer_id}")
            feature.save(force_insert=existing is None)
        if not seen:
            raise ValueError("Refusing to replace a feature layer with an empty source")
        removed = Feature.objects.filter(layer_id__in=tilelayers).exclude(pk__in=seen)
        removed_ids = removed.values_list("pk", flat=True)
        if (DamagesExpected.objects.filter(feature_id__in=removed_ids).exists()
                or DamagesRp.objects.filter(feature_id__in=removed_ids).exists()
                or AdaptationCostBenefit.objects.filter(feature_id__in=removed_ids).exists()
                or AdaptationCostBenefit.objects.filter(protector_feature_id__in=removed_ids).exists()):
            raise ValueError("Cannot remove features referenced by results or as protectors")
        removed.delete()
        print(f"Loaded {len(seen)} features")



if __name__ == "__main__":
    try:
        layer = snakemake.wildcards.layer
        output = snakemake.output
        analysis_data_dir = snakemake.config["analysis_data_dir"]

        network_layers = pandas.read_csv(snakemake.config["network_layers"])
        network_layers_areal_protection = pandas.read_csv(
            snakemake.config["network_layers_areal_protection"]
        )
        network_tilelayers = pandas.read_csv(
            snakemake.config["network_tilelayers"]
        )

    except NameError:
        print("Expected to run from snakemake")
        exit()

    layer = get_network_layer(
        layer,
        network_layers,
        network_layers_areal_protection,
    )
    tilelayers = list(
        get_tilelayers_by_network_source(layer, network_tilelayers)
    )

    reload_features(yield_features(layer, network_tilelayers, analysis_data_dir), tilelayers)

    with open(str(output), "w") as fh:
        fh.write("Loaded to database.\n\n")
        fh.write(
            "From:\n"
            f"{get_network_layer_path(layer, analysis_data_dir)}"
            f"|{layer.gpkg_layer}\n\n"
        )
        fh.write(f"Details:\n{str(layer)}\n")

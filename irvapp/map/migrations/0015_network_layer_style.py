from django.db import migrations, models


NETWORK_LAYER_STYLES = [
    {
        "layer_id": "elec_edges_high",
        "style_type": "line",
        "label": "Power Lines (High Voltage)",
        "color": "#eca926",
    },
    {
        "layer_id": "elec_edges_low",
        "style_type": "line",
        "label": "Power Lines (Low Voltage)",
        "color": "#f1d75c",
        "min_zoom": 11,
    },
    {
        "layer_id": "elec_nodes_diesel",
        "style_type": "square",
        "label": "Power Generation (Diesel)",
        "color": "#fdb1ab",
    },
    {
        "layer_id": "elec_nodes_gas",
        "style_type": "square",
        "label": "Power Generation (Gas)",
        "color": "#e0c8e1",
    },
    {
        "layer_id": "elec_nodes_hydro",
        "style_type": "square",
        "label": "Power Generation (Hydro)",
        "color": "#b5cae0",
    },
    {
        "layer_id": "elec_nodes_solar",
        "style_type": "square",
        "label": "Power Generation (Solar)",
        "color": "#ffd6a3",
    },
    {
        "layer_id": "elec_nodes_wind",
        "style_type": "square",
        "label": "Power Generation (Wind)",
        "color": "#cee8c2",
    },
    {
        "layer_id": "elec_nodes_pole",
        "style_type": "circle",
        "label": "Power Transmission (Poles)",
        "color": "#f1d75c",
        "min_zoom": 13,
    },
    {
        "layer_id": "elec_nodes_substation",
        "style_type": "circle",
        "label": "Power Transmission (Substations)",
        "color": "#eca926",
    },
    {
        "layer_id": "elec_nodes_demand",
        "style_type": "circle",
        "label": "Power Demand",
        "color": "#ff8c00",
        "min_zoom": 13,
    },
    {
        "layer_id": "rail_edges",
        "style_type": "line",
        "label": "Railways",
        "color": "#444",
    },
    {
        "layer_id": "rail_stations",
        "style_type": "circle",
        "label": "Stations",
        "color": "#444",
    },
    {
        "layer_id": "rail_junctions",
        "style_type": "diamond",
        "label": "Railway Junctions",
        "color": "#444",
    },
    {
        "layer_id": "road_edges_class_a",
        "style_type": "line",
        "label": "Roads (Class A)",
        "color": "#941339",
    },
    {
        "layer_id": "road_edges_class_b",
        "style_type": "line",
        "label": "Roads (Class B)",
        "color": "#cb3e4e",
    },
    {
        "layer_id": "road_edges_class_c",
        "style_type": "line",
        "label": "Roads (Class C)",
        "color": "#8471a8",
    },
    {
        "layer_id": "road_edges_motorway",
        "style_type": "line",
        "label": "Roads (Toll)",
        "color": "#487dbc",
    },
    {
        "layer_id": "road_edges_residential",
        "style_type": "line",
        "label": "Roads (Residential)",
        "color": "#b2afaa",
        "min_zoom": 10,
    },
    {
        "layer_id": "road_edges_unclassified",
        "style_type": "line",
        "label": "Roads (Unclassified)",
        "color": "#b2afaa",
        "min_zoom": 10,
    },
    {
        "layer_id": "road_bridges",
        "style_type": "diamond",
        "label": "Bridges",
        "color": "#941339",
    },
    {
        "layer_id": "airport_runways",
        "style_type": "polygon",
        "label": "Airports (Runway)",
        "color": "#d393d3",
    },
    {
        "layer_id": "airport_terminals",
        "style_type": "polygon",
        "label": "Airports (Terminal)",
        "color": "#b393d3",
    },
    {
        "layer_id": "port_areas_break",
        "style_type": "polygon",
        "label": "Ports (Break)",
        "color": "#b46666",
    },
    {
        "layer_id": "port_areas_container",
        "style_type": "polygon",
        "label": "Ports (Container)",
        "color": "#b4667a",
    },
    {
        "layer_id": "port_areas_industry",
        "style_type": "polygon",
        "label": "Ports (Industry)",
        "color": "#b47a66",
    },
    {
        "layer_id": "port_areas_silo",
        "style_type": "polygon",
        "label": "Ports (Silo)",
        "color": "#b48e66",
    },
    {
        "layer_id": "water_potable_edges",
        "style_type": "line",
        "label": "Water Supply Pipelines",
        "color": "#83B4FF",
    },
    {
        "layer_id": "water_potable_nodes_booster",
        "style_type": "inv-triangle",
        "label": "Water Supply (Booster Station)",
        "color": "#83B4FF",
    },
    {
        "layer_id": "water_potable_nodes_catchment",
        "style_type": "inv-triangle",
        "label": "Water Supply (Catchment)",
        "color": "#83B4FF",
    },
    {
        "layer_id": "water_potable_nodes_entombment",
        "style_type": "inv-triangle",
        "label": "Water Supply (Entombment)",
        "color": "#83B4FF",
    },
    {
        "layer_id": "water_potable_nodes_filter",
        "style_type": "inv-triangle",
        "label": "Water Supply (Filter Plant)",
        "color": "#83B4FF",
    },
    {
        "layer_id": "water_potable_nodes_intake",
        "style_type": "inv-triangle",
        "label": "Water Supply (Intake)",
        "color": "#83B4FF",
    },
    {
        "layer_id": "water_potable_nodes_well",
        "style_type": "inv-triangle",
        "label": "Water Supply (Production Well)",
        "color": "#83B4FF",
    },
    {
        "layer_id": "water_potable_nodes_pump",
        "style_type": "inv-triangle",
        "label": "Water Supply (Pump Station)",
        "color": "#83B4FF",
    },
    {
        "layer_id": "water_potable_nodes_relift",
        "style_type": "inv-triangle",
        "label": "Water Supply (Relift Station)",
        "color": "#83B4FF",
    },
    {
        "layer_id": "water_potable_nodes_reservoir",
        "style_type": "inv-triangle",
        "label": "Water Supply (Reservoir)",
        "color": "#83B4FF",
    },
    {
        "layer_id": "water_potable_nodes_river_source",
        "style_type": "inv-triangle",
        "label": "Water Supply (River Source)",
        "color": "#83B4FF",
    },
    {
        "layer_id": "water_potable_nodes_spring",
        "style_type": "inv-triangle",
        "label": "Water Supply (Spring)",
        "color": "#83B4FF",
    },
    {
        "layer_id": "water_potable_nodes_tank",
        "style_type": "inv-triangle",
        "label": "Water Supply (Storage Tank)",
        "color": "#83B4FF",
    },
    {
        "layer_id": "water_potable_nodes_sump",
        "style_type": "inv-triangle",
        "label": "Water Supply (Sump)",
        "color": "#83B4FF",
    },
    {
        "layer_id": "water_potable_nodes_tp",
        "style_type": "inv-triangle",
        "label": "Water Supply (Treatment Plant)",
        "color": "#83B4FF",
    },
    {
        "layer_id": "water_irrigation_edges",
        "style_type": "line",
        "label": "Irrigation Canals",
        "color": "#0091C1",
    },
    {
        "layer_id": "water_irrigation_nodes",
        "style_type": "inv-triangle",
        "label": "Irrigation facilities",
        "color": "#0091C1",
    },
    {
        "layer_id": "water_waste_sewer_gravity",
        "style_type": "line",
        "label": "Wastewater Pipelines (Gravity)",
        "color": "#4d49bc",
    },
    {
        "layer_id": "water_waste_sewer_pressure",
        "style_type": "line",
        "label": "Wastewater Pipelines (Pressure)",
        "color": "#4d49bc",
    },
    {
        "layer_id": "water_waste_nodes_sump",
        "style_type": "inv-triangle",
        "label": "Wastewater (Sump)",
        "color": "#4d49bc",
    },
    {
        "layer_id": "water_waste_nodes_pump",
        "style_type": "inv-triangle",
        "label": "Wastewater (Pump Station)",
        "color": "#4d49bc",
    },
    {
        "layer_id": "water_waste_nodes_relift",
        "style_type": "inv-triangle",
        "label": "Wastewater (Relift Station)",
        "color": "#4d49bc",
    },
    {
        "layer_id": "water_waste_nodes_wwtp",
        "style_type": "inv-triangle",
        "label": "Wastewater (Treament Plant)",
        "color": "#4d49bc",
    },
    {
        "layer_id": "buildings_commercial",
        "style_type": "polygon",
        "label": "Buildings (Commercial)",
        "color": "#f2808c",
        "min_zoom": 12,
    },
    {
        "layer_id": "buildings_industrial",
        "style_type": "polygon",
        "label": "Buildings (Industrial)",
        "color": "#cb97f4",
        "min_zoom": 12,
    },
    {
        "layer_id": "buildings_institutional",
        "style_type": "polygon",
        "label": "Buildings (Institutional)",
        "color": "#808cf2",
        "min_zoom": 12,
    },
    {
        "layer_id": "buildings_mixed",
        "style_type": "polygon",
        "label": "Buildings (Mixed Use)",
        "color": "#f09e69",
        "min_zoom": 12,
    },
    {
        "layer_id": "buildings_other",
        "style_type": "polygon",
        "label": "Buildings (Other)",
        "color": "#bfb4c2",
        "min_zoom": 12,
    },
    {
        "layer_id": "buildings_recreation",
        "style_type": "polygon",
        "label": "Buildings (Recreation)",
        "color": "#95e78b",
        "min_zoom": 12,
    },
    {
        "layer_id": "buildings_residential",
        "style_type": "polygon",
        "label": "Buildings (Residential)",
        "color": "#f2e680",
        "min_zoom": 12,
    },
    {
        "layer_id": "buildings_resort",
        "style_type": "polygon",
        "label": "Buildings (Resort)",
        "color": "#f9b2ea",
        "min_zoom": 12,
    },
    {
        "layer_id": "coast_nodes_cpf",
        "style_type": "polygon",
        "label": "Coastal defence",
        "color": "#e884e5",
    },
]


def populate_network_layer_styles(apps, schema_editor):
    NetworkLayerStyle = apps.get_model("map", "NetworkLayerStyle")
    for style in NETWORK_LAYER_STYLES:
        NetworkLayerStyle.objects.update_or_create(
            layer_id=style["layer_id"],
            defaults={
                "style_type": style["style_type"],
                "label": style["label"],
                "color": style["color"],
                "min_zoom": style.get("min_zoom"),
            },
        )


def clear_network_layer_styles(apps, schema_editor):
    NetworkLayerStyle = apps.get_model("map", "NetworkLayerStyle")
    NetworkLayerStyle.objects.filter(
        layer_id__in=[style["layer_id"] for style in NETWORK_LAYER_STYLES],
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("map", "0014_dataset_color_map_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="NetworkLayerStyle",
            fields=[
                ("layer_id", models.CharField(primary_key=True, serialize=False)),
                ("label", models.CharField()),
                ("style_type", models.CharField()),
                ("color", models.CharField(max_length=64)),
                ("min_zoom", models.IntegerField(blank=True, null=True)),
            ],
            options={
                "db_table": "network_layer_styles",
                "ordering": ["layer_id"],
            },
        ),
        migrations.RunPython(
            populate_network_layer_styles,
            reverse_code=clear_network_layer_styles,
        ),
    ]

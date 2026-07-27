import { makeConfig } from 'lib/helpers';
import {
  ScaleLevel,
  border,
  iconColor,
  iconSize,
  lineStyle,
  pointRadius,
  fillColor,
  strokeColor,
} from 'lib/deck/props/style';

import { infrastructureViewLayer } from './infrastructure-view-layer';
import { StyleParams, ViewLayer } from 'lib/data-map/view-layers';
import { dataColorMap } from 'lib/deck/props/color-map';
import { getAssetDataAccessor } from 'lib/data-map/layers/assets/data-access';
import { colorMap } from 'lib/color-map';
import type { NetworksMetadata } from './state/metadata';
import { iconType } from 'lib/map-shapes/deck-icon';

function withOpacity(color: number[], opacity: number) {
  return [...color.slice(0, 3), Math.round(opacity * 255)];
}

function infraStyle(layer: string, defaultStyle, styleParams: StyleParams) {
  if (styleParams?.colorMap) {
    const { fieldSpec, colorSpec } = styleParams.colorMap;
    return dataColorMap(getAssetDataAccessor(layer, fieldSpec), colorMap(colorSpec));
  }
  return defaultStyle;
}

function layerColor(networksMetadata: NetworksMetadata, layer: string) {
  return networksMetadata[layer]?.deck ?? [51, 51, 51];
}

function layerMinZoom(networksMetadata: NetworksMetadata, layer: string, fallback?: number) {
  return networksMetadata[layer]?.minZoom ?? fallback;
}

enum RoadClass {
  motorway = 'motorway',
  class_a = 'class_a',
  class_b = 'class_b',
  class_c = 'class_c',
  unclassified = 'unclassified',
  residential = 'residential',
}

const roadClassLookup = {
  road_edges_motorway: RoadClass.motorway,
  road_edges_class_a: RoadClass.class_a,
  road_edges_class_b: RoadClass.class_b,
  road_edges_class_c: RoadClass.class_c,
  road_edges_residential: RoadClass.residential,
  road_edges_unclassified: RoadClass.unclassified,
};

const roadLineSize: Record<RoadClass, ScaleLevel> = {
  [RoadClass.motorway]: 0,
  [RoadClass.class_a]: 0,
  [RoadClass.class_b]: 1,
  [RoadClass.class_c]: 2,
  [RoadClass.residential]: 2,
  [RoadClass.unclassified]: 2,
};
function roadsViewLayer(asset_id, networksMetadata: NetworksMetadata) {
  const roadClass = roadClassLookup[asset_id];
  return infrastructureViewLayer(asset_id, ({ zoom, styleParams }) => [
    { minZoom: layerMinZoom(networksMetadata, asset_id, 4) },
    strokeColor(infraStyle(asset_id, layerColor(networksMetadata, asset_id), styleParams)),
    lineStyle(zoom, roadLineSize[roadClass]),
  ]);
}

function potableNodesViewLayer(asset_id, networksMetadata: NetworksMetadata) {
  return infrastructureViewLayer(asset_id, ({ zoom, styleParams }) => [
    iconType('inv-triangle'),
    iconSize(zoom, 1),
    iconColor(infraStyle(asset_id, layerColor(networksMetadata, asset_id), styleParams)),
  ]);
}

function wastewaterNodesViewLayer(asset_id, networksMetadata: NetworksMetadata) {
  return infrastructureViewLayer(asset_id, ({ zoom, styleParams }) => [
    iconType('inv-triangle'),
    iconSize(zoom, 1),
    iconColor(infraStyle(asset_id, layerColor(networksMetadata, asset_id), styleParams)),
  ]);
}

export function getInfrastructureViewLayers(networksMetadata: NetworksMetadata) {
  return makeConfig<ViewLayer, string>([
    infrastructureViewLayer('elec_edges_high', ({ zoom, styleParams }) => [
      strokeColor(
        infraStyle('elec_edges_high', layerColor(networksMetadata, 'elec_edges_high'), styleParams),
      ),
      lineStyle(zoom, 1),
    ]),
    infrastructureViewLayer('elec_edges_low', ({ zoom, styleParams }) => [
      { minZoom: layerMinZoom(networksMetadata, 'elec_edges_low') },
      strokeColor(
        infraStyle('elec_edges_low', layerColor(networksMetadata, 'elec_edges_low'), styleParams),
      ),
      lineStyle(zoom, 2),
    ]),

    infrastructureViewLayer('elec_nodes_diesel', ({ zoom, styleParams }) => [
      iconType('square'),
      iconColor(
        infraStyle(
          'elec_nodes_diesel',
          layerColor(networksMetadata, 'elec_nodes_diesel'),
          styleParams,
        ),
      ),
      iconSize(zoom, 1),
    ]),
    infrastructureViewLayer('elec_nodes_gas', ({ zoom, styleParams }) => [
      iconType('square'),
      iconColor(
        infraStyle('elec_nodes_gas', layerColor(networksMetadata, 'elec_nodes_gas'), styleParams),
      ),
      iconSize(zoom, 1),
    ]),
    infrastructureViewLayer('elec_nodes_hydro', ({ zoom, styleParams }) => [
      iconType('square'),
      iconColor(
        infraStyle(
          'elec_nodes_hydro',
          layerColor(networksMetadata, 'elec_nodes_hydro'),
          styleParams,
        ),
      ),
      iconSize(zoom, 1),
    ]),
    infrastructureViewLayer('elec_nodes_solar', ({ zoom, styleParams }) => [
      iconType('square'),
      iconColor(
        infraStyle(
          'elec_nodes_solar',
          layerColor(networksMetadata, 'elec_nodes_solar'),
          styleParams,
        ),
      ),
      iconSize(zoom, 1),
    ]),
    infrastructureViewLayer('elec_nodes_wind', ({ zoom, styleParams }) => [
      iconType('square'),
      iconColor(
        infraStyle('elec_nodes_wind', layerColor(networksMetadata, 'elec_nodes_wind'), styleParams),
      ),
      iconSize(zoom, 1),
    ]),

    infrastructureViewLayer('elec_nodes_demand', ({ zoom, styleParams }) => [
      { minZoom: layerMinZoom(networksMetadata, 'elec_nodes_demand') },
      fillColor(
        infraStyle(
          'elec_nodes_demand',
          layerColor(networksMetadata, 'elec_nodes_demand'),
          styleParams,
        ),
      ),
      pointRadius(zoom, 3),
      border(),
    ]),
    infrastructureViewLayer('elec_nodes_pole', ({ zoom, styleParams }) => [
      { minZoom: layerMinZoom(networksMetadata, 'elec_nodes_pole') },
      fillColor(
        infraStyle('elec_nodes_pole', layerColor(networksMetadata, 'elec_nodes_pole'), styleParams),
      ),
      pointRadius(zoom, 3),
      border(),
    ]),
    infrastructureViewLayer('elec_nodes_substation', ({ zoom, styleParams }) => [
      border(),
      fillColor(
        infraStyle(
          'elec_nodes_substation',
          layerColor(networksMetadata, 'elec_nodes_substation'),
          styleParams,
        ),
      ),
      pointRadius(zoom, 1),
    ]),

    infrastructureViewLayer('rail_edges', ({ zoom, styleParams }) => [
      strokeColor(
        infraStyle('rail_edges', layerColor(networksMetadata, 'rail_edges'), styleParams),
      ),
      lineStyle(zoom, 1),
    ]),
    infrastructureViewLayer('rail_stations', ({ zoom, styleParams }) => [
      border(),
      fillColor(
        infraStyle('rail_stations', layerColor(networksMetadata, 'rail_stations'), styleParams),
      ),
      pointRadius(zoom, 1),
    ]),
    infrastructureViewLayer('rail_junctions', ({ zoom, styleParams }) => [
      iconType('diamond'),
      iconColor(
        infraStyle('rail_junctions', layerColor(networksMetadata, 'rail_junctions'), styleParams),
      ),
      iconSize(zoom, 2),
    ]),

    roadsViewLayer('road_edges_class_a', networksMetadata),
    roadsViewLayer('road_edges_class_b', networksMetadata),
    roadsViewLayer('road_edges_class_c', networksMetadata),
    roadsViewLayer('road_edges_motorway', networksMetadata),
    roadsViewLayer('road_edges_residential', networksMetadata),
    roadsViewLayer('road_edges_unclassified', networksMetadata),

    infrastructureViewLayer('road_bridges', ({ zoom, styleParams }) => [
      iconType('diamond'),
      iconColor(
        infraStyle('road_bridges', layerColor(networksMetadata, 'road_bridges'), styleParams),
      ),
      iconSize(zoom, 1),
    ]),
    infrastructureViewLayer('airport_runways', ({ zoom, styleParams }) => [
      zoom >= 10 && border(),
      fillColor(
        infraStyle('airport_runways', layerColor(networksMetadata, 'airport_runways'), styleParams),
      ),
    ]),
    infrastructureViewLayer('airport_terminals', ({ zoom, styleParams }) => [
      zoom >= 10 && border(),
      fillColor(
        infraStyle(
          'airport_terminals',
          layerColor(networksMetadata, 'airport_terminals'),
          styleParams,
        ),
      ),
    ]),
    infrastructureViewLayer('port_areas_break', ({ zoom, styleParams }) => [
      zoom >= 10 && border(),
      fillColor(
        infraStyle(
          'port_areas_break',
          layerColor(networksMetadata, 'port_areas_break'),
          styleParams,
        ),
      ),
    ]),
    infrastructureViewLayer('port_areas_container', ({ zoom, styleParams }) => [
      zoom >= 10 && border(),
      fillColor(
        infraStyle(
          'port_areas_container',
          layerColor(networksMetadata, 'port_areas_container'),
          styleParams,
        ),
      ),
    ]),
    infrastructureViewLayer('port_areas_industry', ({ zoom, styleParams }) => [
      zoom >= 10 && border(),
      fillColor(
        infraStyle(
          'port_areas_industry',
          layerColor(networksMetadata, 'port_areas_industry'),
          styleParams,
        ),
      ),
    ]),
    infrastructureViewLayer('port_areas_silo', ({ zoom, styleParams }) => [
      zoom >= 10 && border(),
      fillColor(
        infraStyle('port_areas_silo', layerColor(networksMetadata, 'port_areas_silo'), styleParams),
      ),
    ]),
    potableNodesViewLayer('water_potable_nodes_booster', networksMetadata),
    potableNodesViewLayer('water_potable_nodes_catchment', networksMetadata),
    potableNodesViewLayer('water_potable_nodes_entombment', networksMetadata),
    potableNodesViewLayer('water_potable_nodes_filter', networksMetadata),
    potableNodesViewLayer('water_potable_nodes_intake', networksMetadata),
    potableNodesViewLayer('water_potable_nodes_well', networksMetadata),
    potableNodesViewLayer('water_potable_nodes_pump', networksMetadata),
    potableNodesViewLayer('water_potable_nodes_relift', networksMetadata),
    potableNodesViewLayer('water_potable_nodes_reservoir', networksMetadata),
    potableNodesViewLayer('water_potable_nodes_river_source', networksMetadata),
    potableNodesViewLayer('water_potable_nodes_spring', networksMetadata),
    potableNodesViewLayer('water_potable_nodes_tank', networksMetadata),
    potableNodesViewLayer('water_potable_nodes_sump', networksMetadata),
    potableNodesViewLayer('water_potable_nodes_tp', networksMetadata),

    infrastructureViewLayer('water_potable_edges', ({ zoom, styleParams }) => [
      lineStyle(zoom),
      strokeColor(
        infraStyle(
          'water_potable_edges',
          layerColor(networksMetadata, 'water_potable_edges'),
          styleParams,
        ),
      ),
    ]),
    infrastructureViewLayer('water_irrigation_edges', ({ zoom, styleParams }) => [
      lineStyle(zoom),
      strokeColor(
        infraStyle(
          'water_irrigation_edges',
          layerColor(networksMetadata, 'water_irrigation_edges'),
          styleParams,
        ),
      ),
    ]),
    infrastructureViewLayer('water_irrigation_nodes', ({ zoom, styleParams }) => [
      iconType('inv-triangle'),
      iconSize(zoom, 1),
      iconColor(
        infraStyle(
          'water_irrigation_nodes',
          layerColor(networksMetadata, 'water_irrigation_nodes'),
          styleParams,
        ),
      ),
    ]),
    infrastructureViewLayer('water_waste_sewer_gravity', ({ zoom, styleParams }) => [
      lineStyle(zoom),
      strokeColor(
        infraStyle(
          'water_waste_sewer_gravity',
          layerColor(networksMetadata, 'water_waste_sewer_gravity'),
          styleParams,
        ),
      ),
    ]),
    infrastructureViewLayer('water_waste_sewer_pressure', ({ zoom, styleParams }) => [
      lineStyle(zoom),
      strokeColor(
        infraStyle(
          'water_waste_sewer_pressure',
          layerColor(networksMetadata, 'water_waste_sewer_pressure'),
          styleParams,
        ),
      ),
    ]),
    wastewaterNodesViewLayer('water_waste_nodes_sump', networksMetadata),
    wastewaterNodesViewLayer('water_waste_nodes_pump', networksMetadata),
    wastewaterNodesViewLayer('water_waste_nodes_relift', networksMetadata),
    wastewaterNodesViewLayer('water_waste_nodes_wwtp', networksMetadata),
    infrastructureViewLayer('coast_nodes_cpf', ({ zoom, styleParams }) => [
      fillColor(
        infraStyle(
          'coast_nodes_cpf',
          withOpacity(layerColor(networksMetadata, 'coast_nodes_cpf'), 0.2),
          styleParams,
        ),
      ),
      strokeColor(
        infraStyle('coast_nodes_cpf', layerColor(networksMetadata, 'coast_nodes_cpf'), styleParams),
      ),
      lineStyle(zoom, 1),
    ]),
  ]);
}

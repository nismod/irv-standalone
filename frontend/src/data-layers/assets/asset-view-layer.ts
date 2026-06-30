import { createElement } from 'react';
import { useAtomValue } from 'jotai';

import { StyleParams, ViewLayer, ViewLayerDataAccessFunction } from 'lib/data-map/view-layers';
import { VectorTarget } from 'lib/data-map/types';
import { assetViewLayer as baseAssetViewLayer } from 'lib/data-map/layers/assets/asset-view-layer';
import { VectorLegend } from 'lib/map/legend/VectorLegend';
import { hazardsMetadataState } from 'data-layers/hazards/state/metadata';

import { getAssetDataFormats, getAssetLegendDataFormats } from './data-formats';
import { AssetHoverDescription } from './AssetHoverDescription';

interface ViewLayerMetadata {
  group: string;
  spatialType: string;
  interactionGroup: string;
}

function AssetLegend({ viewLayer }: { viewLayer: ViewLayer }) {
  const hazardsMetadata = useAtomValue(hazardsMetadataState);
  const { colorMap } = viewLayer.styleParams;
  const legendFormatConfig = getAssetLegendDataFormats(colorMap.fieldSpec, hazardsMetadata);

  return createElement(VectorLegend, { colorMap, legendFormatConfig });
}

export function assetViewLayer(
  assetId: string,
  metadata: ViewLayerMetadata,
  selectionPolygonOffset: number,
  customFn: ({ zoom, styleParams }: { zoom: number; styleParams?: StyleParams }) => object[],
  customDataAccessFn: ViewLayerDataAccessFunction,
): ViewLayer {
  const baseLayer = baseAssetViewLayer(
    assetId,
    metadata,
    selectionPolygonOffset,
    customFn,
    customDataAccessFn,
  );
  baseLayer.dataFormatsFn = getAssetDataFormats;
  baseLayer.renderLegend = function () {
    const { colorMap } = this.styleParams;
    const key = `${colorMap.fieldSpec.fieldGroup}-${colorMap.fieldSpec.field}`;

    return createElement(AssetLegend, { key, viewLayer: this });
  };
  baseLayer.renderTooltip = function ({ target }: { target: VectorTarget }) {
    return createElement(AssetHoverDescription, { key: this.id, target, viewLayer: this });
  };
  return baseLayer;
}

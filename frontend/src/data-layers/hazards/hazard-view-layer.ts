import { createElement } from 'react';

import { rasterTileLayer } from 'lib/deck/layers/raster-tile-layer';
import { ViewLayer } from 'lib/data-map/view-layers';
import { RasterTarget } from 'lib/data-map/types';
import { type Dataset } from 'lib/api-client';

import { HazardLegend } from './HazardLegend';
import { HazardHoverDescription } from './HazardHoverDescription';
import { HAZARD_SOURCE } from './source';
import { getHazardColorSpec } from './state/metadata';
import { type HazardParams } from './state/data-selection';

export function getHazardId(hazardType: string, hazardParams: HazardParams) {
  const serialisedParams = Object.entries(hazardParams)
    .filter(([, value]) => value != null)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, value]) => `${key}_${value}`)
    .join('__');

  return [hazardType, serialisedParams].filter(Boolean).join('__');
}

export function hazardViewLayer(
  hazardType: string,
  hazardParams: HazardParams,
  sourceMetadata?: { keys: string[] | null; fixedValues: Record<string, string | null> },
  dataset?: Dataset,
): ViewLayer {
  const magFilter = ['cyclone', 'storm'].includes(hazardType) ? 'nearest' : 'linear';
  const deckId = getHazardId(hazardType, hazardParams);

  return {
    id: hazardType,
    group: 'hazards',
    spatialType: 'raster',
    interactionGroup: 'hazards',
    params: { hazardType, hazardParams },
    fn: ({ deckProps }) => {
      const { scheme, range } = getHazardColorSpec(dataset);

      return rasterTileLayer(
        {
          textureParameters: {
            magFilter,
          },
          opacity: ['storm', 'cyclone'].includes(hazardType) ? 0.6 : 1,
        },
        deckProps,
        {
          id: `${hazardType}@${deckId}`, // follow the convention viewLayerId@deckLayerId
          data: HAZARD_SOURCE.getDataUrl({ hazardType, hazardParams, sourceMetadata }, { scheme, range }),
          refinementStrategy: 'no-overlap',
        },
      );
    },
    renderLegend() {
      return createElement(HazardLegend, {
        key: hazardType,
        viewLayer: this,
      });
    },
    renderTooltip({ target }: { target: RasterTarget }) {
      return createElement(HazardHoverDescription, { key: this.id, target, viewLayer: this });
    },
  };
}

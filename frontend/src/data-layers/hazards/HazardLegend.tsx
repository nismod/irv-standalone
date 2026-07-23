import { FC } from 'react';
import { useAtomValue } from 'jotai';

import { RasterLegend } from 'lib/map/legend/RasterLegend';
import { ViewLayer } from 'lib/data-map/view-layers';

import { getHazardColorSpec, hazardsMetadataState } from './state/metadata';

export const HazardLegend: FC<{ viewLayer: ViewLayer }> = ({ viewLayer }) => {
  const HAZARDS_METADATA = useAtomValue(hazardsMetadataState);
  const { id } = viewLayer;
  if (!HAZARDS_METADATA[id]) {
    return null;
  }
  const dataset = HAZARDS_METADATA[id];
  const { label, unit } = dataset;
  const { scheme, range } = getHazardColorSpec(dataset);
  return <RasterLegend label={label} dataUnit={unit} scheme={scheme} range={range} />;
};

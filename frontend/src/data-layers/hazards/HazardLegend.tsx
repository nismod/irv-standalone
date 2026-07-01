import { FC } from 'react';
import { useAtomValue } from 'jotai';

import { RasterLegend } from 'lib/map/legend/RasterLegend';
import { ViewLayer } from 'lib/data-map/view-layers';

import * as HAZARD_COLOR_MAPS from './color-maps';
import { hazardsMetadataState } from './state/metadata';

export const HazardLegend: FC<{ viewLayer: ViewLayer }> = ({ viewLayer }) => {
  const HAZARDS_METADATA = useAtomValue(hazardsMetadataState);
  const { id } = viewLayer;
  if (!HAZARDS_METADATA[id]) {
    return null;
  }
  const { label, unit } = HAZARDS_METADATA[id];
  const { scheme, range } = HAZARD_COLOR_MAPS[id];
  return <RasterLegend label={label} dataUnit={unit} scheme={scheme} range={range} />;
};

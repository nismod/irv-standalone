import { FC } from 'react';
import { useAtomValue } from 'jotai';

import { RasterHoverDescription } from 'lib/data-map/types';
import { RasterHoverDescription as RasterTooltip } from 'lib/map/tooltip/content/RasterHoverDescription';

import * as HAZARD_COLOR_MAPS from './color-maps';
import { hazardsMetadataState } from './state/metadata';

export const HazardHoverDescription: FC<RasterHoverDescription> = ({ target, viewLayer }) => {
  const HAZARDS_METADATA = useAtomValue(hazardsMetadataState);
  if (!HAZARDS_METADATA[viewLayer.id]) {
    return null;
  }
  const { label, unit } = HAZARDS_METADATA[viewLayer.id];
  const { scheme, range } = HAZARD_COLOR_MAPS[viewLayer.id];
  return (
    <RasterTooltip
      color={target.color}
      label={label}
      dataUnit={unit}
      scheme={scheme}
      range={range}
      type={viewLayer.id === 'storm' ? 'years' : undefined}
    />
  );
};

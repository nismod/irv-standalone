import { FC } from 'react';
import { useAtomValue } from 'jotai';

import { RasterHoverDescription } from 'lib/data-map/types';
import { RasterHoverDescription as RasterTooltip } from 'lib/map/tooltip/content/RasterHoverDescription';

import { getHazardColorSpec, hazardsMetadataState } from './state/metadata';

export const HazardHoverDescription: FC<RasterHoverDescription> = ({ target, viewLayer }) => {
  const HAZARDS_METADATA = useAtomValue(hazardsMetadataState);
  if (!HAZARDS_METADATA[viewLayer.id]) {
    return null;
  }
  const dataset = HAZARDS_METADATA[viewLayer.id];
  const { label, unit } = dataset;
  const { scheme, range } = getHazardColorSpec(dataset);
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

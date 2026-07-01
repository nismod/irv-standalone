import { FC } from 'react';
import { useAtomValue } from 'jotai';

import { RasterHoverDescription } from 'lib/data-map/types';
import { RasterHoverDescription as RasterTooltip } from 'lib/map/tooltip/content/RasterHoverDescription';

import * as RISKS_COLOR_MAPS from './color-maps';
import { risksMetadataState } from './state/metadata';

export const RiskHoverDescription: FC<RasterHoverDescription> = ({ target, viewLayer }) => {
  const RISKS_METADATA = useAtomValue(risksMetadataState);
  if (!RISKS_METADATA[viewLayer.id]) {
    return null;
  }
  const { label, dataUnit, format } = RISKS_METADATA[viewLayer.id];
  const { scheme, range } = RISKS_COLOR_MAPS[viewLayer.id];
  return (
    <RasterTooltip
      color={target.color}
      label={label}
      dataUnit={dataUnit}
      scheme={scheme}
      range={range}
      type={format}
    />
  );
};

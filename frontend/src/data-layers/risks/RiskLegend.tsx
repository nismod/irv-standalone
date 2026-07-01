import { FC } from 'react';
import { useAtomValue } from 'jotai';

import { RasterLegend } from 'lib/map/legend/RasterLegend';
import { ViewLayer } from 'lib/data-map/view-layers';

import * as RISKS_COLOR_MAPS from './color-maps';
import { risksMetadataState } from './state/metadata';

export const RiskLegend: FC<{ viewLayer: ViewLayer }> = ({ viewLayer }) => {
  const RISKS_METADATA = useAtomValue(risksMetadataState);
  const { id } = viewLayer;
  if (!RISKS_METADATA[id]) {
    return null;
  }
  const { label, dataUnit, format } = RISKS_METADATA[id];
  const { scheme, range } = RISKS_COLOR_MAPS[id];
  return (
    <RasterLegend label={label} dataUnit={dataUnit} scheme={scheme} range={range} type={format} />
  );
};

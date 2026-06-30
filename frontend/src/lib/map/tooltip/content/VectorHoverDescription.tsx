import { Typography } from '@mui/material';
import { FC } from 'react';

import { DataItem } from '../detail-components';
import { VectorTarget } from 'lib/data-map/types';
import { DataDescription } from '../DataDescription';
import { ColorBox } from './ColorBox';
import { LayerMetadata, ViewLayer } from 'lib/data-map/view-layers';

type VectorHoverDescriptionProps = {
  viewLayer: ViewLayer;
  feature: VectorTarget['feature'];
  title: string;
  color: string;
  metadata?: LayerMetadata;
};
export const VectorHoverDescription: FC<VectorHoverDescriptionProps> = ({
  title,
  color = '#ccc',
  viewLayer,
  feature,
  metadata,
}) => {
  const { colorMap } = viewLayer.styleParams ?? {};

  const isDataMapped = colorMap != null;

  return (
    <>
      <Typography variant="body2">
        <ColorBox color={color} empty={isDataMapped} />
        {title}
      </Typography>

      <DataItem label="ID" value={`${feature.properties.asset_id}`} />
      {colorMap && (
        <DataDescription
          viewLayer={viewLayer}
          feature={feature}
          colorMap={colorMap}
          metadata={metadata}
        />
      )}
    </>
  );
};

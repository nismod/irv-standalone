import { FC } from 'react';
import { useAtomValue } from 'jotai';

import { VectorHoverDescription } from 'lib/data-map/types';
import { VectorHoverDescription as VectorTooltip } from 'lib/map/tooltip/content/VectorHoverDescription';
import { networksMetadataState } from 'data-layers/networks/state/metadata';
import { hazardsMetadataState } from 'data-layers/hazards/state/metadata';

export const AssetHoverDescription: FC<VectorHoverDescription> = ({ target, viewLayer }) => {
  const hazardsMetadata = useAtomValue(hazardsMetadataState);
  const networksMetadata = useAtomValue(networksMetadataState);
  const { assetId } = (viewLayer.params ?? {}) as { assetId: string };
  const { label: title = assetId, color = '#ccc' } = networksMetadata[assetId] ?? {};
  return (
    <VectorTooltip
      viewLayer={viewLayer}
      feature={target.feature}
      title={title}
      color={color}
      metadata={hazardsMetadata}
    />
  );
};

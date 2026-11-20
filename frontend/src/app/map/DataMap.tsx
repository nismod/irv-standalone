import { FC, useEffect, useMemo } from 'react';
import { useAtomValue, useSetAtom } from 'jotai';

import { interactionGroupsState } from 'app/state/layers/interaction-groups';
import { viewLayerConfigs } from 'app/state/layers/view-layers';

import { DataMap } from 'lib/data-map/DataMap';
import { viewLayersFlatState } from 'lib/state/layers/view-layers';

import { backgroundState, showLabelsState } from './layers/layers-state';
import { useBasemapStyle } from './use-basemap-style';
import { flattenConfig } from 'lib/nested-config/flatten-config';
import { orderLayersByStacking } from 'lib/data-map/layer-order';
import { networkFeatureLayersMetadataState } from 'data-layers/networks/state/metadata';
import { rasterLayersMetadataState } from 'data-layers/hazards/state/metadata';

export const DataMapContainer: FC = () => {
  const background = useAtomValue(backgroundState);
  const showLabels = useAtomValue(showLabelsState);
  const viewLayers = useAtomValue(viewLayerConfigs);
  const featureLayers = useAtomValue(networkFeatureLayersMetadataState);
  const rasterLayers = useAtomValue(rasterLayersMetadataState);
  const setViewLayersFlat = useSetAtom(viewLayersFlatState);
  const { firstLabelId } = useBasemapStyle(background, showLabels);
  const interactionGroups = useAtomValue(interactionGroupsState);
  const flattenedViewLayers = useMemo(
    () => orderLayersByStacking(flattenConfig(viewLayers), { ...featureLayers, ...rasterLayers }),
    [viewLayers, featureLayers, rasterLayers],
  );

  useEffect(() => {
    setViewLayersFlat(flattenedViewLayers);
  }, [flattenedViewLayers, setViewLayersFlat]);

  return (
    <DataMap
      firstLabelId={firstLabelId}
      interactionGroups={interactionGroups}
      viewLayers={flattenedViewLayers}
    />
  );
};

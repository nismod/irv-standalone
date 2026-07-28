import { Box } from '@mui/system';
import { Alert } from '@mui/material';
import { FC, type ComponentProps } from 'react';
import { useAtom, useAtomValue, useSetAtom } from 'jotai';

import { CheckboxTree, recalculateCheckboxStates } from 'lib/controls/checkbox-tree/CheckboxTree';
import { useUpdateDataParam } from 'lib/state/data-params';

import { LayerLabel } from 'lib/sidebar/ui/LayerLabel';

import {
  networkTreeHierarchyState,
  networkSelectionState,
  networkTreeCheckboxState,
  networkTreeConfigState,
  networkTreeExpandedState,
  disabledNetworkNodeIdsState,
} from '../state/data-selection';
import { networksMetadataState } from '../state/metadata';
import { showAdaptationsState, showProtectorFeaturesState } from '../state/layer';

import { protectedFeatureLayersState } from 'lib/state/protected-features';
import { getAssetLayerDefinition, getLeafNodeIdsForLayerIds } from '../layer-registry';

/**
 * Set the checkbox tree state to true for protected feature layers.
 * @param checkBoxState network checkbox tree state.
 */
function useSyncProtectedFeatureLayers() {
  const networkTreeConfig = useAtomValue(networkTreeConfigState);
  const prevLayers = new Set(useAtomValue(networkSelectionState));
  const allLayerIds = new Set(
    Object.values(networkTreeConfig.nodes)
      .filter((n) => !!n.url)
      .map((n) => n.layerId)
      .filter((layerId): layerId is string => layerId !== undefined),
  );

  const showProtectorFeatureLayers = useAtomValue(showProtectorFeaturesState);
  const protectorFeatureLayers = showProtectorFeatureLayers
    ? new Set(['coast_nodes_cpf'])
    : new Set();

  const protectedFeatureLayers = useAtomValue(protectedFeatureLayersState);

  const setCheckboxState = useSetAtom(networkTreeCheckboxState);

  const showLayerIds = protectedFeatureLayers.union(protectorFeatureLayers).intersection(allLayerIds);
  const showLayers = new Set(getLeafNodeIdsForLayerIds(networkTreeConfig, showLayerIds));

  const doUpdate =
    showProtectorFeatureLayers && showLayers.symmetricDifference(prevLayers).size !== 0;

  if (doUpdate) {
    const newState = {
      indeterminate: {},
      checked: {},
    };
    prevLayers.forEach((layer: string) => {
      newState.checked[layer] = false;
    });
    showLayers.forEach((layer: string) => {
      newState.checked[layer] = true;
    });
    const resolvedTreeState = recalculateCheckboxStates(newState, networkTreeConfig);
    setCheckboxState(resolvedTreeState);
  }
}

/**
 * Sync adaptation parameters to the infrastructure checkbox tree, so that
 * selected adaptation sector etc. change when the selected infrastructure
 * layers change.
 * @param checkboxState infrastructure checkbox tree state.
 */
function useSyncAdaptationParameters(checkboxState) {
  const networkTreeConfig = useAtomValue(networkTreeConfigState);
  const updateSector = useUpdateDataParam('adaptation', 'sector');
  const updateSubsector = useUpdateDataParam('adaptation', 'subsector');
  const updateAssetType = useUpdateDataParam('adaptation', 'asset_type');
  const selectedNodeIds = Object.keys(checkboxState.checked).filter(
    (id) =>
      checkboxState.checked[id] &&
      networkTreeConfig.nodes[id] &&
      !networkTreeConfig.nodes[id].children,
  );
  const selectedLayerIds = selectedNodeIds
    .map((nodeId) => networkTreeConfig.nodes[nodeId].layerId)
    .filter((layerId): layerId is string => layerId !== undefined);
  const adaptationLayer = selectedLayerIds.map(getAssetLayerDefinition).find(Boolean);
  if (adaptationLayer) {
    const { sector, subsector, asset_type } = adaptationLayer;
    updateSector(sector);
    updateSubsector(subsector);
    updateAssetType(asset_type);
  }
}

function NodeLabel({
  node,
  checked,
  layerLabelProps,
}: {
  node;
  checked: boolean;
  layerLabelProps?: Omit<ComponentProps<typeof LayerLabel>, 'label' | 'visible'>;
}) {
  return node.children || !layerLabelProps ? (
    node.label
  ) : (
    <LayerLabel {...layerLabelProps} label={node.label} visible={checked} />
  );
}

export const NetworkControl: FC = () => {
  const networkHierarchy = useAtomValue(networkTreeHierarchyState);
  const networkTreeConfig = useAtomValue(networkTreeConfigState);
  const [checkboxState, setCheckboxState] = useAtom(networkTreeCheckboxState);
  const [expanded, setExpanded] = useAtom(networkTreeExpandedState);
  const networksMetadata = useAtomValue(networksMetadataState);
  const disabledNodeIds = useAtomValue(disabledNetworkNodeIdsState);

  const showAdaptations = useAtomValue(showAdaptationsState);
  const showProtectorFeatureLayers = useAtomValue(showProtectorFeaturesState);
  const disableCheck = showAdaptations || showProtectorFeatureLayers;

  useSyncAdaptationParameters(checkboxState);
  useSyncProtectedFeatureLayers();

  return (
    <>
      {disableCheck ? (
        <Box my={1}>
          <Alert severity="info">
            Infrastructure layers are currently following the{' '}
            {showAdaptations ? 'Adaptation Options' : 'Protected Features'} selection
          </Alert>
        </Box>
      ) : null}
      <CheckboxTree
        nodes={networkHierarchy}
        config={networkTreeConfig}
        getLabel={(node, checked) => (
          <NodeLabel
            node={node}
            checked={checked}
            layerLabelProps={networksMetadata[node.layerId ?? node.id]}
          />
        )}
        checkboxState={checkboxState}
        onCheckboxState={setCheckboxState}
        expanded={expanded}
        onExpanded={setExpanded}
        disableCheck={disableCheck}
        disabledNodeIds={disabledNodeIds}
      />
    </>
  );
};

import assetLayerRegistry from 'app/config/sidebar/adaptation-sector-layers.json';
import { CheckboxTreeConfig } from 'lib/controls/checkbox-tree/CheckboxTree';

export interface AssetLayerSelector {
  sector?: string;
  subsector?: string;
  asset_type?: string;
}

export interface AssetLayerRegistryEntry extends Required<AssetLayerSelector> {
  layer_name: string;
}

interface InfrastructureNodeLike {
  node_id: string;
  layer_name?: string;
  render_layer_id?: string;
}

export const assetLayerDefinitions = assetLayerRegistry as AssetLayerRegistryEntry[];

export function resolveAssetLayerIds(selector: AssetLayerSelector) {
  return assetLayerDefinitions
    .filter(
      (definition) =>
        (selector.sector === undefined || definition.sector === selector.sector) &&
        (selector.subsector === undefined || definition.subsector === selector.subsector) &&
        (selector.asset_type === undefined || definition.asset_type === selector.asset_type),
    )
    .map((definition) => definition.layer_name.trim());
}

export function getAssetLayerDefinition(layerId: string) {
  return assetLayerDefinitions.find((definition) => definition.layer_name.trim() === layerId);
}

export function resolveInfrastructureNodeLayerId(node: InfrastructureNodeLike) {
  return (node.render_layer_id ?? node.layer_name ?? node.node_id).trim();
}

export function getLeafNodeIdsForLayerIds<T extends { layerId?: string }>(
  config: CheckboxTreeConfig<T>,
  layerIds: Iterable<string>,
) {
  const layerIdSet = new Set(layerIds);
  return Object.values(config.nodes)
    .filter((node) => !node.children && node.layerId && layerIdSet.has(node.layerId))
    .map((node) => node.id);
}

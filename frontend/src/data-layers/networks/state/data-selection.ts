import mapValues from 'lodash/mapValues';
import { atom } from 'jotai';
import { unwrap } from 'jotai/utils';

import {
  buildTreeConfig,
  recalculateCheckboxStates,
  CheckboxTreeState,
} from 'lib/controls/checkbox-tree/CheckboxTree';
import { sectionStyleValueState } from 'lib/state/sections';
import { STORAGE_PREFIX, atomWithQueryParams, setUrlParam } from 'lib/state/map-view/map-url';

import { type InfrastructureNode, mapInfrastructureTreeList } from 'lib/api-client';
import { dfs, TreeNode } from 'lib/controls/checkbox-tree/tree-node';
import { resolveInfrastructureNodeLayerId } from '../layer-registry';
import { networkDatasetsMetadataState } from './metadata';

interface NetworkLayerData {
  label: string;
  url?: string;
  layerId?: string;
}


async function fetchInfrastructureNodes(): Promise<InfrastructureNode[]> {
  try {
    const { data, error } = await mapInfrastructureTreeList({
      baseUrl: '/api',
      credentials: 'include',
    });
    if (error) {
      throw new Error(`Failed to fetch infrastructure tree: ${JSON.stringify(error)}`);
    }
    if (!data?.results) {
      throw new Error('No results in infrastructure tree response');
    }
    return data.results;
  } catch (error) {
    console.error('Error fetching infrastructure tree:', error);
    return [];
  }
}

function buildHierarchyFromNodes(
  nodes: InfrastructureNode[],
  leafIndex = { value: 0 },
): TreeNode<NetworkLayerData>[] {
  return nodes.map((node) => {
    const treeNode: TreeNode<NetworkLayerData> = {
      id: node.node_id,
      label: node.node_name,
    };
    if (node.children.length > 0) {
      treeNode.children = buildHierarchyFromNodes(node.children, leafIndex);
    } else {
      leafIndex.value++;
      const nodeUrl = leafIndex.value.toString(16).padStart(2, '0'); // 2-digit hex string.
      treeNode.url = nodeUrl;
      treeNode.layerId = resolveInfrastructureNodeLayerId(node);
    }
    return treeNode;
  });
}

export const networkTreeExpandedState = atom<string[]>([]);

const networkTreeHierarchyQuery = atom(async () => {
  const networkTreeNodes = await fetchInfrastructureNodes();
  return buildHierarchyFromNodes(networkTreeNodes);
});

export const networkTreeHierarchyState = unwrap(
  networkTreeHierarchyQuery,
  (prev) => prev ?? [],
);

export const networkTreeConfigState = atom((get) => {
  const networkTreeHierarchy = get(networkTreeHierarchyState);
  return buildTreeConfig(networkTreeHierarchy);
});

export const disabledNetworkNodeIdsState = atom<Set<string>>((get) => {
  const networkTreeConfig = get(networkTreeConfigState);
  const datasets = get(networkDatasetsMetadataState);
  const disabledNodeIds = new Set<string>();

  networkTreeConfig.roots.forEach((root) => {
    dfs(
      root,
      (node) => {
        if (!node.children) {
          if (node.layerId && datasets[node.layerId]?.has_access === false) {
            disabledNodeIds.add(node.id);
          }
          return;
        }

        if (
          node.children.length > 0 &&
          node.children.every((child) => disabledNodeIds.has(child.id))
        ) {
          disabledNodeIds.add(node.id);
        }
      },
      false,
      'post',
    );
  });

  return disabledNodeIds;
});

const networkTreeUrlState = atom((get) => {
  const networkTreeConfig = get(networkTreeConfigState);
  return mapValues(networkTreeConfig.nodes, node => node.url);
});
const networkTreeIdState = atom((get) => {
  const networkTreeURLs = get(networkTreeUrlState);
  return Object.keys(networkTreeURLs);
});

const defaultNetworkTreeState = atom<CheckboxTreeState>((get) => {
  const networkTreeConfig = get(networkTreeConfigState);
  return {
    checked: mapValues(networkTreeConfig.nodes, () => false),
    indeterminate: mapValues(networkTreeConfig.nodes, () => false),
  };
});

const _networkTreeBase = atom(null as CheckboxTreeState | null); 

export const networkTreeCheckboxState = atom(
  (get) => {
    function parseTreeFromString(value: string) {
      const networkTreeConfig = get(networkTreeConfigState);
      const networkTreeURLs = get(networkTreeUrlState);
      const networkTreeIDs = get(networkTreeIdState);
      const disabledNodeIds = get(disabledNetworkNodeIdsState);
      const separator = value.includes('.') ? '.' : ',';
      const checkedFields = value.split(separator).filter(Boolean);
      const checked: Record<string, boolean> = {};
      checkedFields.forEach((url) => {
        const id = networkTreeIDs.includes(url)
          ? url // url is a layer ID.
          : networkTreeIDs.find((id) => networkTreeURLs[id] === url); // url is the hex code for a layer.
        if (id !== undefined) {
          checked[id] = true;
        }
      });
      return recalculateCheckboxStates(
        { checked, indeterminate: {} },
        networkTreeConfig,
        disabledNodeIds,
      );
    }

    const networkTree = get(_networkTreeBase);
    const defaultNetworkTree = networkTree || get(defaultNetworkTreeState);
    const disabledNodeIds = get(disabledNetworkNodeIdsState);
    const params = new URLSearchParams(window.location.search);
    const raw = params.get('netTree') ?? sessionStorage.getItem(STORAGE_PREFIX + 'netTree');
    if (!raw) {
      return recalculateCheckboxStates(defaultNetworkTree, get(networkTreeConfigState), disabledNodeIds);
    }
    return parseTreeFromString(raw);
  },
  (get, set, newTree: CheckboxTreeState) => {
    const networkTreeConfig = get(networkTreeConfigState);
    const networkTreeURLs = get(networkTreeUrlState);
    const disabledNodeIds = get(disabledNetworkNodeIdsState);
    const sanitizedTree = recalculateCheckboxStates(newTree, networkTreeConfig, disabledNodeIds);
    set(_networkTreeBase, sanitizedTree);
    const checkedLayers = Object.keys(sanitizedTree.checked).filter(
      (id) =>
        sanitizedTree.checked[id] &&
        networkTreeConfig.nodes[id] &&
        !networkTreeConfig.nodes[id].children,
    );
    const checked = checkedLayers.map((id) => networkTreeURLs[id]);
    const str = checked.join('.');
    sessionStorage.setItem(STORAGE_PREFIX + 'netTree', str);
    set(atomWithQueryParams, setUrlParam('netTree', str));
  }
);

export const networkSelectionState = atom<string[]>((get) => {
  const checkboxState = get(networkTreeCheckboxState);
  const networkTreeConfig = get(networkTreeConfigState);

  return Object.keys(checkboxState.checked).filter(
    (id) =>
      checkboxState.checked[id] &&
      networkTreeConfig.nodes[id] &&
      !networkTreeConfig.nodes[id].children,
  );
});

export const selectedNetworkLayerIdsState = atom<string[]>((get) => {
  const networkTreeConfig = get(networkTreeConfigState);

  return get(networkSelectionState)
    .map((nodeId) => networkTreeConfig.nodes[nodeId]?.layerId)
    .filter((layerId): layerId is string => layerId !== undefined);
});

export const networksStyleState = atom((get) => get(sectionStyleValueState('assets')));

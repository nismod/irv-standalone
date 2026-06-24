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
import { TreeNode } from 'lib/controls/checkbox-tree/tree-node';

interface NetworkLayerData {
  label: string;
  url?: string;
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

let leafIndex = 0;
function buildHierarchyFromNodes(nodes: InfrastructureNode[]): TreeNode<NetworkLayerData>[] {
  return nodes.map((node) => {
    const treeNode: TreeNode<NetworkLayerData> = {
      id: node.node_id,
      label: node.node_name,
    };
    if (node.children.length > 0) {
      treeNode.children = buildHierarchyFromNodes(node.children);
    } else {
      leafIndex++;
      const nodeUrl = leafIndex.toString(16).padStart(2, '0'); // 2-digit hex string.
      treeNode.url = nodeUrl;
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
      return recalculateCheckboxStates({ checked, indeterminate: {} }, networkTreeConfig);
    }

    const networkTree = get(_networkTreeBase);
    const defaultNetworkTree = networkTree || get(defaultNetworkTreeState);
    const params = new URLSearchParams(window.location.search);
    const raw = params.get('netTree') ?? sessionStorage.getItem(STORAGE_PREFIX + 'netTree');
    if (!raw) return defaultNetworkTree;
    return parseTreeFromString(raw);
  },
  (get, set, newTree: CheckboxTreeState) => {
    const networkTreeConfig = get(networkTreeConfigState);
    const networkTreeURLs = get(networkTreeUrlState);
    set(_networkTreeBase, newTree);
    const checkedLayers = Object.keys(newTree.checked).filter(
      (id) =>
        newTree.checked[id] && networkTreeConfig.nodes[id] && !networkTreeConfig.nodes[id].children,
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

export const networksStyleState = atom((get) => get(sectionStyleValueState('assets')));

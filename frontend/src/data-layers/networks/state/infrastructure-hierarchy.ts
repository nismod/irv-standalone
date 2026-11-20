import { type InfrastructureNode } from 'lib/api-client';
import { type TreeNode } from 'lib/controls/checkbox-tree/tree-node';

interface NetworkLayerData {
  label: string;
  url?: string;
  layerId?: string;
}

export function buildHierarchyFromNodes(
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
      // Retain positions of unlinked nodes so existing map URLs stay stable.
      leafIndex.value++;
      if (node.feature_layer) {
        treeNode.url = leafIndex.value.toString(16).padStart(2, '0');
        treeNode.layerId = node.feature_layer;
      }
    }
    return treeNode;
  });
}

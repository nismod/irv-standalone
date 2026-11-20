import { describe, expect, it } from 'vitest';

import { buildHierarchyFromNodes, orderHierarchyLayers } from './infrastructure-hierarchy';

describe('infrastructure hierarchy', () => {
  it('uses explicit layer links and leaves unmatched nodes without a layer', () => {
    const [root] = buildHierarchyFromNodes([{
      node_id: 'roads', node_name: 'Roads', parent: null, children: [
        { node_id: 'missing', node_name: 'Missing', parent: 'roads', feature_layer: null, children: [] },
        { node_id: 'class-a', node_name: 'Class A', parent: 'roads', feature_layer: 'road_edges_class_a', children: [] },
      ],
    }]);
    expect(root.children?.[0].layerId).toBeUndefined();
    expect(root.children?.[1].layerId).toBe('road_edges_class_a');
    expect(root.children?.[1].url).toBe('02');
  });

  it('orders linked siblings while retaining their saved URL codes', () => {
    const nodes = buildHierarchyFromNodes([
      { node_id: 'a', node_name: 'A', parent: null, feature_layer: 'a', children: [] },
      { node_id: 'b', node_name: 'B', parent: null, feature_layer: 'b', children: [] },
    ]);
    const ordered = orderHierarchyLayers(nodes, { a: { display_order: 2 }, b: { display_order: 1 } });
    expect(ordered.map((node) => [node.id, node.url])).toEqual([['b', '02'], ['a', '01']]);
  });
});

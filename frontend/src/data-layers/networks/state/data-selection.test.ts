import { describe, expect, it } from 'vitest';

import { buildHierarchyFromNodes } from './infrastructure-hierarchy';

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
});

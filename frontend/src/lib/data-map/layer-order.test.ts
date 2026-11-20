import { describe, expect, it } from 'vitest';
import type { ViewLayer } from './view-layers';
import { orderLayersByStacking } from './layer-order';

describe('layer stacking', () => {
  it('interleaves feature and raster layers, preserving ties and overlay positions', () => {
    const layers = [
      { id: 'raster-high', stackingOrder: 8 },
      { id: 'overlay' },
      { id: 'feature-low', stackingOrder: 1 },
      { id: 'raster-low', stackingOrder: 1 },
    ] as ViewLayer[];
    expect(orderLayersByStacking(layers).map((layer) => layer.id))
      .toEqual(['feature-low', 'overlay', 'raster-low', 'raster-high']);
    expect(layers.map((layer) => layer.id)).toEqual(['raster-high', 'overlay', 'feature-low', 'raster-low']);
  });

  it('uses catalogue order for layers from any section', () => {
    const layers = [{ id: 'building' }, { id: 'overlay' }, { id: 'raster' }] as ViewLayer[];
    expect(orderLayersByStacking(layers, {
      building: { stacking_order: 5 }, raster: { stacking_order: 2 },
    }).map((layer) => layer.id)).toEqual(['raster', 'overlay', 'building']);
  });
});

import type { ViewLayer } from './view-layers';

/** Sort configured layers together, keeping other map overlays in their slots. */
export function orderLayersByStacking(
  layers: ViewLayer[],
  metadata: Record<string, { stacking_order?: number }> = {},
): ViewLayer[] {
  const order = (layer: ViewLayer) => metadata[layer.id]?.stacking_order ?? layer.stackingOrder;
  const ordered = layers.filter((layer) => order(layer) !== undefined);
  ordered.sort((a, b) => order(a)! - order(b)!);
  let index = 0;
  return layers.map((layer) => (order(layer) === undefined ? layer : ordered[index++]));
}

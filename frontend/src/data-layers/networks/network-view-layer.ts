import { ViewLayer } from 'lib/data-map/view-layers';

export function networkViewLayer({ network, styleParams, infrastructureViewLayers }): ViewLayer {
  return {
    ...infrastructureViewLayers[network],
    styleParams,
  };
}

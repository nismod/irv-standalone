import { ViewLayer } from 'lib/data-map/view-layers';
import { border, fillColor } from 'lib/deck/props/style';
import { assetDataAccessFunction } from 'lib/data-map/layers/assets/data-access';

import { assetViewLayer } from 'data-layers/assets/asset-view-layer';
export function buildingsViewLayer(
  building_type_id: string,
  color: [number, number, number, number?],
): ViewLayer {
  return assetViewLayer(
    building_type_id,
    {
      group: 'buildings',
      spatialType: 'vector',
      interactionGroup: 'assets',
    },
    -1000,
    () => [{ minZoom: 11 }, border(color), fillColor(color)],
    assetDataAccessFunction(building_type_id),
  );
}

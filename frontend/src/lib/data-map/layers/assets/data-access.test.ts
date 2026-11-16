import { describe, expect, it } from 'vitest';
import { MapGeoJSONFeature } from 'maplibre-gl';
import { getAssetDataAccessor } from './data-access';

const feature = {
  properties: {
    'ead__cyclone__rcp_4.5__epoch_2050__conf_None': 10,
    'ead__coastal__rcp_4.5__epoch_2050__conf_None': 20,
    'eael__cyclone__rcp_4.5__epoch_2050__conf_None': 30,
    'eael__coastal__rcp_4.5__epoch_2050__conf_None': 40,
  },
} as unknown as MapGeoJSONFeature;

describe('expected damage tile access', () => {
  it.each([
    ['cyclone', 'ead_mean', 10],
    ['cyclone', 'eael_mean', 30],
    ['all', 'ead_mean', 30],
    ['all', 'eael_mean', 70],
  ])('reads %s %s using the existing tile convention', (hazard, field, expected) => {
    const accessor = getAssetDataAccessor('roads', {
      fieldGroup: 'damages_expected',
      field,
      fieldDimensions: { hazard, parameters: { epoch: 2050, rcp: '4.5' } },
    });
    expect(accessor(feature)).toBe(expected);
  });
});

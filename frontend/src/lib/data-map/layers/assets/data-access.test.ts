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
  ])('reads %s %s using the existing tile convention', (hazard, field, expected) => {
    const accessor = getAssetDataAccessor('roads', {
      fieldGroup: 'damages_expected',
      field,
      fieldDimensions: { hazard, parameters: { epoch: 2050, rcp: '4.5' }, protection_standard: 0 },
    });
    expect(accessor(feature)).toBe(expected);
  });

  it.each([
    ['flood', { gwl: 2, slr: 0.5 }, 0, 'ead_mean'],
    ['all', { rcp: '4.5', epoch: 2050 }, 0, 'ead_mean'],
    ['cyclone', { rcp: '4.5', epoch: 2050 }, 100, 'ead_mean'],
    ['cyclone', { rcp: '4.5', epoch: 2050 }, 0, 'ead_amax'],
  ])(
    'loads %s through the attributes API when legacy tiles cannot represent it',
    async (hazard, parameters, protection_standard, field) => {
      const fieldSpec = {
        fieldGroup: 'damages_expected',
        field,
        fieldDimensions: { hazard, parameters, protection_standard },
      };
      const accessor = getAssetDataAccessor('roads', fieldSpec);
      const loader = accessor.dataLoader;
      expect(loader.fieldSpec).toEqual(fieldSpec);
      await loader.loadData(
        async (_ids, layer, spec) => {
          expect(layer).toBe('roads');
          expect(spec.fieldDimensions.parameters).toEqual(parameters);
          return { 123: 42 };
        },
        [123],
      );
      // loadData currently schedules the update after its fetch promise settles.
      await Promise.resolve();
      expect(accessor({ id: 123, properties: {} })).toBe(42);
    },
  );
});

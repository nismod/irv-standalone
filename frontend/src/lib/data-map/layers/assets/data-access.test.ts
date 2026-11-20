import { describe, expect, it } from 'vitest';
import { getAssetDataAccessor } from './data-access';

describe('expected damage tile access', () => {
  it.each([
    ['flood', { gwl: 2, slr: 0.5 }, 0, 'ead_mean'],
    ['all', { rcp: '4.5', epoch: 2050 }, 0, 'ead_mean'],
    ['cyclone', { rcp: '4.5', epoch: 2050 }, 100, 'ead_mean'],
    ['cyclone', { rcp: '4.5', epoch: 2050 }, 0, 'ead_amax'],
  ])(
    'loads %s through the attributes API',
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

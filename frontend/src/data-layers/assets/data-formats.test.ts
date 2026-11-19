import { describe, expect, it } from 'vitest';
import { getAssetDataFormats } from './data-formats';

describe('damage labels', () => {
  it('names the hazards contributing to a selected total', () => {
    const fieldSpec = {
      fieldGroup: 'damages_expected', field: 'ead_mean',
      fieldDimensions: {
        hazard: 'all', parameters: { GWL: 2 }, protection_standard: 0,
        hazard_parameters: { fluvial: { GWL: 2 }, pluvial: { GWL: 2 } },
      },
    };
    const formats = getAssetDataFormats(fieldSpec, {
      coastal: { label: 'Coastal flooding' },
      fluvial: { label: 'River flooding' },
      pluvial: { label: 'Surface flooding' },
    });
    expect(formats.getDataLabel(fieldSpec)).toBe('Direct Damages (River flooding + Surface flooding)');
  });
});

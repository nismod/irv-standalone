import { describe, expect, it } from 'vitest';
import { matchRasterScenario } from './raster-scenario';

const config = {
  paramDefaults: { GWL: 0.75, RP: 100 },
  paramDomains: { GWL: [0.75, 2, 3], RP: [20, 100, 500] },
};

describe('raster scenario linking', () => {
  it('matches case and return-period aliases against the actual raster keys', () => {
    expect(matchRasterScenario({ gwl: 2, returnPeriod: 500 }, config)).toEqual({
      linked: true,
      desired: { GWL: 2, RP: 500 },
    });
  });
  it('keeps incompatible schemas independent without inventing a projection', () => {
    expect(matchRasterScenario({ rcp: 'baseline', epoch: 2010 }, config)).toEqual({
      linked: false,
      desired: {},
    });
    expect(matchRasterScenario({ gwl: 2, member: 'b' }, config)).toEqual({
      linked: false,
      desired: {},
    });
    expect(matchRasterScenario({ gwl: 4 }, config)).toEqual({ linked: false, desired: {} });
  });
  it('uses equivalent scalar URL values without modifying model parameter types', () => {
    const parameters = { gwl: '2' };
    expect(matchRasterScenario(parameters, config)).toEqual({ linked: true, desired: { GWL: 2 } });
    expect(parameters).toEqual({ gwl: '2' });
  });
  it('does not link a combination rejected by raster dependencies', () => {
    expect(
      matchRasterScenario(
        { rcp: '8.5', epoch: 2010 },
        {
          paramDefaults: { rcp: 'baseline', epoch: 2010 },
          paramDomains: { rcp: ['baseline', '8.5'], epoch: [2010, 2050] },
          paramDependencies: { rcp: ({ epoch }) => (epoch === 2010 ? ['baseline'] : ['8.5']) },
        },
      ),
    ).toEqual({ linked: false, desired: {} });
  });

  it('requires the selected values to occur together in a raster catalogue row', () => {
    const sparseConfig = {
      paramDefaults: { GWL: 2, SLR: 0, RP: 100 },
      paramDomains: { GWL: [2, 3], SLR: [0, 0.5], RP: [100, 500] },
      paramCombinations: [
        { GWL: 2, SLR: 0, RP: 100 },
        { GWL: 3, SLR: 0.5, RP: 500 },
      ],
    };
    expect(matchRasterScenario({ gwl: 2, slr: 0.5 }, sparseConfig)).toEqual({
      linked: false,
      desired: {},
    });
    expect(matchRasterScenario({ gwl: '3', slr: 0.5 }, sparseConfig)).toEqual({
      linked: true,
      desired: { GWL: 3, SLR: 0.5 },
    });
    expect(matchRasterScenario({ gwl: 2, returnPeriod: 500 }, sparseConfig).linked).toBe(false);
    expect(matchRasterScenario({ gwl: 3 }, { ...sparseConfig, paramCombinations: [] }).linked).toBe(false);
  });
});

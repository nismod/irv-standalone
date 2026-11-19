import { describe, expect, it } from 'vitest';
import type { FieldSpec } from 'lib/data-map/view-layers';
import {
  changeParameter,
  ModelScenario,
  parameterKey,
  parameterOptions,
  scenarioDimensions,
  scenariosForHazard,
  scenariosForHazards,
  selectParameters,
  selectResult,
  valueKey,
} from './scenarios';

const rows: ModelScenario[] = [
  { hazard: 'flood', parameters: { gwl: 1.5, slr: 0, member: 'a' }, protection_standard: 0 },
  { hazard: 'flood', parameters: { gwl: 2, slr: 0.5, member: 'a' }, protection_standard: 0 },
  { hazard: 'flood', parameters: { gwl: 2, slr: 1, member: 'b' }, protection_standard: 0 },
];

describe('model scenarios', () => {
  it('accepts JSON arrays, booleans and nested objects in FieldSpec model parameters', () => {
    const parameters = { enabled: true, members: [1, '1', false], settings: { optional: null } };
    const fieldSpec: FieldSpec = {
      fieldGroup: 'damages_expected',
      field: 'ead_mean',
      fieldDimensions: scenarioDimensions({ hazard: 'flood', protection_standard: 0, parameters }),
    };
    expect(fieldSpec.fieldDimensions.parameters).toEqual(parameters);
  });

  it('keeps complete scenarios and their JSON types when changing sparse dimensions', () => {
    const selected = rows[0].parameters;
    expect(parameterOptions(rows, selected, 'gwl').map((option) => option.value)).toEqual([1.5, 2]);
    const next = changeParameter(rows, selected, 'gwl', valueKey(2));
    expect(next).toEqual(rows[1].parameters);
    expect(parameterOptions(rows, next, 'slr').map((option) => option.value)).toEqual([0.5]);
    expect(changeParameter(rows, next, 'member', valueKey('b'))).toEqual(rows[2].parameters);
    expect(selectParameters([], selected)).toBeNull();
  });

  it('retains a valid selection across hazard changes and falls back to a real combination', () => {
    expect(selectParameters(rows, { slr: 0.5, gwl: 2, member: 'a' })).toBe(rows[1].parameters);
    const other = [{ hazard: 'heat', parameters: { gwl: 3 } }];
    expect(selectParameters(other, rows[1].parameters)).toEqual({ gwl: 3 });
    expect(selectParameters(rows, { gwl: 2, slr: 999 })).toEqual(rows[1].parameters);
  });

  it('offers all-hazard scenarios only at a shared parameter set and protection standard', () => {
    const combined = [
      ...rows,
      { ...rows[1], hazard: 'heat' },
      { ...rows[0], hazard: 'heat', protection_standard: 100 },
      { ...rows[2], parameters: { gwl: 4 }, hazard: 'heat' },
    ];
    expect(scenariosForHazard(combined, 'all')).toEqual([{ ...rows[1], hazard: 'all' }]);
    expect(scenariosForHazard(combined, 'heat')).toHaveLength(3);
  });

  it('distinguishes JSON values, object key order, and missing values', () => {
    expect(parameterKey({ gwl: 2, slr: 0.5 })).toBe(parameterKey({ slr: 0.5, gwl: 2 }));
    expect(valueKey(1)).not.toBe(valueKey('1'));
    expect(valueKey(undefined)).not.toBe(valueKey(null));
    const nested = [{ hazard: 'flood', parameters: { config: { a: [1, '1'] } } }];
    expect(selectParameters(nested, { config: { a: [1, '1'] } })).toEqual(nested[0].parameters);
  });

  it('combines independent hazard parameters and keeps shared dimensions compatible', () => {
    const catalogue: ModelScenario[] = [
      ...[0, 20].map((SLR) => ({ hazard: 'coastal', parameters: { SLR }, protection_standard: 0 })),
      ...[2, 3].map((GWL) => ({ hazard: 'fluvial', parameters: { GWL }, protection_standard: 0 })),
      { hazard: 'pluvial', parameters: { GWL: 2 }, protection_standard: 0 },
    ];
    const all = scenariosForHazard(catalogue, 'all');
    expect(all.map((row) => row.parameters)).toEqual([{ SLR: 0, GWL: 2 }, { SLR: 20, GWL: 2 }]);
    const selected = selectResult(all, { SLR: 20, GWL: 2 });
    expect(scenarioDimensions(selected)).toEqual({
      hazard: 'all', parameters: { SLR: 20, GWL: 2 }, protection_standard: 0,
      hazard_parameters: { coastal: { SLR: 20 }, fluvial: { GWL: 2 }, pluvial: { GWL: 2 } },
    });
    expect(parameterOptions(all, all[0].parameters, 'SLR').map((option) => option.value)).toEqual([0, 20]);
    expect(scenariosForHazard([...catalogue, {
      hazard: 'wind', parameters: { GWL: '2' }, protection_standard: 0,
    }], 'all')).toEqual([]);
    expect(scenariosForHazard([], 'all')).toEqual([]);
  });

  it('keeps fixed result dimensions outside the parameter set', () => {
    const result = selectResult(rows, rows[1].parameters, { protection_standard: 0 });
    expect(scenarioDimensions(result)).toEqual({
      hazard: 'flood',
      parameters: { gwl: 2, slr: 0.5, member: 'a' },
      protection_standard: 0,
    });
    const adaptations = [
      {
        hazard: 'flood',
        parameters: { gwl: 2 },
        adaptation_name: 'Wall',
        adaptation_protection_level: 50,
      },
    ];
    expect(scenarioDimensions(selectResult(adaptations, { gwl: 2 }))).toEqual(adaptations[0]);
    const otherOption = {
      ...adaptations[0],
      adaptation_name: 'Raise',
      adaptation_protection_level: 100,
    };
    expect(
      selectResult(
        [...adaptations, otherOption],
        { gwl: 2 },
        {
          adaptation_name: 'Raise',
          adaptation_protection_level: 50,
        },
      ),
    ).toEqual(otherOption);
  });

  it('scopes a shared-parameter total to the checked hazards only', () => {
    const catalogue: ModelScenario[] = ['coastal', 'fluvial', 'pluvial'].map((hazard) => ({
      hazard, parameters: { GWL: 2 }, protection_standard: 0,
    }));
    expect(scenariosForHazards(catalogue, ['fluvial', 'pluvial'])).toEqual([{
      hazard: 'all', parameters: { GWL: 2 }, protection_standard: 0,
      hazard_parameters: { fluvial: { GWL: 2 }, pluvial: { GWL: 2 } },
    }]);
    expect(scenariosForHazards(catalogue, ['fluvial'])).toEqual([catalogue[1]]);
    expect(scenariosForHazards(catalogue, [])).toEqual([]);
    expect(scenariosForHazards(catalogue, ['fluvial', 'missing'])).toEqual([]);
    expect(scenariosForHazards(catalogue, 'all')).toEqual(scenariosForHazard(catalogue, 'all'));
  });
});

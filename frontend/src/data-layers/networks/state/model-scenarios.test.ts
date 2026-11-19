import { afterEach, describe, expect, it, vi } from 'vitest';
import { createStore, type PrimitiveAtom } from 'jotai';
import * as api from 'lib/api-client';
import * as sdk from 'lib/api-client/sdk.gen';
import { modelParametersState } from 'lib/model-scenarios/state';
import { dataParamState, syncExternalConfigState } from 'lib/state/data-params';
import { damageSourceState, damageTypeState } from 'lib/state/damage-map';
import { mapViewConfig } from 'lib/state/map-view/map-view-config';
import { networksStyleState, selectedNetworkLayerIdsState } from './data-selection';
import { damageScenarioState, damagesFieldState } from './damage-scenarios';
import { adaptationFieldSpecState, adaptationFieldState } from './layer';
import {
  protectedFeatureAdaptationOptionsState,
  protectedFeatureScenarioState,
} from 'lib/state/protected-features';
import { selectionState } from 'lib/state/interactions/interaction-state';
import { damageSourceStateEffect } from 'app/state/damage-mapping/damage-map';
import { hazardSelectionState } from 'data-layers/hazards/state/data-selection';
import { matchRasterScenario } from 'data-layers/hazards/raster-scenario';
import { HAZARD_SOURCE } from 'data-layers/hazards/source';
import { hazardsMetadataState, hazardsMapOrderState } from 'data-layers/hazards/state/metadata';
import { hazardDomainState } from 'data-layers/hazards/state/domains';
import { hazardVisibilityState } from 'data-layers/hazards/state/hazard-visibility';
import type { Dataset } from 'lib/api-client';

vi.mock('./data-selection', async () => {
  const { atom } = await import('jotai');
  return {
    selectedNetworkLayerIdsState: atom(['roads']),
    networksStyleState: atom('damages'),
    networkTreeCheckboxState: atom({ checked: {}, indeterminate: {} }),
    networkTreeConfigState: atom({ nodes: {}, roots: [] }),
  };
});
vi.mock('../view-layers', () => ({ getInfrastructureViewLayers: () => ({}) }));
vi.mock('data-layers/hazards/state/metadata', async (importOriginal) => {
  const actual = await importOriginal<typeof import('data-layers/hazards/state/metadata')>();
  const { atom } = await import('jotai');
  return { ...actual, hazardsMetadataState: atom({}), hazardsMapOrderState: atom([]) };
});
vi.mock('lib/state/interactions/interaction-state', async () => {
  const { atom } = await import('jotai');
  const { atomFamily } = await import('jotai-family');
  return { selectionState: atomFamily(() => atom({ target: { feature: { id: 123 } } })) };
});
vi.mock('lib/state/map-view/map-url', async () => {
  const { atom } = await import('jotai');
  return {
    atomWithStoredBool: (_name, value) => atom(value),
    atomWithStoredStr: (_name, value) => atom(value),
    atomWithQueryParams: atom({ searchParams: new URLSearchParams() }),
    STORAGE_PREFIX: '',
    setUrlParam: vi.fn(),
  };
});
vi.mock('lib/state/map-view/map-view-config', async () => {
  const { atom } = await import('jotai');
  return { mapViewConfig: atom({ app: { name: 'Test', currency: 'MUR' }, initialViewState: { latitude: 0, longitude: 0, zoom: 0 }, viewLimits: {} }) };
});

const subscriptions: (() => void)[] = [];
afterEach(() => {
  subscriptions.splice(0).forEach((unsubscribe) => unsubscribe());
  vi.restoreAllMocks();
});

describe('model scenario query flow', () => {
  it('keeps configured currency and daily units with discovered damage and adaptation scenarios', async () => {
    vi.spyOn(api, 'mapModelScenariosList').mockImplementation(async ({ path }) => ({
      data: path.field_group === 'damages_expected'
        ? [{ hazard: 'fluvial', parameters: { GWL: 2 }, protection_standard: 0 }]
        : [{ hazard: 'fluvial', parameters: { GWL: 2 }, adaptation_name: 'Wall', adaptation_protection_level: 50 }],
    }) as never);
    const store = createStore();
    store.set(dataParamState({ group: 'adaptation', param: 'sector' }), 'power');
    subscriptions.push(store.sub(damagesFieldState, () => {}));
    subscriptions.push(store.sub(adaptationFieldSpecState, () => {}));
    await vi.waitFor(() => {
      expect(store.get(damagesFieldState)?.unit).toBe('MUR');
      expect(store.get(adaptationFieldSpecState)?.unit).toBe('MUR');
    });
    store.set(damageTypeState, 'indirect');
    store.set(adaptationFieldState, 'avoided_eael_mean');
    expect(store.get(damagesFieldState).unit).toBe('MUR/day');
    expect(store.get(adaptationFieldSpecState).unit).toBe('MUR/day');
    const config = store.get(mapViewConfig);
    store.set(mapViewConfig as PrimitiveAtom<typeof config>, {
      ...config, app: { ...config.app, currency: 'USD' },
    });
    expect(store.get(damagesFieldState).unit).toBe('USD/day');
    expect(store.get(adaptationFieldSpecState).unit).toBe('USD/day');
    store.set(damageTypeState, 'direct');
    store.set(adaptationFieldState, 'cost_benefit_ratio');
    expect(store.get(damagesFieldState).unit).toBe('USD');
    expect(store.get(adaptationFieldSpecState).unit).toBeUndefined();
  });

  it('activates each matching all-hazard raster using its own parameters', () => {
    const store = createStore();
    store.set(damageSourceState, 'all');
    store.set(hazardsMetadataState as PrimitiveAtom<Record<string, Dataset>>, Object.fromEntries(
      ['coastal', 'fluvial', 'pluvial', 'wind'].map((id) => [id, { id, has_access: true } as Dataset]),
    ));
    store.set(hazardsMapOrderState as PrimitiveAtom<string[]>, ['coastal', 'fluvial', 'pluvial', 'wind']);
    const hazardDomains = {
      coastal: { paramDefaults: { SLR: 0, RP: 100 }, paramDomains: { SLR: [0, 20], RP: [100, 500] } },
      fluvial: { paramDefaults: { GWL: 2, RP: 100 }, paramDomains: { GWL: [2, 3], RP: [100, 500] } },
      pluvial: { paramDefaults: { GWL: 2, RP: 100 }, paramDomains: { GWL: [2], RP: [100] } },
      wind: { paramDefaults: { GWL: 2 }, paramDomains: { GWL: [2, 3] } },
    };
    store.set(hazardSelectionState('wind'), true);
    const ops = { get: store.get, set: store.set };
    damageSourceStateEffect(ops, {
      scenario: {
        hazard: 'all', parameters: { SLR: 20, GWL: 3 },
        hazard_parameters: { coastal: { SLR: 20 }, fluvial: { GWL: 3 }, pluvial: { GWL: 3 } },
      },
      hazardDomains,
    });
    expect(store.get(hazardVisibilityState)).toEqual({ coastal: true, fluvial: true, pluvial: false, wind: false });
    expect(store.get(dataParamState({ group: 'coastal', param: 'SLR' }))).toBe(20);
    expect(store.get(dataParamState({ group: 'fluvial', param: 'GWL' }))).toBe(3);

    damageSourceStateEffect(ops, {
      scenario: { hazard: 'coastal', parameters: { SLR: 0 } }, hazardDomains,
    });
    expect(store.get(hazardSelectionState('coastal'))).toBe(true);
    expect(store.get(hazardSelectionState('fluvial'))).toBe(false);
    damageSourceStateEffect(ops, { scenario: null, hazardDomains });
    expect(store.get(hazardSelectionState('coastal'))).toBe(false);
  });

  it('limits shared-schema all-hazard rasters to the damage scope and accessible datasets', () => {
    const store = createStore();
    store.set(hazardsMetadataState as PrimitiveAtom<Record<string, Dataset>>, {
      fluvial: { id: 'fluvial', has_access: true } as Dataset,
      coastal: { id: 'coastal', has_access: false } as Dataset,
      wind: { id: 'wind', has_access: true } as Dataset,
    });
    store.set(hazardsMapOrderState as PrimitiveAtom<string[]>, ['fluvial', 'coastal', 'wind']);
    const config = { paramDefaults: { GWL: 2 }, paramDomains: { GWL: [2, 3] } };
    damageSourceStateEffect({ get: store.get, set: store.set }, {
      scenario: { hazard: 'all', parameters: { GWL: 3 } },
      hazards: ['fluvial', 'coastal'],
      hazardDomains: { fluvial: config, coastal: config, wind: config },
    });
    expect(store.get(hazardVisibilityState)).toEqual({ fluvial: true, wind: false });
    expect(store.get(dataParamState({ group: 'fluvial', param: 'GWL' }))).toBe(3);
  });

  it('uses the combined all-hazard controls to request exact per-hazard scenarios', async () => {
    vi.spyOn(api, 'mapModelScenariosList').mockResolvedValue({
      data: [
        ...[0, 20].map((SLR) => ({ hazard: 'coastal', parameters: { SLR }, protection_standard: 0 })),
        ...['fluvial', 'pluvial'].flatMap((hazard) => [2, 3].map((GWL) => ({
          hazard, parameters: { GWL }, protection_standard: 0,
        }))),
      ],
    } as never);
    const store = createStore();
    store.set(damageSourceState, 'all');
    subscriptions.push(store.sub(damagesFieldState, () => {}));
    await vi.waitFor(() => expect(store.get(damagesFieldState)).not.toBeNull());
    store.set(modelParametersState('damages_expected'), { SLR: 20, GWL: 3 });
    expect(store.get(damagesFieldState).fieldDimensions).toEqual({
      hazard: 'all', parameters: { SLR: 20, GWL: 3 }, protection_standard: 0,
      hazard_parameters: { coastal: { SLR: 20 }, fluvial: { GWL: 3 }, pluvial: { GWL: 3 } },
    });
    store.set(damageSourceState, ['fluvial', 'pluvial']);
    expect(store.get(damageScenarioState).selectedHazards).toEqual(['fluvial', 'pluvial']);
    expect(store.get(damagesFieldState).fieldDimensions).toEqual({
      hazard: 'all', parameters: { GWL: 3 }, protection_standard: 0,
      hazard_parameters: { fluvial: { GWL: 3 }, pluvial: { GWL: 3 } },
    });
    store.set(damageSourceState, []);
    expect(store.get(damagesFieldState)).toBeNull();
    store.set(damageSourceState, ['coastal']);
    expect(store.get(damagesFieldState).fieldDimensions).toEqual({
      hazard: 'coastal', parameters: { SLR: 20 }, protection_standard: 0,
    });
  });

  it('drops a restricted persisted hazard without selecting a different hazard', async () => {
    vi.spyOn(api, 'mapModelScenariosList').mockResolvedValue({
      data: [
        { hazard: 'fluvial', parameters: { gwl: 2 }, protection_standard: 0 },
        { hazard: 'coastal', parameters: { gwl: 4 }, protection_standard: 0 },
      ],
    } as never);
    const store = createStore();
    store.set(hazardsMetadataState as PrimitiveAtom<Record<string, Dataset>>, {
      coastal: { id: 'coastal', has_access: false } as Dataset,
    });
    store.set(damageSourceState, ['coastal']);
    subscriptions.push(store.sub(damagesFieldState, () => {}));
    await vi.waitFor(() => expect(store.get(damageScenarioState).hazards).toEqual(['fluvial']));
    expect(store.get(damagesFieldState)).toBeNull();
    expect(store.get(damageScenarioState).selectedHazards).toEqual([]);
  });

  it('revalidates an active selection when permissions change while the catalogue is cached', async () => {
    const catalogue = vi.spyOn(api, 'mapModelScenariosList').mockResolvedValue({
      data: [{ hazard: 'coastal', parameters: { gwl: 2 }, protection_standard: 0 }],
    } as never);
    const store = createStore();
    const metadata = hazardsMetadataState as PrimitiveAtom<Record<string, Dataset>>;
    store.set(metadata, { coastal: { id: 'coastal', has_access: true } as Dataset });
    store.set(damageSourceState, ['coastal']);
    subscriptions.push(store.sub(damagesFieldState, () => {}));
    await vi.waitFor(() =>
      expect(store.get(damagesFieldState)?.fieldDimensions.hazard).toBe('coastal'),
    );
    store.set(metadata, { coastal: { id: 'coastal', has_access: false } as Dataset });
    expect(store.get(damagesFieldState)).toBeNull();
    expect(catalogue).toHaveBeenCalledTimes(1);
  });

  it('waits for asset filters before requesting adaptation metadata', () => {
    const request = vi.spyOn(api, 'mapModelScenariosList');
    const store = createStore();
    subscriptions.push(store.sub(adaptationFieldSpecState, () => {}));
    expect(store.get(adaptationFieldSpecState)).toBeNull();
    expect(request).not.toHaveBeenCalled();
  });

  it('uses protector scenarios for colouring and updates the cache scope with the selection', async () => {
    const request = vi.spyOn(api, 'mapModelScenariosList').mockResolvedValue({
      data: [2, 4].map((gwl) => ({
        hazard: 'coastal',
        parameters: { gwl },
        adaptation_name: 'Wall',
        adaptation_protection_level: 50,
      })),
    } as never);
    const store = createStore();
    store.set(networksStyleState as PrimitiveAtom<string>, 'protectedFeatures');
    subscriptions.push(store.sub(adaptationFieldSpecState, () => {}));

    await vi.waitFor(() => expect(store.get(adaptationFieldSpecState)).not.toBeNull());
    const initial = store.get(adaptationFieldSpecState);
    expect(initial.fieldDimensions).toEqual({
      hazard: 'coastal',
      parameters: { gwl: 2 },
      adaptation_name: 'Wall',
      adaptation_protection_level: 50,
      protector_id: 123,
    });
    // There are no asset filters in this store: only the protector catalogue
    // should be needed to construct the colour field.
    expect(request).toHaveBeenCalledTimes(1);
    expect(request).toHaveBeenCalledWith(expect.objectContaining({ query: { protector_id: 123 } }));

    store.set(modelParametersState('adaptation'), { gwl: 4 });
    const nextScenario = store.get(adaptationFieldSpecState);
    expect(nextScenario.fieldDimensions.parameters).toEqual({ gwl: 4 });
    expect(nextScenario).not.toEqual(initial);

    store.set(selectionState('assets'), { target: { feature: { id: 456 } } } as never);
    expect(store.get(adaptationFieldSpecState)).toBeNull();
    await vi.waitFor(() =>
      expect(store.get(adaptationFieldSpecState)?.fieldDimensions.protector_id).toBe(456),
    );
    expect(store.get(adaptationFieldSpecState).fieldDimensions.parameters).toEqual({ gwl: 4 });
    expect(store.get(adaptationFieldSpecState)).not.toEqual(nextScenario);
  });

  it('links matching raster dimensions and hides incompatible scenarios', () => {
    const store = createStore();
    const ops = { get: store.get, set: store.set };
    const hazardDomains = {
      heat: {
        paramDefaults: { gwl: 1.5, slr: 0, returnPeriod: 100 },
        paramDomains: { gwl: [1.5, 2], slr: [0, 0.5], returnPeriod: [100, 500] },
        paramDependencies: { slr: ({ gwl }) => (gwl === 2 ? [0.5] : [0]) },
      },
    };
    damageSourceStateEffect(ops, {
      scenario: { hazard: 'heat', parameters: { gwl: 2, slr: 0.5 } },
      hazardDomains,
    });
    expect(store.get(dataParamState({ group: 'heat', param: 'gwl' }))).toBe(2);
    expect(store.get(dataParamState({ group: 'heat', param: 'slr' }))).toBe(0.5);
    expect(store.get(dataParamState({ group: 'heat', param: 'returnPeriod' }))).toBe(500);
    expect(store.get(hazardSelectionState('heat'))).toBe(true);
    damageSourceStateEffect(ops, {
      scenario: { hazard: 'heat', parameters: { gwl: 3 } },
      hazardDomains,
    });
    expect(matchRasterScenario({ gwl: 3 }, hazardDomains.heat).linked).toBe(false);
    expect(store.get(dataParamState({ group: 'heat', param: 'gwl' }))).toBe(2);
    expect(store.get(hazardSelectionState('heat'))).toBe(false);
    damageSourceStateEffect(ops, {
      scenario: { hazard: 'heat', parameters: { gwl: 2, slr: 0.5, member: 'b' } },
      hazardDomains,
    });
    expect(store.get(hazardSelectionState('heat'))).toBe(false);
  });

  it('links GWL river raster keys and rejects legacy RCP/year damage scenarios', () => {
    const store = createStore();
    const ops = { get: store.get, set: store.set };
    const hazardDomains = {
      fluvial: {
        paramDefaults: { GWL: 0.75, RP: 100 },
        paramDomains: { GWL: [0.75, 2, 3], RP: [20, 100, 500] },
      },
    };
    damageSourceStateEffect(ops, {
      scenario: { hazard: 'fluvial', parameters: { rcp: 'baseline', epoch: 2010 } },
      hazardDomains,
    });
    expect(store.get(hazardSelectionState('fluvial'))).toBe(false);
    damageSourceStateEffect(ops, {
      scenario: { hazard: 'fluvial', parameters: { gwl: 2 } },
      hazardDomains,
    });
    expect(store.get(hazardSelectionState('fluvial'))).toBe(true);
    expect(
      HAZARD_SOURCE.getDataUrl(
        {
          hazardType: 'fluvial',
          hazardParams: {
            GWL: store.get(dataParamState({ group: 'fluvial', param: 'GWL' })),
            RP: store.get(dataParamState({ group: 'fluvial', param: 'RP' })),
          },
          sourceMetadata: { keys: ['GWL', 'RP'], fixedValues: {} },
        },
        { scheme: 'blues', range: [0, 10] },
      ),
    ).toContain('/fluvial/2/100/');
  });

  it('preserves a synchronised raster selection when sidebar configuration finishes loading', () => {
    const store = createStore();
    const hazardDomains = {
      fluvial: {
        paramDefaults: { gwl: 2, returnPeriod: 100 },
        paramDomains: { gwl: [2, 3], returnPeriod: [100, 500] },
      },
    };
    damageSourceStateEffect({ get: store.get, set: store.set }, {
      scenario: { hazard: 'fluvial', parameters: { gwl: 3 } },
      hazardDomains,
    });
    expect(store.get(dataParamState({ group: 'fluvial', param: 'returnPeriod' }))).toBe(500);

    // The combined sidebar config can arrive after damage/raster discovery.
    store.set(syncExternalConfigState, hazardDomains);
    expect(store.get(dataParamState({ group: 'fluvial', param: 'returnPeriod' }))).toBe(500);
    expect(store.get(dataParamState({ group: 'fluvial', param: 'gwl' }))).toBe(3);

    // Loading another group must not reset an already initialised hazard.
    store.set(syncExternalConfigState, {
      ...hazardDomains,
      risks: { paramDefaults: { sector: 'all' }, paramDomains: { sector: ['all', 'power'] } },
    });
    expect(store.get(dataParamState({ group: 'fluvial', param: 'returnPeriod' }))).toBe(500);
    expect(store.get(dataParamState({ group: 'fluvial', param: 'gwl' }))).toBe(3);
    expect(store.get(dataParamState({ group: 'risks', param: 'sector' }))).toBe('all');

    // Values removed by a catalogue refresh still fall back to valid defaults.
    store.set(syncExternalConfigState, {
      fluvial: { ...hazardDomains.fluvial, paramDomains: { gwl: [2], returnPeriod: [100] } },
    });
    expect(store.get(dataParamState({ group: 'fluvial', param: 'returnPeriod' }))).toBe(100);
    expect(store.get(dataParamState({ group: 'fluvial', param: 'gwl' }))).toBe(2);
  });

  it('links only complete raster catalogue rows, including sparse RP and confidence values', async () => {
    vi.spyOn(api, 'rasterTileSourceDomains').mockResolvedValue({
      data: {
        domains: [
          { type: 'heat', GWL: '2', SLR: '0', rp: '20', confidence: 'None' },
          { type: 'heat', GWL: '2', SLR: '0', rp: '100', confidence: 'None' },
          { type: 'heat', GWL: '3', SLR: '0.5', rp: '500', confidence: '50' },
        ],
      },
    } as never);
    const store = createStore();
    store.set(hazardsMetadataState as PrimitiveAtom<Record<string, Dataset>>, {
      heat: { id: 'heat', has_access: true } as Dataset,
    });
    subscriptions.push(store.sub(hazardDomainState, () => {}));
    await vi.waitFor(() =>
      expect(store.get(hazardDomainState)?.heat?.paramCombinations).toHaveLength(3),
    );
    const hazardDomains = store.get(hazardDomainState);
    const ops = { get: store.get, set: store.set };
    damageSourceStateEffect(ops, {
      scenario: { hazard: 'heat', parameters: { gwl: 2, slr: 0 } },
      hazardDomains,
    });
    expect(store.get(hazardSelectionState('heat'))).toBe(true);
    expect(store.get(dataParamState({ group: 'heat', param: 'returnPeriod' }))).toBe(100);
    expect(store.get(dataParamState({ group: 'heat', param: 'confidence' }))).toBe('None');

    damageSourceStateEffect(ops, {
      scenario: { hazard: 'heat', parameters: { gwl: 2, slr: 0.5 } },
      hazardDomains,
    });
    expect(store.get(hazardSelectionState('heat'))).toBe(false);
    expect(store.get(dataParamState({ group: 'heat', param: 'SLR' }))).toBe(0);

    damageSourceStateEffect(ops, {
      scenario: { hazard: 'heat', parameters: { gwl: 3, slr: 0.5 } },
      hazardDomains,
    });
    expect(store.get(hazardSelectionState('heat'))).toBe(true);
    expect(store.get(dataParamState({ group: 'heat', param: 'GWL' }))).toBe(3);
    expect(store.get(dataParamState({ group: 'heat', param: 'SLR' }))).toBe(0.5);
    expect(store.get(dataParamState({ group: 'heat', param: 'returnPeriod' }))).toBe(500);
    expect(store.get(dataParamState({ group: 'heat', param: 'confidence' }))).toBe(50);
  });

  it('defers damage requests until metadata loads and shares the selected JSON object', async () => {
    let resolveCatalog: (value: unknown) => void;
    const catalog = vi.spyOn(api, 'mapModelScenariosList').mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveCatalog = resolve;
        }) as never,
    );
    const store = createStore();
    subscriptions.push(store.sub(damagesFieldState, () => {}));
    expect(store.get(damagesFieldState)).toBeNull();
    expect(catalog).toHaveBeenCalledWith(expect.objectContaining({ query: { layer: ['roads'] } }));
    resolveCatalog({
      data: [
        { hazard: 'heat', parameters: { gwl: 2, slr: 0.5 }, protection_standard: 0 },
        { hazard: 'heat', parameters: { gwl: 4, slr: 1 }, protection_standard: 0 },
      ],
    });
    await vi.waitFor(() => expect(store.get(damagesFieldState)).not.toBeNull());
    store.set(modelParametersState('damages_expected'), { slr: 1, gwl: 4 });
    store.set(damageSourceState, ['heat']);
    expect(store.get(damagesFieldState).fieldDimensions).toEqual({
      hazard: 'heat',
      parameters: { gwl: 4, slr: 1 },
      protection_standard: 0,
    });
    // A changed asset scope must not reuse the previous scope's result while loading.
    store.set(selectedNetworkLayerIdsState as PrimitiveAtom<string[]>, ['power']);
    expect(store.get(damagesFieldState)).toBeNull();
    resolveCatalog({ data: [] });
    await vi.waitFor(() => expect(catalog).toHaveBeenCalledTimes(2));
  });

  it('uses discovered adaptation dimensions and sends the same parameters to protected-feature queries', async () => {
    const parameters = { gwl: 2, slr: 0.5, options: { member: [1, '1'] } };
    vi.spyOn(api, 'mapModelScenariosList').mockResolvedValue({
      data: [
        { hazard: 'heat', parameters, adaptation_name: 'Shade', adaptation_protection_level: 50 },
      ],
    } as never);
    const request = vi
      .spyOn(sdk, 'mapFeaturesProtectedByList')
      .mockResolvedValue({ data: [] } as never);
    const store = createStore();
    store.set(dataParamState({ group: 'adaptation', param: 'sector' }), 'energy');
    store.set(dataParamState({ group: 'adaptation', param: 'subsector' }), 'power');
    store.set(dataParamState({ group: 'adaptation', param: 'asset_type' }), 'edge');
    store.set(modelParametersState('adaptation'), parameters);
    subscriptions.push(store.sub(adaptationFieldSpecState, () => {}));
    subscriptions.push(store.sub(protectedFeatureAdaptationOptionsState(undefined), () => {}));
    await vi.waitFor(() => expect(store.get(adaptationFieldSpecState)).not.toBeNull());
    expect(store.get(adaptationFieldSpecState).fieldDimensions).toEqual({
      hazard: 'heat',
      parameters,
      adaptation_name: 'Shade',
      adaptation_protection_level: 50,
    });
    await vi.waitFor(() => expect(request).toHaveBeenCalled());
    const query = request.mock.calls[0][0].query;
    expect(JSON.parse(query.parameters)).toEqual(parameters);
    expect(store.get(protectedFeatureScenarioState).parameters).toEqual(parameters);
    store.set(selectionState('assets'), { target: { feature: { id: 456 } } } as never);
    await vi.waitFor(() =>
      expect(request).toHaveBeenLastCalledWith(
        expect.objectContaining({ path: { protector_id: 456 } }),
      ),
    );
  });
});

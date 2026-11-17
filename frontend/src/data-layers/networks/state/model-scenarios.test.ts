import { afterEach, describe, expect, it, vi } from 'vitest';
import { createStore, type PrimitiveAtom } from 'jotai';
import * as api from 'lib/api-client';
import * as sdk from 'lib/api-client/sdk.gen';
import { modelParametersState } from 'lib/model-scenarios/state';
import { dataParamState } from 'lib/state/data-params';
import { damageSourceState } from 'lib/state/damage-map';
import { networksStyleState, selectedNetworkLayerIdsState } from './data-selection';
import { damagesFieldState } from './damage-scenarios';
import { adaptationFieldSpecState } from './layer';
import {
  protectedFeatureAdaptationOptionsState,
  protectedFeatureScenarioState,
} from 'lib/state/protected-features';
import { selectionState } from 'lib/state/interactions/interaction-state';
import { damageSourceStateEffect } from 'app/state/damage-mapping/damage-map';
import { hazardSelectionState } from 'data-layers/hazards/state/data-selection';
import { matchRasterScenario } from 'data-layers/hazards/raster-scenario';
import { HAZARD_SOURCE } from 'data-layers/hazards/source';
import { hazardsMetadataState } from 'data-layers/hazards/state/metadata';
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
  return { ...actual, hazardsMetadataState: atom({}) };
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

const subscriptions: (() => void)[] = [];
afterEach(() => {
  subscriptions.splice(0).forEach((unsubscribe) => unsubscribe());
  vi.restoreAllMocks();
});

describe('model scenario query flow', () => {
  it('drops a restricted persisted hazard and excludes it from all-hazard scenarios', async () => {
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
    store.set(damageSourceState, 'coastal');
    subscriptions.push(store.sub(damagesFieldState, () => {}));
    await vi.waitFor(() => expect(store.get(damagesFieldState)).not.toBeNull());
    expect(store.get(damagesFieldState).fieldDimensions).toEqual({
      hazard: 'all',
      parameters: { gwl: 2 },
      protection_standard: 0,
    });
  });

  it('revalidates an active selection when permissions change while the catalogue is cached', async () => {
    const catalogue = vi.spyOn(api, 'mapModelScenariosList').mockResolvedValue({
      data: [{ hazard: 'coastal', parameters: { gwl: 2 }, protection_standard: 0 }],
    } as never);
    const store = createStore();
    const metadata = hazardsMetadataState as PrimitiveAtom<Record<string, Dataset>>;
    store.set(metadata, { coastal: { id: 'coastal', has_access: true } as Dataset });
    store.set(damageSourceState, 'coastal');
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
    store.set(damageSourceState, 'heat');
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

import { atom } from 'jotai';
import { atomFamily } from 'jotai-family';
import { unwrap } from 'jotai/utils';

import { createClient } from 'lib/api-client/client';
import { mapFeaturesProtectedByList } from 'lib/api-client/sdk.gen';
import { ProtectedFeature } from 'lib/api-client/types.gen';
import { selectionState } from './interactions/interaction-state';
import { VectorTarget } from 'lib/data-map/types';
import {
  modelParametersState,
  scenarioCatalogState,
  scenarioQueryKey,
} from 'lib/model-scenarios/state';
import { parameterKey, selectParameters } from 'lib/model-scenarios/scenarios';
import { viewLayerState } from './layers/view-layers';
import { sectionStyleValueState } from './sections';

const apiClient = createClient({
  baseUrl: '/api',
});

/**
 * Fetch a list of all adaptation options, by feature ID and layer,
 * for features protected by the current selected feature,
 * filtered by model parameters.
 */
export const protectedFeatureScenarioState = atom((get) => {
  const target = get(selectionState('assets'))?.target as VectorTarget;
  const id = target?.feature?.id;
  const catalog =
    id == null
      ? { rows: [] }
      : get(scenarioCatalogState(scenarioQueryKey('adaptation', { protector_id: Number(id) })));
  return {
    protectorId: id == null ? null : Number(id),
    catalog,
    parameters: selectParameters(catalog?.rows ?? [], get(modelParametersState('adaptation'))),
  };
});

const protectedFeatureAdaptationOptionsQuery = atomFamily((parameters?: string) =>
  atom(async (get) => {
    const selection = get(selectionState('assets'));
    const target = selection?.target as VectorTarget;
    if (!target?.feature?.id) {
      return [];
    }
    const selected = get(protectedFeatureScenarioState).parameters;
    if (parameters === undefined && selected === null) return [];
    const { data } = await mapFeaturesProtectedByList({
      client: apiClient,
      throwOnError: true,
      path: {
        protector_id: +target.feature.id,
      },
      query: {
        parameters: parameters ?? parameterKey(selected),
      },
    });
    return data ?? [];
  }),
);

const protectedFeatureAdaptationOptionsCached = atomFamily((parameters?: string) =>
  unwrap(protectedFeatureAdaptationOptionsQuery(parameters), () => []),
);

/**
 * A list of all adaptation options, by feature ID and layer,
 * for features protected by the current selected feature.
 * Components using this atom will not suspend while waiting for the API.
 */
export const protectedFeatureAdaptationOptionsState = atomFamily((parameters?: string) =>
  atom((get) => {
    try {
      const data: ProtectedFeature[] = get(protectedFeatureAdaptationOptionsCached(parameters));
      return { data, error: null };
    } catch (error) {
      return { data: [], error };
    }
  }),
);

/**
 * Fetch a list of layer IDs for the current protected feature query set.
 */
export const protectedFeatureLayersQuery = atom(async (get) => {
  const features = await get(protectedFeatureAdaptationOptionsQuery(undefined));
  return new Set(features?.map((feature) => feature.layer));
});

const protectedFeatureLayersCached = unwrap(
  protectedFeatureLayersQuery,
  (prev) => prev ?? new Set<string>(),
);

/**
 * A set of unique feature layer IDs for the protected feature list.
 */
export const protectedFeatureLayersState = atom((get) => {
  const style = get(sectionStyleValueState('assets'));
  if (!style || style !== 'protectedFeatures') {
    return new Set<string>();
  }
  try {
    return get(protectedFeatureLayersCached);
  } catch {
    return new Set<string>();
  }
});

/**
 * Adaptation options for the selected model scenario and protector.
 */
export const protectedFeatureAdaptationsState = atom((get) => {
  const { data } = get(protectedFeatureAdaptationOptionsState(undefined));
  return data;
});

const viewLayerAdaptationField = atomFamily((viewLayerID: string) =>
  atom((get) => {
    const viewLayer = get(viewLayerState(viewLayerID));
    return viewLayer?.styleParams?.colorMap?.fieldSpec?.field;
  }),
);

export const protectedFeatureLayerDataState = atom((get) => {
  const viewLayersData = new Map();
  const style = get(sectionStyleValueState('assets'));
  if (!style || style !== 'protectedFeatures') {
    return viewLayersData;
  }
  const protectedFeatureAdaptations = get(protectedFeatureAdaptationsState);
  const viewLayerIDs = get(protectedFeatureLayersState);
  viewLayerIDs.forEach((viewLayerID: string) => {
    const field = get(viewLayerAdaptationField(viewLayerID));
    const viewLayerDataEntries: [number, string | number][] = protectedFeatureAdaptations
      ?.filter((row) => row.layer === viewLayerID && !!row[field])
      .map((row) => [row.id, row[field]]);
    const data = viewLayerDataEntries.length > 0 ? Object.fromEntries(viewLayerDataEntries) : null;
    viewLayersData.set(viewLayerID, data);
  });
  return viewLayersData;
});

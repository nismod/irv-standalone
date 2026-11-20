import { atom, type Atom } from 'jotai';
import { atomFamily } from 'jotai-family';
import { unwrap } from 'jotai/utils';
import stringify from 'json-stable-stringify';
import { mapModelScenariosList } from 'lib/api-client';
import type { ModelParameters, ModelScenario, ModelType } from './scenarios';

export interface ScenarioScope {
  layer?: string | string[];
  sector?: string;
  subsector?: string;
  asset_type?: string;
  protector_id?: number;
}

export interface ScenarioCatalog {
  rows: ModelScenario[];
  error?: string;
}

export const modelParametersState = atomFamily((model: ModelType) => {
  // Include the model in the stored value to keep the two selections independent.
  // Parameter sets from different result models need not share a schema.
  const state = atom({ model, parameters: null as ModelParameters | null });
  return atom(
    (get) => get(state).parameters,
    (_get, set, parameters: ModelParameters | null) => {
      set(state, { model, parameters });
    },
  );
});

export const scenarioQueryKey = (model: ModelType, scope: ScenarioScope = {}) =>
  stringify({
    model,
    ...scope,
    ...(scope.layer
      ? { layer: (Array.isArray(scope.layer) ? [...scope.layer] : [scope.layer]).sort() }
      : {}),
  });

export const scenarioCatalogState = atomFamily((key: string): Atom<ScenarioCatalog | undefined> =>
  unwrap(
    atom(async (): Promise<ScenarioCatalog> => {
      const { model, ...scope } = JSON.parse(key);
      // An empty layer selection is distinct from an unfiltered catalogue.
      if (Array.isArray(scope.layer) && !scope.layer.length) return { rows: [] };
      try {
        const { data } = await mapModelScenariosList({
          baseUrl: '/api',
          credentials: 'include',
          throwOnError: true,
          path: { field_group: model },
          query: scope,
        });
        return { rows: data };
      } catch (error) {
        return { rows: [], error: error instanceof Error ? error.message : String(error) };
      }
    }),
    () => undefined,
  ),
);

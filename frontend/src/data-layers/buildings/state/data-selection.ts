import { atom } from 'jotai';
import { unwrap } from 'jotai/utils';

import { mapDatasetsList, mapFeatureLayersList } from 'lib/api-client';
import { atomWithStoredJson } from 'lib/state/map-view/map-url';

export const buildingsStyleState = atom('type');

async function fetchBuildingLayerIds(): Promise<string[]> {
  const datasets: string[] = [];
  let offset = 0;
  const limit = 100;
  while (true) {
    const { data, error } = await mapDatasetsList({
      baseUrl: '/api', credentials: 'include', query: { group: 'buildings', limit, offset },
    });
    if (error || !data) throw error ?? new Error('Missing buildings datasets');
    datasets.push(...data.results.map(({ id }) => id));
    if (!data.next) break;
    if (data.results.length === 0) throw new Error('Empty buildings dataset page');
    offset += data.results.length;
  }
  const datasetIds = new Set(datasets);
  const layers: string[] = [];
  offset = 0;
  while (true) {
    const { data, error } = await mapFeatureLayersList({
      baseUrl: '/api', credentials: 'include', query: { limit, offset },
    });
    if (error || !data) throw error ?? new Error('Missing feature layer metadata');
    layers.push(...data.results.filter((layer) => layer.dataset && datasetIds.has(layer.dataset)).map((layer) => layer.layer_name));
    if (!data.next) return [...new Set(layers)];
    if (data.results.length === 0) throw new Error('Empty feature layer page');
    offset += data.results.length;
  }
}

const buildingLayerIdsQuery = atom(fetchBuildingLayerIds);
export const buildingLayerIdsState = unwrap(buildingLayerIdsQuery, (previous) => previous ?? []);

export type BuildingSelection = Record<string, boolean>;
export const buildingSelectionState = atomWithStoredJson<BuildingSelection>('buiSel', {});

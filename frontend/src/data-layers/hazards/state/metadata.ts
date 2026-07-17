import { atom } from 'jotai';
import { unwrap } from 'jotai/utils';
import { type Dataset, mapDatasetsList } from 'lib/api-client';

async function fetchHazardsMetadata() {
  try {
    const { data, error } = await mapDatasetsList({
      baseUrl: '/api',
      credentials: 'include',
      query: {
        group: 'hazards',
      },
    });
    if (error) {
      console.error('Error fetching hazards metadata:', error);
      return [];
    }
    return data.results;
  } catch (error) {
    console.error('Error fetching hazards metadata:', error);
    return [];
  }
}

const hazardsMetadataQuery = atom(async () => {
  const metadata: Record<string, Dataset> = {};
  const datasets: Dataset[] = await fetchHazardsMetadata();
  datasets.forEach((dataset) => {
    metadata[dataset.id] = dataset;
  });
  return metadata;
});

export const hazardsMetadataState = unwrap(hazardsMetadataQuery, (prev) => prev ?? {});

export const hazardsMapOrderState = atom<string[]>((get) => {
  const metadata = get(hazardsMetadataState);
  return Object.values(metadata)
    .filter((dataset) => dataset.has_access)
    .sort((a, b) => a.stacking_order - b.stacking_order)
    .map((dataset) => dataset.id);
});

export const hazardsUIOrderState = atom<string[]>((get) => {
  const metadata = get(hazardsMetadataState);
  return Object.values(metadata)
    .sort((a, b) => a.display_order - b.display_order)
    .map((dataset) => dataset.id);
});

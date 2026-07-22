import { atom } from 'jotai';
import { unwrap } from 'jotai/utils';
import { type Dataset, mapDatasetsList, rasterTileSource } from 'lib/api-client';

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

const hazardSourceKeysQuery = atom(async (get) => {
  const metadata = get(hazardsMetadataState);
  const datasets = Object.values(metadata);
  const tileSourceEntries = datasets
    .map((dataset) => [dataset.id, dataset.tile_source] as const)
    .filter(([, tileSourceId]) => tileSourceId != null);

  const uniqueTileSourceIds = [...new Set(tileSourceEntries.map(([, tileSourceId]) => tileSourceId))];

  const responses = await Promise.all(
    uniqueTileSourceIds.map(async (sourceId) => {
      const { data, error } = await rasterTileSource({
        baseUrl: '/api',
        path: { source_id: sourceId },
        credentials: 'include',
      });

      if (error) {
        console.error(`Error fetching raster source ${sourceId}:`, error);
        return [sourceId, null] as const;
      }

      return [sourceId, data.keys] as const;
    }),
  );

  const keysBySourceId = Object.fromEntries(responses);

  return Object.fromEntries(
    tileSourceEntries.map(([datasetId, tileSourceId]) => [datasetId, keysBySourceId[tileSourceId] ?? null]),
  ) as Record<string, string[] | null>;
});

export const hazardSourceKeysState = unwrap(hazardSourceKeysQuery, (prev) => prev ?? {});

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

import { atom } from 'jotai';
import { unwrap } from 'jotai/utils';
import { type Dataset, mapDatasetsList, rasterTileSource, rasterTileSourceDomains } from 'lib/api-client';

const DEFAULT_HAZARD_COLOR_SCHEMES: Record<string, { scheme: string; range: [number, number] }> = {
  fluvial: { scheme: 'blues', range: [0, 10] },
  coastal: { scheme: 'greens', range: [0, 10] },
  surface: { scheme: 'purples', range: [0, 10] },
  pluvial: { scheme: 'purples', range: [0, 10] },
  cyclone: { scheme: 'reds', range: [0, 75] },
  storm: { scheme: 'viridis', range: [0, 250] },
};

export function getHazardColorSpec(dataset?: Dataset | null) {
  const fallback = (dataset && DEFAULT_HAZARD_COLOR_SCHEMES[dataset.id]) ?? DEFAULT_HAZARD_COLOR_SCHEMES.pluvial;
  const range =
    dataset?.color_range != null &&
    dataset.color_range.length === 2 &&
    dataset.color_range.every((value) => typeof value === 'number')
      ? ([dataset.color_range[0], dataset.color_range[1]] as [number, number])
      : fallback.range;

  return {
    scheme: dataset?.color_scheme ?? fallback.scheme,
    range,
  };
}

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

type HazardSourceMetadata = {
  keys: string[] | null;
  fixedValues: Record<string, string | null>;
};

export const hazardSourceMetadataState = unwrap(
  atom(async (get) => {
    const metadata = get(hazardsMetadataState);
    const datasets = Object.values(metadata);
    const responses = await Promise.all(
      datasets.map(async (dataset) => {
        if (dataset.tile_source == null) {
          return [dataset.id, { keys: null, fixedValues: {} }] as const;
        }

        const [{ data: sourceData, error: sourceError }, { data: domainData, error: domainError }] = await Promise.all([
          rasterTileSource({
            baseUrl: '/api',
            path: { source_id: dataset.tile_source },
            credentials: 'include',
          }),
          rasterTileSourceDomains({
            baseUrl: '/api',
            path: { dataset_id: dataset.id },
            credentials: 'include',
          }),
        ]);

        if (sourceError) {
          console.error(`Error fetching raster source ${dataset.tile_source}:`, sourceError);
        }
        if (domainError) {
          console.error(`Error fetching raster source domains for ${dataset.id}:`, domainError);
        }

        const keys = sourceData?.keys ?? null;
        const domains = domainData?.domains ?? [];
        const fixedValues = Object.fromEntries(
          (keys ?? []).map((key) => {
            const values = Array.from(new Set(domains.map((entry) => entry[key]).filter((value) => value != null)));
            return [key, values.length === 1 ? values[0] : null];
          }),
        ) as Record<string, string | null>;

        return [dataset.id, { keys, fixedValues }] as const;
      }),
    );

    return Object.fromEntries(responses) as Record<string, HazardSourceMetadata>;
  }),
  (prev) => prev ?? {},
);

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

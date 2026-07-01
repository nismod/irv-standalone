import { atom } from 'jotai';
import { unwrap } from 'jotai/utils';

async function fetchHazardsMetadata() {
  const module = await import('./datasets.json');
  return module.default;
}

const hazardsMetadataQuery = atom(async () => {
  const metadata = {};
  const datasets = await fetchHazardsMetadata();
  datasets.forEach((dataset) => {
    metadata[dataset.id] = dataset;
  });
  return metadata;
});

export const hazardsMetadataState = unwrap(
  hazardsMetadataQuery,
  (prev) => prev ?? {},
);

export const HAZARDS_MAP_ORDER = ['storm', 'cyclone', 'fluvial', 'surface', 'coastal'];
export const HAZARDS_UI_ORDER = ['fluvial', 'surface', 'coastal', 'cyclone', 'storm'];

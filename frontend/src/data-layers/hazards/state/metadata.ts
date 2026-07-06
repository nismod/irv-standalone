import { atom } from 'jotai';
import { unwrap } from 'jotai/utils';

type HazardMetadata = {
  id: string;
  label: string;
  unit: string;
  displayOrder: number;
  stackingOrder: number;
};

async function fetchHazardsMetadata() {
  const module = await import('./datasets.json');
  return module.default;
}

const hazardsMetadataQuery = atom(async () => {
  const metadata: Record<string, HazardMetadata> = {};
  const datasets: HazardMetadata[] = await fetchHazardsMetadata();
  datasets.forEach((dataset) => {
    metadata[dataset.id] = dataset;
  });
  return metadata;
});

export const hazardsMetadataState = unwrap(
  hazardsMetadataQuery,
  (prev) => prev ?? {},
);

export const hazardsMapOrderState = atom<string[]>((get) => {
  const metadata = get(hazardsMetadataState);
  return Object.values(metadata)
    .sort((a, b) => a.stackingOrder - b.stackingOrder)
    .map((dataset) => dataset.id);
});

export const hazardsUIOrderState = atom<string[]>((get) => {
  const metadata = get(hazardsMetadataState);
  return Object.values(metadata)
    .sort((a, b) => a.displayOrder - b.displayOrder)
    .map((dataset) => dataset.id);
});

import { atom } from 'jotai';
import { unwrap } from 'jotai/utils';

async function fetchRisksMetadata() {
  const module = await import('./datasets.json');
  return module.default;
}

export type RiskMetadata = {
  id: string;
  label: string;
  dataUnit: string;
  format: string;
};

export type RisksMetadata = Record<string, RiskMetadata>;

const risksMetadataQuery = atom(async () => {
  const metadata: RisksMetadata = {};
  const datasets = await fetchRisksMetadata();
  datasets.forEach((dataset) => {
    metadata[dataset.id] = dataset;
  });
  return metadata;
});

export const risksMetadataState = unwrap(risksMetadataQuery, (prev) => prev ?? {});

export const riskIdsState = atom((get) => Object.keys(get(risksMetadataState)));

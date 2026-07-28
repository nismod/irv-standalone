import { atom } from 'jotai';
import { unwrap } from 'jotai/utils';

import { type Dataset, mapDatasetsList } from 'lib/api-client';
import { colorCssToRgb, makeConfig } from 'lib/helpers';
import { LegendShapeType } from 'lib/map-shapes/ShapeLegend';

export interface NetworkLayerMetadata {
  id: string;
  type: LegendShapeType;
  label: string;
  color: string;
  minZoom?: number | null;
  deck: [number, number, number, number?];
}

export type NetworksMetadata = Record<string, NetworkLayerMetadata>;
export type NetworkDatasetsMetadata = Record<string, Dataset>;

interface NetworkLayerStyleResponse {
  id: string;
  type: LegendShapeType;
  label: string;
  color: string;
  minZoom?: number | null;
}

interface PaginatedNetworkLayerStyleResponse {
  results?: NetworkLayerStyleResponse[];
}

async function fetchNetworkLayerStyles(): Promise<NetworkLayerStyleResponse[]> {
  try {
    const response = await fetch('/api/map/network-layer-styles', {
      credentials: 'include',
    });
    if (!response.ok) {
      throw new Error(`Failed to fetch network layer styles: ${response.status}`);
    }

    const data = (await response.json()) as
      NetworkLayerStyleResponse[] | PaginatedNetworkLayerStyleResponse;
    return Array.isArray(data) ? data : (data.results ?? []);
  } catch (error) {
    console.error('Error fetching network layer styles:', error);
    return [];
  }
}

async function fetchNetworkDatasets(): Promise<Dataset[]> {
  try {
    const { data, error } = await mapDatasetsList({
      baseUrl: '/api',
      credentials: 'include',
      query: {
        group: 'infrastructure',
      },
    });
    if (error) {
      console.error('Error fetching network datasets metadata:', error);
      return [];
    }
    return data.results;
  } catch (error) {
    console.error('Error fetching network datasets metadata:', error);
    return [];
  }
}

const networksMetadataQuery = atom(async () => {
  const styles = await fetchNetworkLayerStyles();
  return makeConfig<NetworkLayerMetadata, string>(
    styles.map((style) => ({
      ...style,
      deck: colorCssToRgb(style.color),
    })),
  );
});

export const networksMetadataState = unwrap(networksMetadataQuery, (prev) => prev ?? {});

const networkDatasetsMetadataQuery = atom(async () => {
  const metadata: NetworkDatasetsMetadata = {};
  const datasets = await fetchNetworkDatasets();
  datasets.forEach((dataset) => {
    metadata[dataset.id] = dataset;
  });
  return metadata;
});

export const networkDatasetsMetadataState = unwrap(
  networkDatasetsMetadataQuery,
  (prev) => prev ?? {},
);

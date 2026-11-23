import { atom } from 'jotai';
import { unwrap } from 'jotai/utils';

import { type FeatureLayer, mapFeatureLayersList } from 'lib/api-client';
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
export type NetworkFeatureLayersMetadata = Record<string, FeatureLayer>;

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

async function fetchNetworkFeatureLayers(): Promise<FeatureLayer[]> {
  try {
    const layers: FeatureLayer[] = [];
    const limit = 100;
    while (true) {
      const { data, error } = await mapFeatureLayersList({
        baseUrl: '/api',
        credentials: 'include',
        query: { limit, offset: layers.length },
      });
      if (error || !data) throw error ?? new Error('Missing feature layer metadata');
      layers.push(...data.results);
      if (!data.next) return layers;
      if (data.results.length === 0) throw new Error('Empty feature layer page');
    }
  } catch (error) {
    console.error('Error fetching network feature layer metadata:', error);
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

const networkFeatureLayersMetadataQuery = atom(async () => {
  const metadata: NetworkFeatureLayersMetadata = {};
  const layers = await fetchNetworkFeatureLayers();
  layers.forEach((layer) => {
    metadata[layer.layer_name] = layer;
  });
  return metadata;
});

export const networkFeatureLayersMetadataState = unwrap(
  networkFeatureLayersMetadataQuery,
  (prev) => prev ?? {},
);

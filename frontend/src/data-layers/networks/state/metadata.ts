import { atom } from 'jotai';
import { unwrap } from 'jotai/utils';

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

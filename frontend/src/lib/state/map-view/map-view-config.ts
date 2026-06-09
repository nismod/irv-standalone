import { atom } from 'jotai';

import { MapConfig, mapConfigList } from '../../api-client';

interface MapViewConfig {
  initialViewState: {
    latitude: number;
    longitude: number;
    zoom: number;
  };
  viewLimits: {
    minZoom?: number;
    maxZoom?: number;
    minPitch?: number;
    maxPitch?: number;
  };
}

const defaultViewConfig: MapViewConfig = {
  initialViewState: {
    latitude: 0,
    longitude: 0,
    zoom: 0,
  },
  viewLimits: {
    minZoom: 0,
    maxZoom: 0,
    maxPitch: 0,
  },
};

function configFromApiResponse(data: MapConfig[]): MapViewConfig {
  const bareState = {} as Record<string, number>;
  data.forEach(({ config_name, config_value }) => {
    const n = Number(config_value);
    if (Number.isFinite(n)) {
      bareState[config_name] = n;
    }
  });
  return {
    initialViewState: {
      latitude: bareState.latitude ?? defaultViewConfig.initialViewState.latitude,
      longitude: bareState.longitude ?? defaultViewConfig.initialViewState.longitude,
      zoom: bareState.zoom ?? defaultViewConfig.initialViewState.zoom,
    },
    viewLimits: {
      minZoom: bareState.minZoom ?? defaultViewConfig.viewLimits.minZoom,
      maxZoom: bareState.maxZoom ?? defaultViewConfig.viewLimits.maxZoom,
      maxPitch: bareState.maxPitch ?? defaultViewConfig.viewLimits.maxPitch,
    },
  }
}

async function fetchMapViewConfig(): Promise<MapViewConfig> {
  try {
    const { data, error } = await mapConfigList({
      baseUrl: '/api',
      credentials: 'include',
    });
    if (error) {
      throw new Error(`Failed to fetch map view config: ${JSON.stringify(error)}`);
    }
    if (!data?.results) {
      throw new Error('No results in map view config response');
    }
    return configFromApiResponse(data.results);
  } catch (error) {
    console.error('Error fetching map view config:', error);
    // Return default config on error
    return defaultViewConfig;
  }
}

export const mapViewConfig = atom(fetchMapViewConfig());

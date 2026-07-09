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

type MapViewConfigNumberKey =
  | keyof MapViewConfig['initialViewState']
  | keyof MapViewConfig['viewLimits'];

const mapViewConfigNumberKeys = new Set<string>([
  'latitude',
  'longitude',
  'zoom',
  'minZoom',
  'maxZoom',
  'minPitch',
  'maxPitch',
]);

const defaultViewConfig: MapViewConfig = {
  initialViewState: {
    latitude: 0,
    longitude: 0,
    zoom: 0,
  },
  viewLimits: {
    minZoom: 0,
    maxZoom: 0,
    minPitch: 0,
    maxPitch: 0,
  },
};

function isMapViewConfigNumberKey(configName: string): configName is MapViewConfigNumberKey {
  return mapViewConfigNumberKeys.has(configName);
}

function configFromApiResponse(data: MapConfig[]): MapViewConfig {
  const bareState: Partial<Record<MapViewConfigNumberKey, number>> = {};
  data.forEach(({ config_name, config_value, config_type }) => {
    if (config_type !== 'number' || !isMapViewConfigNumberKey(config_name)) {
      return;
    }

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
      minPitch: bareState.minPitch ?? defaultViewConfig.viewLimits.minPitch,
      maxPitch: bareState.maxPitch ?? defaultViewConfig.viewLimits.maxPitch,
    },
  };
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

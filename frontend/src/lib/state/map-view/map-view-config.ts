import { atom } from 'jotai';
import { unwrap } from 'jotai/utils';

import { MapConfig, mapConfigList } from '../../api-client';

interface MapViewConfig {
  app: {
    name: string;
  };
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
type MapViewConfigStringKey = 'appName';

const mapViewConfigNumberKeys = new Set<string>([
  'latitude',
  'longitude',
  'zoom',
  'minZoom',
  'maxZoom',
  'minPitch',
  'maxPitch',
]);
const mapViewConfigStringKeys = new Set<string>(['appName']);

const defaultViewConfig: MapViewConfig = {
  app: {
    name: '',
  },
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

function isMapViewConfigStringKey(configName: string): configName is MapViewConfigStringKey {
  return mapViewConfigStringKeys.has(configName);
}

function configFromApiResponse(data: MapConfig[]): MapViewConfig {
  const numberState: Partial<Record<MapViewConfigNumberKey, number>> = {};
  const stringState: Partial<Record<MapViewConfigStringKey, string>> = {};
  data.forEach(({ config_name, config_value, config_type }) => {
    if (config_type === 'string' && isMapViewConfigStringKey(config_name)) {
      stringState[config_name] = String(config_value).trim();
      return;
    }

    if (config_type === 'number' && isMapViewConfigNumberKey(config_name)) {
      const n = Number(config_value);
      if (Number.isFinite(n)) {
        numberState[config_name] = n;
      }
    }
  });
  return {
    app: {
      name: stringState.appName || defaultViewConfig.app.name,
    },
    initialViewState: {
      latitude: numberState.latitude ?? defaultViewConfig.initialViewState.latitude,
      longitude: numberState.longitude ?? defaultViewConfig.initialViewState.longitude,
      zoom: numberState.zoom ?? defaultViewConfig.initialViewState.zoom,
    },
    viewLimits: {
      minZoom: numberState.minZoom ?? defaultViewConfig.viewLimits.minZoom,
      maxZoom: numberState.maxZoom ?? defaultViewConfig.viewLimits.maxZoom,
      minPitch: numberState.minPitch ?? defaultViewConfig.viewLimits.minPitch,
      maxPitch: numberState.maxPitch ?? defaultViewConfig.viewLimits.maxPitch,
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
const mapViewConfigQuery = atom(fetchMapViewConfig);

export const mapViewConfig = unwrap(mapViewConfigQuery, (prev) => prev ?? defaultViewConfig);

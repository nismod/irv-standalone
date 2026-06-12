import { HazardParams } from 'data-layers/hazards/state/data-selection';
import { atom } from 'jotai';
import { atomFamily } from 'jotai-family';
import { unwrap } from 'jotai/utils';

import { rasterTileSourceDomains } from 'lib/api-client';
import {
  inferDependenciesFromData,
  inferDomainsFromData,
} from 'lib/controls/data-params';
import { type DataParamGroupConfig } from 'lib/controls/data-params';

type HazardType = 'fluvial' | 'surface' | 'coastal' | 'cyclone';
type HazardParamGroupConfig = DataParamGroupConfig<HazardParams>;
export type HazardDomains = Record<HazardType, HazardParamGroupConfig>;

const hazardTypes: HazardType[] = ['fluvial', 'surface', 'coastal', 'cyclone'];

async function fetchRasterSourceDomains() {
  const { data, error } = await rasterTileSourceDomains({
    baseUrl: '/api',
    path: {
      source_id: 1,
    },
    credentials: 'include',
  });
  if (error) {
    console.error('Error fetching raster source domains:', error);
    return [];
  }
  return data.domains;
}

const rasterSourceQuery = atom(fetchRasterSourceDomains);

const rasterSourceData = unwrap(rasterSourceQuery, (prev) => prev ?? []);

const rasterDomainsByType = atomFamily((type: HazardType) => {
  return atom((get) => {
    const data = get(rasterSourceData);
    const entriesOfType = data.filter((entry) => entry.type === type);
    const inferredDomains = inferDomainsFromData(entriesOfType);
    if (!inferredDomains) {
      return null;
    }
    return {
      epoch: inferredDomains.epoch.map((value) => Number(value)).sort((a, b) => a - b),
      rcp: inferredDomains.rcp.map((value) => value.replace('x', '.')),
      confidence: inferredDomains.confidence,
      returnPeriod: inferredDomains.rp.map((value) => Number(value)).sort((a, b) => a - b),
    };
  });
});

const rasterDependenciesByType = atomFamily((type: HazardType) => {
  return atom((get) => {
    const data = get(rasterSourceData);
    const entriesOfType = data.filter((entry) => entry.type === type);
    entriesOfType.forEach((entry) => {
      entry.rcp = entry.rcp.replace('x', '.');
    });
    return inferDependenciesFromData(entriesOfType, {
      rcp: ['epoch'],
    });
  });
});

const hazardParamGroup = atomFamily((type: HazardType) => {
  return atom((get) => {
    const paramDomains = get(rasterDomainsByType(type));
    if (!paramDomains) {
      return null;
    }
    const paramDefaults = {
      returnPeriod: 100,
      epoch: 2010,
      rcp: 'baseline',
      confidence: type === 'cyclone' ? 50 : 'None',
    };
    const paramDependencies = get(rasterDependenciesByType(type));
    return {
      paramDomains,
      paramDefaults,
      paramDependencies,
    };
  });
});

export const hazardDomainState = atom<HazardDomains | null>((get) => {
  const baseState = {} as HazardDomains;
  hazardTypes.forEach((type) => {
    baseState[type] = get(hazardParamGroup(type));
  });
  return baseState;
});

import { HazardParams } from 'data-layers/hazards/state/data-selection';
import { atom } from 'jotai';
import { atomFamily } from 'jotai-family';
import { unwrap } from 'jotai/utils';

import { rasterTileSourceDomains } from 'lib/api-client';
import {
  inferDependenciesFromData,
  inferDomainsFromData,
} from 'lib/controls/data-params';
import { type DataParamGroupConfig, type ParamDomain } from 'lib/controls/data-params';
import { hazardsMetadataState } from './metadata';

type HazardParamGroupConfig = DataParamGroupConfig<HazardParams>;
export type HazardDomains = Record<string, HazardParamGroupConfig | null>;
type RasterSourceDomainEntry = Record<string, string>;

async function fetchRasterSourceDomains(hazardIds: string[]) {
  const responses = await Promise.all(
    hazardIds.map((datasetId) =>
      rasterTileSourceDomains({
        baseUrl: '/api',
        path: { dataset_id: datasetId },
        credentials: 'include',
      }),
    ),
  );

  return Object.fromEntries(
    responses.map(({ data, error }, index) => {
      const hazardType = hazardIds[index];
      if (error) {
        console.error(`Error fetching ${hazardType} raster source domains:`, error);
        return [hazardType, []];
      }
      return [hazardType, data.domains];
    }),
  ) as Record<string, RasterSourceDomainEntry[]>;
}

const rasterSourceQuery = atom(async (get) => {
  const metadata = get(hazardsMetadataState);
  const hazardIds = Object.keys(metadata);
  return fetchRasterSourceDomains(hazardIds);
});

const rasterSourceData = unwrap(
  rasterSourceQuery,
  (prev) => prev ?? {},
);

function getEntriesForType(data: Record<string, RasterSourceDomainEntry[]>, type: string) {
  const entries = data[type] ?? [];
  if (entries.length === 0) {
    return [];
  }

  if (!entries.some((entry) => 'type' in entry)) {
    return entries;
  }

  const filteredEntries = entries.filter((entry) => entry.type === type);
  return filteredEntries.length > 0 ? filteredEntries : entries;
}

function withDefinedDomains<T extends Record<string, ParamDomain | undefined>>(obj: T) {
  return Object.fromEntries(
    Object.entries(obj).filter(([, value]) => value != null),
  ) as Partial<{ [K in keyof T]: Exclude<T[K], undefined> }>;
}

function withDefinedDefaults<T extends Record<string, HazardParams[keyof HazardParams] | undefined>>(obj: T) {
  return Object.fromEntries(
    Object.entries(obj).filter(([, value]) => value != null),
  ) as Partial<{ [K in keyof T]: Exclude<T[K], undefined> }>;
}

const PARAM_KEY_ALIASES: Record<string, string> = {
  rp: 'returnPeriod',
};

function normaliseParamKey(key: string) {
  return PARAM_KEY_ALIASES[key] ?? key;
}

function normaliseParamValue(value: string) {
  const numericValue = Number(value);
  if (value.trim() !== '' && Number.isFinite(numericValue)) {
    return numericValue;
  }
  if (typeof value === 'string' && value.includes('x')) {
    return value.replace('x', '.');
  }
  return value;
}

function buildParamDomains(entries: RasterSourceDomainEntry[]) {
  const inferredDomains = inferDomainsFromData(entries);
  if (!inferredDomains) {
    return null;
  }

  const paramDomains = Object.fromEntries(
    Object.entries(inferredDomains)
      .filter(([key]) => key !== 'type')
      .map(([key, values]) => {
        const paramKey = normaliseParamKey(key);
        const mappedValues = values.map((value) => normaliseParamValue(String(value)));

        const uniqueValues = Array.from(new Set(mappedValues.map((value) => JSON.stringify(value)))).map(
          (value) => JSON.parse(value),
        );

        const sortedValues =
          uniqueValues.every((value) => typeof value === 'number')
            ? [...uniqueValues].sort((a, b) => Number(a) - Number(b))
            : uniqueValues;

        return [paramKey, sortedValues];
      }),
  );

  return withDefinedDomains(paramDomains as Record<string, ParamDomain | undefined>);
}

function buildParamDefaults(type: string, paramDomains: Record<string, ParamDomain>) {
  return withDefinedDefaults(
    Object.fromEntries(
      Object.entries(paramDomains).map(([key, values]) => {
        const preferredDefault = (
          {
            returnPeriod: 100,
            epoch: 2010,
            rcp: 'baseline',
            confidence: type === 'cyclone' ? 50 : 'None',
          } as Record<string, string | number>
        )[key];

        const value = preferredDefault != null && values.includes(preferredDefault)
          ? preferredDefault
          : values[0];

        return [key, value];
      }),
    ) as Record<string, HazardParams[keyof HazardParams] | undefined>,
  );
}

function normaliseDependencyEntries(entries: RasterSourceDomainEntry[]) {
  return entries.map((entry) =>
    Object.fromEntries(
      Object.entries(entry)
        .filter(([key]) => key !== 'type')
        .map(([key, value]) => [normaliseParamKey(key), normaliseParamValue(value)]),
    ),
  );
}

const rasterDomainsByType = atomFamily((type: string) => {
  return atom((get) => {
    const data = get(rasterSourceData);
    const entriesOfType = getEntriesForType(data, type);
    return buildParamDomains(entriesOfType) as DataParamGroupConfig<HazardParams>['paramDomains'] | null;
  });
});

const rasterDependenciesByType = atomFamily((type: string) => {
  return atom((get) => {
    const data = get(rasterSourceData);
    const entriesOfType = normaliseDependencyEntries(getEntriesForType(data, type));

    if (entriesOfType.length === 0) {
      return {};
    }

    const dependencySpec = {} as Record<string, string[]>;
    if (entriesOfType.some((entry) => 'rcp' in entry) && entriesOfType.some((entry) => 'epoch' in entry)) {
      dependencySpec.rcp = ['epoch'];
    }

    if (Object.keys(dependencySpec).length === 0) {
      return {};
    }

    return inferDependenciesFromData(entriesOfType, dependencySpec);
  });
});

const hazardParamGroup = atomFamily((type: string) => {
  return atom((get) => {
    const paramDomains = get(rasterDomainsByType(type));
    if (!paramDomains) {
      return null;
    }
    const paramDefaults = buildParamDefaults(type, paramDomains as Record<string, ParamDomain>) as DataParamGroupConfig<HazardParams>['paramDefaults'];
    const paramDependencies = get(rasterDependenciesByType(type));
    return {
      paramDomains,
      paramDefaults,
      paramDependencies,
    } as HazardParamGroupConfig;
  });
});

export const hazardDomainState = atom<HazardDomains | null>((get) => {
  const metadata = get(hazardsMetadataState);
  const baseState = {} as HazardDomains;
  Object.keys(metadata).forEach((type) => {
    baseState[type] = get(hazardParamGroup(type));
  });
  return baseState;
});

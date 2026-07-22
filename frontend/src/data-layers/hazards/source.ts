import { type HazardParams } from './state/data-selection';

const API_KEY_ALIASES: Record<string, keyof HazardParams | 'hazardType'> = {
  type: 'hazardType',
  rp: 'returnPeriod',
};
const LEGACY_SOURCE_KEYS = ['type', 'rp', 'rcp', 'epoch', 'confidence'];

function getDefaultHazardParams(hazardType: string): HazardParams {
  return {
    returnPeriod: hazardType === 'storm' ? 0 : 100,
    rcp: 'baseline',
    epoch: 2010,
    confidence: hazardType === 'cyclone' ? 50 : 'None',
    speed: hazardType === 'storm' ? 30 : undefined,
  };
}

function getRasterSourceValue(
  key: string,
  hazardType: string,
  hazardParams: HazardParams,
) {
  if (key === 'type') {
    return hazardType === 'storm' ? `storm${hazardParams.speed ?? 0}` : hazardType;
  }

  const paramKey = API_KEY_ALIASES[key] ?? key;
  const value =
    paramKey === 'hazardType'
      ? hazardType
      : hazardParams[paramKey as keyof HazardParams];

  if (key === 'rcp' && value != null) {
    return String(value).replace('.', 'x');
  }

  return value ?? '';
}

export const HAZARD_SOURCE = {
  getDataUrl(
    {
      hazardType,
      hazardParams = {},
      sourceKeys = [],
    }: { hazardType: string; hazardParams?: Partial<HazardParams>; sourceKeys?: string[] | null },
    { scheme, range }: { scheme: string; range: [number, number] },
  ) {
    const resolvedHazardParams = {
      ...getDefaultHazardParams(hazardType),
      ...(Object.fromEntries(
        Object.entries(hazardParams).filter(([, v]) => v != null),
      ) as Partial<HazardParams>),
    };

    const serialisedKeys = (sourceKeys?.length ? sourceKeys : LEGACY_SOURCE_KEYS)
      .map((key) => getRasterSourceValue(key, hazardType, resolvedHazardParams))
      .join('/');

    return `/api/tiles/raster/${hazardType}/${serialisedKeys}/{z}/{x}/{y}.png?colormap=${scheme}&stretch_range=[${range[0]},${range[1]}]`;
  },
};

import { type HazardParams } from './state/data-selection';

const API_KEY_ALIASES: Record<string, keyof HazardParams | 'hazardType'> = {
  type: 'hazardType',
  rp: 'returnPeriod',
};

export type HazardSourceMetadata = {
  keys: string[];
  fixedValues: Record<string, string | null>;
};

function getRasterSourceValue(
  key: string,
  hazardType: string,
  hazardParams: Partial<HazardParams>,
  fixedValues: Record<string, string | null> = {},
) {
  const fixedValue = fixedValues[key];
  if (fixedValue != null) {
    return fixedValue;
  }

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
      sourceMetadata,
    }: { hazardType: string; hazardParams?: Partial<HazardParams>; sourceMetadata: HazardSourceMetadata },
    { scheme, range }: { scheme: string; range: [number, number] },
  ) {
    const sourceValues = sourceMetadata.keys.map((key) =>
      getRasterSourceValue(key, hazardType, hazardParams, sourceMetadata.fixedValues),
    );
    if (sourceValues.some((value) => value == null || value === '')) {
      return null;
    }

    const serialisedKeys = sourceValues.join('/');

    return `/api/tiles/raster/${hazardType}/${serialisedKeys}/{z}/{x}/{y}.png?colormap=${scheme}&stretch_range=[${range[0]},${range[1]}]`;
  },
};

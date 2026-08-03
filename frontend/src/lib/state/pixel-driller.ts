import { Atom, atom } from 'jotai';
import { atomFamily } from 'jotai-family';
import { unwrap } from 'jotai/utils';
import { atomWithStoredJson } from './map-view/map-url';

export type PixelDomain = 'fluvial' | 'surface' | 'coastal' | 'cyclone';

// Base type for pixel record keys - all keys are optional strings
export type PixelRecordKeys = Record<string, string | number | undefined>;
type PixelValue = string | number | null;

// Generic pixel record that accepts a specific keys type
export interface PixelRecord<TKeys extends PixelRecordKeys = PixelRecordKeys> {
  value: number | null;
  layer: {
    domain: PixelDomain;
    keys: TKeys;
    id: string;
  };
}

type PixelData = {
  [key: string]: PixelValue[];
};

type Row = {
  id: number | string;
  [key: string]: PixelValue;
};

export type PixelDataRecord = PixelRecordKeys & {
  epoch?: number;
  rp?: number;
  value: number | null;
  variable: string;
  unit: string;
};

export type LayerParam = Record<string, PixelValue | undefined>;

const dataCache = new Map<string, PixelData>();

type MapLocation = {
  lat: number;
  lon: number;
};

/**
 * Latitude and longitude of the selected map pixel.
 */
export const pixelSelectionState = atomWithStoredJson<MapLocation | null>(
  'site',
  null as MapLocation | null,
);

/**
 * Query to fetch hazard data for the selected map pixel.
 */
const pixelDrillerQuery: Atom<Promise<PixelData | null>> = atom(async (get) => {
  const pixelSelection = get(pixelSelectionState);
  if (!pixelSelection) {
    return Promise.resolve(null);
  }
  const { lat, lon } = pixelSelection;
  const roundedLat = lat.toFixed(4);
  const roundedLon = lon.toFixed(4);
  const key = `${roundedLat}-${roundedLon}`;
  if (dataCache.has(key)) {
    return dataCache.get(key) ?? null;
  }
  const response = await fetch(`/api/pixel/${roundedLon}/${roundedLat}`);
  if (!response.ok) {
    return null;
  }
  const data: PixelData = await response.json();
  dataCache.set(key, data);
  return data;
});

/**
 * Loadable state for the current pixel driller data.
 */
export const pixelDrillerDataState: Atom<PixelData | null> = unwrap(
  pixelDrillerQuery,
  (prev) => prev ?? null,
);

/**
 * Column headers for the pixel driller data tables.
 */
export const pixelDrillerDataHeaders: Atom<string[]> = atom((get) => {
  const pixelData = get(pixelDrillerDataState);
  if (!pixelData) {
    return [];
  }
  const headers = Object.keys(pixelData);
  return headers;
});

/**
 * Set of return periods for a given hazard.
 */
export const pixelDrillerDataRPs: (hazard: string) => Atom<Set<number>> = atomFamily(
  (hazard: string) =>
    atom((get) => {
      const pixelDataRows = get(mapDataArraysToRowObjects);
      if (!pixelDataRows) {
        return new Set<number>();
      }
      const data = getFilteredPixelData(pixelDataRows, hazard);
      return new Set(
        data.flatMap((d) => (typeof d.rp === 'number' ? [d.rp] : [])),
      );
    }),
);

/**
 * Map a collection of data arrays to a single array of row objects.
 * @param data
 * @returns
 */
const mapDataArraysToRowObjects = atom<Row[]>((get) => {
  const data = get(pixelDrillerDataState);
  if (!data) {
    return [];
  }
  const keys = Object.keys(data);
  return data[keys[0]].map((_, rowNumber) => {
    const row = { id: rowNumber };
    keys.forEach((key) => {
      row[key] = data[key][rowNumber];
    });
    return row;
  });
});

/**
 * Filter pixel data by hazard and the supplied layer dimensions.
 * @param pixelData
 * @param headers
 * @param hazard
 * @param parameters
 * @returns
 */
function getFilteredPixelData(
  pixelDataRows: Row[],
  hazard: string,
  parameters: LayerParam = {},
): Row[] {
  return pixelDataRows
    .filter((row) => row.hazard === hazard)
    .filter((row) =>
      Object.entries(parameters).every(
        ([key, value]) => value === undefined || row[key] === value,
      ),
    );
}

/**
 * Reduce a set of data rows down to a single row with multiple RP columns.
 * @param data
 * @param hazard
 * @param parameters
 * @returns
 */
function reducePixelDataRow(
  data: Row[],
  hazard: string,
  parameters: LayerParam,
): Row | null {
  if (!data.length) {
    return null;
  }
  const { variable, unit } = data[0];
  const row = {
    id: `${hazard}-${JSON.stringify(parameters)}`,
    variable,
    unit,
    hazard,
    ...Object.fromEntries(
      Object.entries(parameters).map(([key, value]) => [
        key,
        value,
      ]),
    ),
  };
  data.forEach((d) => {
    if (typeof d.rp !== 'number') return;
    const value = typeof d.band_data === 'number' ? d.band_data : 0;
    row[`rp-${d.rp}`] = value > 0.005 ? value.toFixed(2) : '-';
  });
  return row;
}

type PixelDrillerRowsKey = {
  pixel_layer: string;
  layerParams: LayerParam[];
  _serialized?: string;
};

function createPixelDrillerRowsKey(
  pixel_layer: string,
  layerParams: LayerParam[],
): PixelDrillerRowsKey {
  const serialized = layerParams
    .map((parameters) => JSON.stringify(parameters))
    .join(',');
  return { pixel_layer, layerParams, _serialized: serialized };
}

/**
 * Rows of pixel driller data for a specific pixel_layer, grouped by dimensions.
 */
export const pixelDrillerDataRows = ({
  pixel_layer,
  layerParams,
}: PixelDrillerRowsKey): Atom<Row[]> => {
  const key = createPixelDrillerRowsKey(pixel_layer, layerParams);
  return pixelDrillerDataRowsFamily(key);
};

const pixelDrillerDataRowsFamily = atomFamily(
  ({ pixel_layer, layerParams }: PixelDrillerRowsKey) =>
    atom((get) => {
      const pixelDataRows = get(mapDataArraysToRowObjects);
      if (!pixelDataRows) {
        return [];
      }
      return layerParams
        .map((parameters) => {
          const data = getFilteredPixelData(pixelDataRows, pixel_layer, parameters);
          const reduced = reducePixelDataRow(data, pixel_layer, parameters);
          return reduced;
        })
        .filter((row): row is Row => row !== null);
    }),
  (a, b) => a.pixel_layer === b.pixel_layer && a._serialized === b._serialized,
);

/**
 * Data records for a specific pixel_layer. Grouped by dimensions, but not reduced to a
 * single row per group. Used for downloads and charts that require the RP as a variable instead of a column.
 */
export const pixelDrillerDataRecords = ({ pixel_layer, layerParams }: PixelDrillerRowsKey) => {
  const key = createPixelDrillerRowsKey(pixel_layer, layerParams);
  return pixelDrillerDataRecordsFamily(key);
};

const pixelDrillerDataRecordsFamily = atomFamily(
  ({ pixel_layer, layerParams }: PixelDrillerRowsKey) =>
    atom((get) => {
      const pixelDataRows = get(mapDataArraysToRowObjects);
      if (!pixelDataRows) {
        return [];
      }
      return layerParams
        .flatMap((parameters) =>
          getFilteredPixelData(pixelDataRows, pixel_layer, parameters),
        )
        .filter((row) => row !== null)
        .map((row) => ({
          ...Object.fromEntries(
            Object.entries(row).filter(
              ([key]) => !['id', 'hazard', 'band_data'].includes(key),
            ),
          ),
          value: typeof row.band_data === 'number' ? row.band_data : null,
          variable: String(row.variable ?? ''),
          unit: String(row.unit ?? ''),
        }));
    }),
  (a, b) => a.pixel_layer === b.pixel_layer && a._serialized === b._serialized,
);

const PIXEL_DOMAINS = new Set<PixelDomain>(['fluvial', 'surface', 'coastal', 'cyclone']);

const pixelDrillerRecords = atom((get) => {
  const selectedData = get(pixelDrillerDataState);
  if (!selectedData?.key || !selectedData.hazard || !selectedData.band_data) {
    return [];
  }
  return selectedData.key
    .map((_, i): PixelRecord | null => {
      const domain = selectedData.hazard[i];
      if (!PIXEL_DOMAINS.has(domain as PixelDomain)) {
        return null;
      }

      const keys = Object.fromEntries(
        Object.entries(selectedData)
          .filter(([key]) => !['hazard', 'band_data'].includes(key))
          .map(([key, values]) => [key, values[i]]),
      );

      return {
        value: typeof selectedData.band_data[i] === 'number' ? selectedData.band_data[i] : null,
        layer: {
          domain: domain as PixelDomain,
          id: String(selectedData.key[i] ?? `${domain}-${i}`),
          keys,
        },
      };
    })
    .filter((record): record is PixelRecord => record !== null);
});

function fixedPrecisionNumber(n: number | null, precision: number): number | null {
  if (Number.isFinite(n)) {
    return Number(n.toPrecision(precision));
  }
  return n;
}

export const pixelDrillerExportRecords = atom<PixelRecord[]>((get) => {
  const records = get(pixelDrillerRecords);
  return records.map((record) => ({
    value: fixedPrecisionNumber(record.value, 3),
    layer: {
      ...record.layer,
    },
  }));
});

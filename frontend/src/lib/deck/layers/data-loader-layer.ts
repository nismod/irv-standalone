import { DataFetcher, DataLoader } from 'lib/data-loader/data-loader';
import { getFeatureId } from '../utils/get-feature-id';
import { MapGeoJSONFeature } from 'maplibre-gl';

export interface DataLoaderOptions {
  dataLoader: DataLoader;
  dataFetcher?: DataFetcher;
}

/**
 * Load data from the attributes API for every feature in a tile.
 */
export function dataLoaderLayer(tileProps, { dataLoader, dataFetcher }: DataLoaderOptions) {
  const {
    tile: { content },
  } = tileProps;
  if (content && dataLoader) {
    const ids: number[] = [
      ...new Set<number>(
        content
          .map((f: MapGeoJSONFeature) => getFeatureId(f))
          .filter((id: number | undefined) => Number.isSafeInteger(id) && id > 0),
      ),
    ];
    if (!ids.length) return null;
    dataLoader?.loadData(dataFetcher, ids);
  }

  return null;
}

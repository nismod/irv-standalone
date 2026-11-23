import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createStore } from 'jotai';
import {
  mapRasterLayersList,
  rasterTileSource,
  rasterTileSourceDomains,
  type RasterLayer,
} from 'lib/api-client';
import { fetchHazardsMetadata, hazardSourceMetadataState } from './metadata';
import { hazardDomainState } from './domains';

vi.mock('lib/api-client', () => ({
  mapRasterLayersList: vi.fn(),
  rasterTileSource: vi.fn(),
  rasterTileSourceDomains: vi.fn(),
}));

beforeEach(() => vi.resetAllMocks());

describe('raster catalogue', () => {
  it('loads all hazard pages', async () => {
    vi.mocked(mapRasterLayersList)
      .mockResolvedValueOnce({
        data: { results: [{ id: 'first' }], next: 'next', count: 2 },
      } as never)
      .mockResolvedValueOnce({
        data: { results: [{ id: 'second' }], next: null, count: 2 },
      } as never);
    expect((await fetchHazardsMetadata()).map((layer) => layer.id)).toEqual(['first', 'second']);
    expect(vi.mocked(mapRasterLayersList).mock.calls[1][0]?.query).toEqual({
      group: 'hazards',
      limit: 100,
      offset: 1,
    });
  });
});

describe('hazard source access', () => {
  beforeEach(() => {
    const layers = [
      { id: 'fluvial', dataset: 'fluvial', has_access: true, tile_source: 1 },
      { id: 'surface', dataset: 'surface', has_access: false, tile_source: 2 },
      { id: 'coastal', dataset: null, group: null, has_access: false, tile_source: 3 },
    ] as RasterLayer[];
    vi.mocked(mapRasterLayersList).mockResolvedValue({
      data: { results: layers, next: null, count: layers.length },
    } as never);
    vi.mocked(rasterTileSource).mockResolvedValue({ data: { keys: ['rp'] } } as never);
    vi.mocked(rasterTileSourceDomains).mockResolvedValue({
      data: { domains: [{ rp: '100' }] },
    } as never);
  });

  it('fetches source metadata only for accessible hazards', async () => {
    // A fresh store keeps request assertions independent of unfinished Storybook requests.
    const store = createStore();
    const unsubscribe = store.sub(hazardSourceMetadataState, () => {});
    try {
      await vi.waitFor(() =>
        expect(store.get(hazardSourceMetadataState)).toEqual({
          fluvial: { keys: ['rp'], fixedValues: { rp: '100' } },
          surface: { keys: null, fixedValues: {} },
          coastal: { keys: null, fixedValues: {} },
        }),
      );
      expect(vi.mocked(rasterTileSource).mock.calls.map(([options]) => options.path)).toEqual([
        { source_id: 1 },
      ]);
      expect(
        vi.mocked(rasterTileSourceDomains).mock.calls.map(([options]) => options.path),
      ).toEqual([{ dataset_id: 'fluvial' }]);
    } finally {
      unsubscribe();
    }
  });

  it('fetches parameter domains only for accessible hazards', async () => {
    const store = createStore();
    const unsubscribe = store.sub(hazardDomainState, () => {});
    try {
      await vi.waitFor(() =>
        expect(store.get(hazardDomainState)).toEqual({
          fluvial: expect.objectContaining({ paramDomains: { returnPeriod: [100] } }),
          surface: null,
          coastal: null,
        }),
      );
      expect(
        vi.mocked(rasterTileSourceDomains).mock.calls.map(([options]) => options.path),
      ).toEqual([{ dataset_id: 'fluvial' }]);
    } finally {
      unsubscribe();
    }
  });
});

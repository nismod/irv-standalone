import { describe, expect, it, vi } from 'vitest';
import { mapRasterLayersList } from 'lib/api-client';
import { fetchHazardsMetadata } from './metadata';

vi.mock('lib/api-client', () => ({ mapRasterLayersList: vi.fn() }));

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

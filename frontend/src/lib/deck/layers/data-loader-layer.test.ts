import { afterEach, describe, expect, it, vi } from 'vitest';
import { DataLoader } from 'lib/data-loader/data-loader';
import { mapAttributesCreate } from 'lib/api-client/sdk.gen';
import { dataLoaderLayer } from './data-loader-layer';

vi.mock('lib/api-client/sdk.gen', () => ({ mapAttributesCreate: vi.fn() }));

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe('tile attribute loading', () => {
  it('sends top-level and property IDs to the API without missing or duplicate IDs', async () => {
    vi.stubGlobal('document', { cookie: 'csrftoken=test-token' });
    vi.mocked(mapAttributesCreate).mockResolvedValue({ data: { 123: 10, 456: 20 } } as never);
    const loader = new DataLoader('tile-test', 'roads', {
      fieldGroup: 'damages_expected',
      field: 'ead_mean',
      fieldDimensions: { hazard: 'all', parameters: { gwl: 2 }, protection_standard: 0 },
    });
    dataLoaderLayer(
      {
        tile: {
          content: [
            { id: 123, properties: {} },
            { properties: { id: '456' } },
            { id: 123, properties: {} },
            { properties: {} },
            { id: 0 },
            { id: -1 },
            { id: 1.5 },
            { id: Infinity },
          ],
        },
      },
      { dataLoader: loader },
    );
    await vi.waitFor(() =>
      expect(mapAttributesCreate).toHaveBeenCalledWith(
        expect.objectContaining({
          body: { ids: [123, 456] },
          path: { field_group: 'damages_expected' },
        }),
      ),
    );
    await vi.waitFor(() => expect(loader.getData(123)).toBe(10));
    expect(loader.getData(456)).toBe(20);
  });

  it('does not request attributes for empty tiles or features without usable IDs', () => {
    const loadData = vi.fn();
    for (const content of [[], [{ properties: {} }], [{ id: null }, { id: -2 }]]) {
      dataLoaderLayer({ tile: { content } }, { dataLoader: { loadData } as unknown as DataLoader });
    }
    expect(loadData).not.toHaveBeenCalled();
  });
});

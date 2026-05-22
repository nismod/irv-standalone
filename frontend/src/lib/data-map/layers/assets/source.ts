export const ASSETS_SOURCE = {
  getDataUrl({ assetId }) {
    return `/api/tiles/vector/data/${assetId}.json`;
  },
};

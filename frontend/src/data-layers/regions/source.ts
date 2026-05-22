export const REGIONS_SOURCE = {
  getDataUrl({ regionLevel }) {
    return `/api/tiles/vector/data/regions_${regionLevel}.json`;
  },
};

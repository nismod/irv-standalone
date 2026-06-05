function capitalise(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

export const RISK_SOURCE = {
  getDataUrl({ riskType, sector }, { scheme, range }) {
    return `/api/tiles/raster/hotspots/${sector}${capitalise(riskType)}/100/baseline/2010/None/{z}/{x}/{y}.png?colormap=${scheme}&stretch_range=[${range[0]},${range[1]}]`;
  },
};

import { atom } from 'jotai';

const HAZARDS_METADATA = {
  cyclone: {
    label: 'Tropical cyclone wind speed',
    dataUnit: 'm/s',
  },
  fluvial: {
    label: 'River Flooding',
    dataUnit: 'm',
  },
  surface: {
    label: 'Surface Flooding',
    dataUnit: 'm',
  },
  coastal: {
    label: 'Coastal Flooding',
    dataUnit: 'm',
  },
  storm: {
    label: 'Tropical cyclone return period',
    dataUnit: 'yrs',
  },
};

export const hazardsMetadataState = atom(HAZARDS_METADATA);

export const HAZARDS_MAP_ORDER = ['storm', 'cyclone', 'fluvial', 'surface', 'coastal'];
export const HAZARDS_UI_ORDER = ['fluvial', 'surface', 'coastal', 'cyclone', 'storm'];

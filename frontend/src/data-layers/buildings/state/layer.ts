import { atom } from 'jotai';

import { ViewLayer } from 'lib/data-map/view-layers';
import { sectionVisibilityState } from 'lib/state/sections';

import { buildingsViewLayer } from 'data-layers/buildings/buildings-view-layer';
import { networksMetadataState } from 'data-layers/networks/state/metadata';

import { buildingLayerIdsState, buildingSelectionState } from './data-selection';

export const buildingsLayerState = atom<ViewLayer[]>((get) =>
  get(sectionVisibilityState('buildings'))
    ? get(buildingLayerIdsState)
        .filter((id) => (get(buildingSelectionState)[id] ?? true) && get(networksMetadataState)[id])
        .map((id) => buildingsViewLayer(id, get(networksMetadataState)[id].deck))
    : [],
);

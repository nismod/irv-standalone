import { atom, type Getter } from 'jotai';

import { ViewLayer } from 'lib/data-map/view-layers';
import { truthyKeys } from 'lib/helpers';
import { dataParamConfigState, dataParamState } from 'lib/state/data-params';
import { sectionVisibilityState } from 'lib/state/sections';

import { hazardVisibilityState } from './hazard-visibility';
import { hazardsMetadataState, hazardSourceMetadataState } from './metadata';
import { hazardViewLayer } from '../hazard-view-layer';
import { type HazardParams } from './data-selection';

export const hazardsLayerState = atom<ViewLayer[]>((get) =>
  get(sectionVisibilityState('hazards'))
    ? truthyKeys(get(hazardVisibilityState)).map((hazard) =>
        hazardViewLayer(
          hazard,
          getHazardParams(get, hazard),
          get(hazardSourceMetadataState)[hazard],
          get(hazardsMetadataState)[hazard],
        ),
      )
    : [],
);

function getHazardParams(get: Getter, hazard: string): HazardParams {
  const groupConfig = get(dataParamConfigState)[hazard];
  if (!groupConfig) {
    return {};
  }

  return Object.fromEntries(
    Object.keys(groupConfig.paramDefaults)
      .map((param) => [param, get(dataParamState({ group: hazard, param }))] as const)
      .filter(([, value]) => value != null),
  ) as HazardParams;
}

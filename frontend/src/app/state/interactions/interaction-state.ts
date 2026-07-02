import { atom } from 'jotai';

import { interactionGroupsConfigState } from 'app/config/interaction-groups';
import { InteractionTarget, RasterTarget, VectorTarget } from 'lib/data-map/types';
import { hoverState, hasHover } from 'lib/state/interactions/interaction-state';
import { showPopulationState } from 'data-layers/regions/state/data-selection';

type InteractionLayer = InteractionTarget<VectorTarget> | InteractionTarget<RasterTarget>;
type IT = InteractionLayer | InteractionLayer[];

type LayerHoverState = {
  isHovered: boolean;
  hoverTarget: IT;
};

export const layerHoverStates = atom((get) => {
  const regionDataShown = get(showPopulationState);
  const interactionGroupEntries = [...get(interactionGroupsConfigState).entries()];
  const mapEntries = interactionGroupEntries.map(([groupId]) => {
    const hoverTarget = get(hoverState(groupId));
    const isHovered =
      groupId === 'regions' ? regionDataShown && hasHover(hoverTarget) : hasHover(hoverTarget);
    return [groupId, { isHovered, hoverTarget }] as [string, LayerHoverState];
  });
  return new Map<string, LayerHoverState>(mapEntries);
});

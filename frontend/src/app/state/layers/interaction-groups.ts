import { atom } from 'jotai';

import { interactionGroupsConfigState } from 'app/config/interaction-groups';
import { showPopulationState } from 'data-layers/regions/state/data-selection';

export const interactionGroupsState = atom((get) => {
  const regionDataShown = get(showPopulationState);
  const groups = new Map(get(interactionGroupsConfigState));
  if (groups.has('regions')) {
    const regionsGroup = groups.get('regions');
    groups.set('regions', { ...regionsGroup, usesAutoHighlight: regionDataShown });
  }

  return groups;
});

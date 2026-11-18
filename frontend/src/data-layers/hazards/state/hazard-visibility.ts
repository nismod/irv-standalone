import { atom } from 'jotai';

import { damageSourceState } from 'lib/state/damage-map';
import { showDamagesState } from 'app/state/damage-mapping/damage-map';

import { hazardsMapOrderState, hazardsMetadataState } from './metadata';
import { getHazardSelectionAggregate } from './data-selection';

export const hazardVisibilityState = atom((get) => {
  if (get(showDamagesState)) {
    const selectedDamageSource = get(damageSourceState);
    const metadata = get(hazardsMetadataState);
    const hazards = selectedDamageSource === 'all'
      ? get(hazardsMapOrderState)
      : [selectedDamageSource];
    return getHazardSelectionAggregate({ get }, hazards.filter((hazard) => metadata[hazard]?.has_access));
  } else {
    const hazardsMapOrder = get(hazardsMapOrderState);
    return getHazardSelectionAggregate({ get }, hazardsMapOrder);
  }
});

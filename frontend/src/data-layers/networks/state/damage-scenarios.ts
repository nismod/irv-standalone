import { atom } from 'jotai';
import { FieldSpec } from 'lib/data-map/view-layers';
import { mapViewConfig } from 'lib/state/map-view/map-view-config';
import {
  damageSourceState,
  damageTypeState,
  damageProtectionStandardState,
} from 'lib/state/damage-map';
import {
  modelParametersState,
  scenarioCatalogState,
  scenarioQueryKey,
} from 'lib/model-scenarios/state';
import {
  scenarioDimensions,
  scenariosForHazard,
  selectResult,
} from 'lib/model-scenarios/scenarios';
import { selectedNetworkLayerIdsState } from './data-selection';
import { hazardsMetadataState } from 'data-layers/hazards/state/metadata';

export const damageScenarioCatalogState = atom((get) =>
  get(
    scenarioCatalogState(
      scenarioQueryKey('damages_expected', { layer: get(selectedNetworkLayerIdsState) }),
    ),
  ),
);

export const damageScenarioState = atom((get) => {
  const catalog = get(damageScenarioCatalogState);
  const metadata = get(hazardsMetadataState);
  const available = catalog?.rows.filter((row) => metadata[row.hazard]?.has_access !== false) ?? [];
  const hazards = [...new Set(available.map((row) => row.hazard))];
  const requested = get(damageSourceState);
  const hazard = requested === 'all' || hazards.includes(requested) ? requested : 'all';
  const rows = scenariosForHazard(available, hazard);
  const result = selectResult(rows, get(modelParametersState('damages_expected')), {
    protection_standard: get(damageProtectionStandardState),
  });
  return { catalog, hazards, hazard, rows, result };
});

export const damagesFieldState = atom<FieldSpec | null>((get) => {
  const { result } = get(damageScenarioState);
  if (!result) return null;
  const damageType = get(damageTypeState);

  return {
    fieldGroup: 'damages_expected',
    fieldDimensions: scenarioDimensions(result),
    field: damageType === 'direct' ? 'ead_mean' : 'eael_mean',
    unit: `${get(mapViewConfig).app.currency}${damageType === 'direct' ? '' : '/day'}`,
  };
});

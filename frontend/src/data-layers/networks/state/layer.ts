import { atom } from 'jotai';
import { atomFamily } from 'jotai-family';
import uniq from 'lodash/uniq';
import fromPairs from 'lodash/fromPairs';
import mapValues from 'lodash/mapValues';

import { recalculateCheckboxStates } from 'lib/controls/checkbox-tree/CheckboxTree';
import { ViewLayer, StyleParams, ColorSpec, FieldSpec } from 'lib/data-map/view-layers';
import { StateEffect } from 'lib/recoil/state-effects/types';
import { mapViewConfig } from 'lib/state/map-view/map-view-config';
import { dataParamState } from 'lib/state/data-params';
import { sectionVisibilityState } from 'lib/state/sections';
import { protectedFeatureScenarioState } from 'lib/state/protected-features';

import { LayerSpec } from 'lib/asset-list/use-sorted-features';
import { damageMapStyleParamsState } from 'app/state/damage-mapping/damage-style-params';
import {
  modelParametersState,
  scenarioCatalogState,
  scenarioQueryKey,
} from 'lib/model-scenarios/state';
import { parameterKey, scenarioDimensions, selectResult } from 'lib/model-scenarios/scenarios';

import * as networkColorMaps from '../color-maps';
import {
  networksStyleState,
  selectedNetworkLayerIdsState,
  networkTreeCheckboxState,
  networkTreeConfigState,
} from './data-selection';
import { networksMetadataState } from './metadata';
import { type AdaptationOptionParams } from 'app/config/sidebar/NETWORK_DOMAINS';
import { getInfrastructureViewLayers } from '../view-layers';
import { getLeafNodeIdsForLayerIds, resolveAssetLayerIds } from '../layer-registry';

const infrastructureViewLayersState = atom((get) =>
  getInfrastructureViewLayers(get(networksMetadataState)),
);

export const networksLayerState = atom<ViewLayer[]>((get) => {
  if (!get(sectionVisibilityState('assets'))) {
    return [];
  }

  const infrastructureViewLayers = get(infrastructureViewLayersState);
  return get(selectedNetworkLayerIdsState).flatMap((layerId) => {
    const baseLayer = infrastructureViewLayers[layerId];
    if (!baseLayer) return [];
    return {
      ...baseLayer,
      styleParams: get(networkStyleParamsState(layerId)),
    };
  });
});

export const showAdaptationsState = atom<boolean>(
  (get) => get(networksStyleState) === 'adaptation',
);

export const showProtectorFeaturesState = atom<boolean>(
  (get) => get(networksStyleState) === 'protectedFeatures',
);

export const adaptationFieldState = atom<
  'avoided_ead_mean' | 'avoided_eael_mean' | 'adaptation_cost' | 'cost_benefit_ratio'
>('avoided_ead_mean');

export const adaptationCostBenefitRatioEaelDaysState = atom<number>(15);

export const adaptationDataParamsStateEffect: StateEffect<AdaptationOptionParams> = (
  { get, set },
  adaptationParams,
) => {
  const { sector, subsector, asset_type } = adaptationParams;
  const networkTreeConfig = get(networkTreeConfigState);

  const layers = uniq(resolveAssetLayerIds({ sector, subsector, asset_type }));
  const nodeIds = getLeafNodeIdsForLayerIds(networkTreeConfig, layers);

  const currentSelection = get(networkTreeCheckboxState);
  const updatedTreeState = {
    checked: {
      ...mapValues(currentSelection.checked, () => false),
      ...fromPairs(nodeIds.map((nodeId) => [nodeId, true])),
    },
    indeterminate: {},
  };
  const resolvedTreeState = recalculateCheckboxStates(updatedTreeState, networkTreeConfig);

  set(networkTreeCheckboxState, resolvedTreeState);

  // currently not auto-updating the expanded state of the tree since that can make the adaptations UI section move out of view
  // set(networkTreeExpandedState, truthyKeys(resolvedTreeState.indeterminate));
};

export const adaptationLayerSpecState = atom<LayerSpec>((get) => {
  const sector = get(dataParamState({ group: 'adaptation', param: 'sector' }));
  const subsector = get(dataParamState({ group: 'adaptation', param: 'subsector' }));
  const asset_type = get(dataParamState({ group: 'adaptation', param: 'asset_type' }));

  return {
    sector: sector !== null ? String(sector) : undefined,
    subsector: subsector !== null ? String(subsector) : undefined,
    asset_type: asset_type ? String(asset_type) : undefined,
  };
});

export const adaptationScenarioState = atom((get) => {
  const scope = get(adaptationLayerSpecState);
  const catalog = Object.values(scope).some((value) => value !== undefined)
    ? get(scenarioCatalogState(scenarioQueryKey('adaptation', scope)))
    : undefined;
  const hazards = [...new Set(catalog?.rows.map((row) => row.hazard) ?? [])];
  const requestedHazard = get(dataParamState({ group: 'adaptation', param: 'hazard' }));
  const hazard = hazards.find((value) => value === requestedHazard) ?? hazards[0];
  const rows = catalog?.rows.filter((row) => row.hazard === hazard) ?? [];
  const preferredName = get(dataParamState({ group: 'adaptation', param: 'adaptation_name' }));
  const preferredLevel = get(
    dataParamState({ group: 'adaptation', param: 'adaptation_protection_level' }),
  );
  const selected = selectResult(rows, get(modelParametersState('adaptation')));
  const parameterRows = selected
    ? rows.filter((row) => parameterKey(row.parameters) === parameterKey(selected.parameters))
    : [];
  const names = [...new Set(parameterRows.map((row) => row.adaptation_name))];
  const name = names.find((value) => value === preferredName) ?? names[0];
  const optionRows = parameterRows.filter((row) => row.adaptation_name === name);
  const result =
    optionRows.find((row) => row.adaptation_protection_level === preferredLevel) ?? optionRows[0];
  return { catalog, hazards, hazard, rows, names, optionRows, result };
});

export const adaptationFieldSpecState = atom<FieldSpec | null>((get) => {
  const field = get(adaptationFieldState);
  const protector = get(showProtectorFeaturesState) ? get(protectedFeatureScenarioState) : null;
  const result = protector
    ? selectResult(protector.catalog?.rows ?? [], protector.parameters)
    : get(adaptationScenarioState).result;
  if (!result) return null;

  let fieldParams: {
    eael_days?: number;
  } = {};
  if (field === 'cost_benefit_ratio') {
    fieldParams = {
      eael_days: get(adaptationCostBenefitRatioEaelDaysState),
    };
  }

  return {
    fieldGroup: 'adaptation',
    unit: field === 'cost_benefit_ratio'
      ? undefined
      : `${get(mapViewConfig).app.currency}${field === 'avoided_eael_mean' ? '/day' : ''}`,
    fieldDimensions: {
      ...scenarioDimensions(result),
      // Protector results are supplied by the protected-features query. Keep
      // their data-loader cache separate when another protector is selected.
      ...(protector ? { protector_id: protector.protectorId } : {}),
    },
    field,
    fieldParams,
  };
});

export const adaptationColorSpecState = atom<ColorSpec>((get) => {
  const field = get(adaptationFieldState);
  return networkColorMaps[field];
});

export const adaptationStyleParamsState = atom<StyleParams>((get) => {
  const fieldSpec = get(adaptationFieldSpecState);
  const colorSpec = get(adaptationColorSpecState);

  if (!fieldSpec) return {};

  return {
    colorMap: {
      fieldSpec,
      colorSpec,
    },
  };
});

export const networkStyleParamsState = atomFamily((layerId: string) =>
  atom<StyleParams>((get) => {
    switch (get(networksStyleState)) {
      case 'damages':
        return get(damageMapStyleParamsState(layerId));
      case 'adaptation':
        return get(adaptationStyleParamsState);
      case 'protectedFeatures':
        return get(adaptationStyleParamsState);
      default:
        return {};
    }
  }),
);

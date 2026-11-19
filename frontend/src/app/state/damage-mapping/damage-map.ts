import forEach from 'lodash/forEach';
import { atom } from 'jotai';

import { dataParamOptionsState, dataParamState } from 'lib/state/data-params';
import { damageScenarioState } from 'data-layers/networks/state/damage-scenarios';
import {
  matchRasterScenario,
  resolveRasterScenario,
  rasterReturnPeriodKey,
  rasterReturnPeriodOptions,
} from 'data-layers/hazards/raster-scenario';

import { hazardDomainState } from 'data-layers/hazards/state/domains';
import { hazardSelectionState } from 'data-layers/hazards/state/data-selection';
import { networksStyleState } from 'data-layers/networks/state/data-selection';

export const showDamagesState = atom((get) => get(networksStyleState) === 'damages');

export const damageScenarioSyncState = atom((get) => {
  const { result, selectedHazards } = get(damageScenarioState);
  return { scenario: result, hazards: selectedHazards, hazardDomains: get(hazardDomainState) };
});

export const damageRasterReturnPeriodsState = atom((get) => {
  const { result, selectedHazards } = get(damageScenarioState);
  if (!result) return [];
  const domains = get(hazardDomainState);
  return selectedHazards.flatMap((hazard) => {
    const config = domains?.[hazard];
    if (!config || !get(hazardSelectionState(hazard))) return [];
    const key = rasterReturnPeriodKey(config);
    if (!key) return [];
    const current = Object.fromEntries(
      Object.keys(config.paramDefaults).map((param) => [
        param,
        get(dataParamState({ group: hazard, param })),
      ]),
    );
    const value = current[key];
    const options = rasterReturnPeriodOptions(current, config);
    if (typeof value !== 'number' || !options.includes(value)) return [];
    return [{ hazard, value, options }];
  });
});

export const damageSourceStateEffect = (
  { get, set },
  { scenario, hazards = [], hazardDomains },
) => {
  const selections =
    scenario?.hazard === 'all'
      ? (scenario.hazard_parameters ??
        Object.fromEntries(hazards.map((hazard) => [hazard, scenario.parameters])))
      : scenario
        ? { [scenario.hazard]: scenario.parameters }
        : {};
  forEach(hazardDomains, (groupConfig, group) => {
    const parameters = selections[group];
    const matches = parameters != null && Boolean(groupConfig);
    if (matches && groupConfig) {
      const names = Object.keys(groupConfig.paramDefaults);
      const current = Object.fromEntries(
        names.map((param) => [
          param,
          get(dataParamState({ group, param })) ?? groupConfig.paramDefaults[param],
        ]),
      );
      const { linked, desired } = matchRasterScenario(parameters, groupConfig);
      if (!linked) {
        set(hazardSelectionState(group), false);
        return;
      }
      const resolved = resolveRasterScenario(current, desired, groupConfig);
      if (!resolved) {
        set(hazardSelectionState(group), false);
        return;
      }
      const [params, options] = resolved;
      names.forEach((param) => {
        set(dataParamState({ group, param }), params[param]);
        set(dataParamOptionsState({ group, param }), options[param]);
      });
    }
    set(hazardSelectionState(group), matches);
  });
};

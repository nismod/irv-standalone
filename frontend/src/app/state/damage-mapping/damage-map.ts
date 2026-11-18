import forEach from 'lodash/forEach';
import { atom } from 'jotai';

import { dataParamOptionsState, dataParamState } from 'lib/state/data-params';
import { damageScenarioState } from 'data-layers/networks/state/damage-scenarios';
import { matchRasterScenario, resolveRasterScenario } from 'data-layers/hazards/raster-scenario';

import { hazardDomainState } from 'data-layers/hazards/state/domains';
import { hazardSelectionState } from 'data-layers/hazards/state/data-selection';
import { networksStyleState } from 'data-layers/networks/state/data-selection';

export const showDamagesState = atom((get) => get(networksStyleState) === 'damages');

export const damageScenarioSyncState = atom((get) => ({
  scenario: get(damageScenarioState).result,
  hazardDomains: get(hazardDomainState),
}));

export const damageSourceStateEffect = ({ get, set }, { scenario, hazardDomains }) => {
  forEach(hazardDomains, (groupConfig, group) => {
    const matches = group === scenario?.hazard && Boolean(groupConfig);
    if (matches && groupConfig) {
      const names = Object.keys(groupConfig.paramDefaults);
      const current = Object.fromEntries(
        names.map((param) => [
          param,
          get(dataParamState({ group, param })) ?? groupConfig.paramDefaults[param],
        ]),
      );
      const { linked, desired } = matchRasterScenario(scenario.parameters, groupConfig);
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

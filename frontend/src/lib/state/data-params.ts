import forEach from 'lodash/forEach';
import { useCallback } from 'react';
import { atom } from 'jotai';
import { useAtomCallback } from 'jotai/utils';
import { atomFamily } from 'jotai-family';

import {
  DataParamGroupConfig,
  Param,
  ParamDomain,
  resolveParamDependencies,
} from 'lib/controls/data-params';
import { toDictionary } from 'lib/helpers';
import { Ops } from 'lib/recoil/state-effects/types';

export type DataParamParam = Readonly<{
  group: string;
  param: string;
}>;

export const dataParamConfigState = atom<Record<string, DataParamGroupConfig>>({});

const paramEqual = (a: DataParamParam, b: DataParamParam) =>
  a.group === b.group && a.param === b.param;

export const dataParamState = atomFamily(() => atom(null as Param | null), paramEqual);

export const dataParamOptionsState = atomFamily(() => atom([] as ParamDomain), paramEqual);

/**
 * A writeable selector that takes a config object, from an external source,
 * and creates new data params states for the sidebar controls.
 * Use this to initialise the sidebar from app config.
 */
export const syncExternalConfigState = atom(
  (get) => get(dataParamConfigState),
  (get, set, newConfig: Record<string, DataParamGroupConfig>) => {
    if (get(dataParamConfigState) === newConfig) return;
    set(dataParamConfigState, newConfig);

    Object.entries(newConfig).forEach(([group, groupConfig]) => {
      if (!groupConfig) {
        // group config is still loading.
        return;
      }
      const paramNames = Object.keys(groupConfig.paramDefaults);
      // Another panel may have set these values before config loading finished.
      // Keep valid selections when new groups or refreshed domains arrive.
      const currentValues = Object.fromEntries(
        paramNames.map((param) => {
          const current = get(dataParamState({ group, param }));
          return [
            param,
            groupConfig.paramDomains[param]?.includes(current)
              ? current
              : groupConfig.paramDefaults[param],
          ];
        }),
      );
      const [values, options] = resolveParamDependencies(
        currentValues,
        groupConfig,
      );

      paramNames.forEach((param) => {
        set(dataParamState({ group, param }), values[param]);
        set(dataParamOptionsState({ group, param }), options[param]);
      });
    });
  },
);

export function useUpdateDataParam(group: string, paramId: string) {
  return useAtomCallback(
    useCallback(
      (get, set, newValue: Param) => {
        const dataParamConfig = get(dataParamConfigState);
        const dataParamSize = Object.entries(dataParamConfig).length;
        if (dataParamSize === 0) {
          return;
        }
        const groupConfig = dataParamConfig[group];
        if (!groupConfig) {
          // group config is still loading.
          return;
        }
        const paramNames = Object.keys(groupConfig.paramDefaults);
        const groupParams = toDictionary(
          paramNames,
          (param: string) => param,
          (param: string) => get(dataParamState({ group, param })),
        );

        const [resolvedParams, resolvedOptions] = resolveParamDependencies(
          { ...groupParams, [paramId]: newValue },
          groupConfig,
        );

        forEach(resolvedParams, (resolvedParamValue, paramId) => {
          const atomParam = { group, param: paramId };
          set(dataParamState(atomParam), resolvedParamValue);
          set(dataParamOptionsState(atomParam), resolvedOptions[paramId]);
        });
      },
      [group, paramId],
    ),
  );
}

export function setParamToTopValue(
  { get, set }: Pick<Ops, 'get' | 'set'>,
  group: string,
  param: string,
) {
  const damageSourceParamDomain = get(dataParamOptionsState({ group, param }));
  if (!damageSourceParamDomain || damageSourceParamDomain.length === 0) {
    // No available options for this param; do not modify the current state.
    return;
  }
  const topParam = damageSourceParamDomain[damageSourceParamDomain.length - 1];
  set(dataParamState({ group, param }), topParam);
}

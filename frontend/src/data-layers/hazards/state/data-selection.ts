import { atom, type Atom } from 'jotai';
import { unwrap } from 'jotai/utils';
import { atomFamily } from 'jotai-family';
import fromPairs from 'lodash/fromPairs';

import { atomWithStoredBool } from 'lib/state/map-view/map-url';
import { DataParamGroupConfig } from 'lib/controls/data-params';

export interface HazardParams {
  returnPeriod: number;
  epoch: number;
  rcp: string;
  confidence: string | number;
  speed?: number;
}

async function fetchHazardDomains() {
  //TODO: move this into the Django app.
  const  module = await import('app/config/sidebar/HAZARD_DOMAINS');
  return module.HAZARD_DOMAINS;
}

export type HazardDomains = Record<string, DataParamGroupConfig<HazardParams>>;
export const hazardDomainState = unwrap(
  atom(fetchHazardDomains),
  prev => prev || null,
);

export const hazardSelectionState = atomFamily((id: string) => atomWithStoredBool(id, false));

interface TransactionGetterInterface {
  get<T>(a: Atom<T>): T;
}

export function getHazardSelectionAggregate(
  { get }: TransactionGetterInterface,
  hazards: string[],
) {
  return fromPairs(hazards.map((group) => [group, get(hazardSelectionState(group))]));
}

import { atom, type Atom } from 'jotai';
import { atomFamily } from 'jotai-family';
import fromPairs from 'lodash/fromPairs';

import { atomWithStoredBool } from 'lib/state/map-view/map-url';
import { HAZARD_DOMAINS } from 'app/config/sidebar/HAZARD_DOMAINS';

export type HazardDomains = typeof HAZARD_DOMAINS;
export const hazardDomainState = atom(HAZARD_DOMAINS);

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

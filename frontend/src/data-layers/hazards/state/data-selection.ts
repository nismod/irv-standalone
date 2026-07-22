import { type Atom } from 'jotai';
import { atomFamily } from 'jotai-family';
import fromPairs from 'lodash/fromPairs';

import { atomWithStoredBool } from 'lib/state/map-view/map-url';

export interface HazardParams {
  [key: string]: string | number | undefined;
  returnPeriod?: number;
  epoch?: number;
  rcp?: string;
  confidence?: string | number;
  speed?: number;
}

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

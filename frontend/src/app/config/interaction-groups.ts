import { atom } from 'jotai';
import { unwrap } from 'jotai/utils';

import type { InteractionGroupConfig } from 'lib/data-map/types';

type InteractionGroupsConfig = Record<string, InteractionGroupConfig>;

async function fetchInteractionGroupsConfig() {
  const module = await import('./interaction-groups.json');
  const config = module.default as InteractionGroupsConfig;
  return new Map<string, InteractionGroupConfig>(Object.entries(config));
}

const interactionGroupsQuery = atom(fetchInteractionGroupsConfig);

export const interactionGroupsConfigState = unwrap(
  interactionGroupsQuery,
  (prev) => prev ?? new Map<string, InteractionGroupConfig>(),
);

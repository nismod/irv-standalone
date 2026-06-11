import { atom, useAtom, useAtomValue } from 'jotai';
import { unwrap } from 'jotai/utils';

import { DataParamGroupConfig } from 'lib/controls/data-params';
import { syncExternalConfigState } from 'lib/state/data-params';
import { hazardDomainState } from 'data-layers/hazards/state/data-selection';

async function fetchNetworkDomains() {
  //TODO: move this into the Django app.
  const module = await import('app/config/sidebar/NETWORK_DOMAINS');
  return module.NETWORK_DOMAINS;
}

async function fetchRiskDomains() {
  //TODO: move this into the Django app.
  const module = await import('app/config/sidebar/RISK_DOMAINS');
  return module.RISK_DOMAINS;
}

const networkDomainState = unwrap(
  atom(fetchNetworkDomains),
  prev => prev || null,
);
const riskDomainState = unwrap(
  atom(fetchRiskDomains),
  prev => prev || null,
);

const dataParamConfigState =
  atom<Record<string, DataParamGroupConfig>>((get) => {
    const hazardDomains = get(hazardDomainState);
    const networkDomains = get(networkDomainState);
    const riskDomains = get(riskDomainState);

    if (!hazardDomains || !networkDomains || !riskDomains) {
      return {};
    }
    return {
      ...hazardDomains,
      ...networkDomains,
      risks: riskDomains,
    };
  });

export function useSyncConfigState() {
  const [config, setConfig] = useAtom(syncExternalConfigState);
  const dataParamConfig = useAtomValue(dataParamConfigState);
  if (config !== dataParamConfig) {
    setConfig(dataParamConfig);
  }
}

import { atom, useAtom, useAtomValue } from 'jotai';

import { NETWORK_DOMAINS } from 'data-layers/networks/domains';
import { RISK_DOMAINS } from 'data-layers/risks/domains';

import { DataParamGroupConfig } from 'lib/controls/data-params';
import { syncExternalConfigState } from 'lib/state/data-params';
import { hazardDomainState } from 'data-layers/hazards/state/data-selection';

const networkDomainState = atom(NETWORK_DOMAINS);
const riskDomainState = atom(RISK_DOMAINS);

const dataParamConfigState =
  atom<Record<string, DataParamGroupConfig>>((get) => {
    const hazardDomains = get(hazardDomainState);
    const networkDomains = get(networkDomainState);
    const riskDomains = get(riskDomainState);

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

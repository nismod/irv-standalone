import { atom, useAtom, useAtomValue } from 'jotai';
import { useEffect } from 'react';

import { DataParamGroupConfig } from 'lib/controls/data-params';
import { syncExternalConfigState } from 'lib/state/data-params';
import { hazardDomainState } from 'data-layers/hazards/state/domains';
import { networkDomainState } from 'data-layers/networks/state/domains';
import { riskDomainState } from 'data-layers/risks/state/domains';

const dataParamConfigState = atom<Record<string, DataParamGroupConfig>>((get) => {
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
  useEffect(() => {
    if (config !== dataParamConfig) setConfig(dataParamConfig);
  }, [config, dataParamConfig, setConfig]);
}

import { DataParamGroupConfig } from 'lib/controls/data-params';

export interface RiskParams {
  sector: string;
  returnPeriod: number;
  epoch: number;
  rcp: string;
  confidence: string | number;
}

export const sectorRiskTypes = {
  all: ['exposureValue', 'EAD', 'EADflood', 'EADcyclone'],
  power: ['exposureValue', 'EAD', 'demandAffected', 'populationAffected', 'lossGdp'],
  water: ['exposureValue', 'EAD'],
  transport: ['exposureValue', 'EAD', 'lossGdpIsolation', 'lossGdpRerouting'],
};

const defaultSectorDomains = {
  returnPeriod: [0],
  epoch: [2010],
  rcp: ['baseline'],
  confidence: ['None'],
};

export const RISK_DOMAINS: DataParamGroupConfig<RiskParams> = {
  /*
    Default parameter ranges for each risk type.
  */
  paramDomains: {
    sector: ['all', 'power', 'transport', 'water'],
    ...defaultSectorDomains,
  },
  /*
    Default parameter values for each risk type.
  */
  paramDefaults: {
    sector: 'all',
    returnPeriod: 0,
    epoch: 2010,
    rcp: 'baseline',
    confidence: 'None',
  },
  /*
    Callback functions to define custom parameter ranges based on selected hazard etc.
  */
  paramDependencies: {
    rcp: () => defaultSectorDomains.rcp,
    epoch: () => defaultSectorDomains.epoch,
    returnPeriod: () => defaultSectorDomains.returnPeriod,
    confidence: () => defaultSectorDomains.confidence,
  },
};

import {
  DataParamGroupConfig,
  inferDependenciesFromData,
  inferDomainsFromData,
} from 'lib/controls/data-params';
import { assetLayerDefinitions } from 'data-layers/networks/layer-registry';

// Asset filters remain project configuration. Model scenarios and adaptation
// options come from the results catalogue, independently of these filters.
export interface AdaptationOptionParams {
  sector: string;
  subsector: string;
  asset_type: string;
}

const assetFilters = assetLayerDefinitions.map(({ sector, subsector, asset_type }) => ({
  sector,
  subsector,
  asset_type,
}));

export const NETWORK_DOMAINS: Record<string, DataParamGroupConfig<AdaptationOptionParams>> = {
  adaptation: {
    paramDefaults: { sector: 'power', subsector: 'transmission', asset_type: 'pole' },
    paramDomains: inferDomainsFromData(assetFilters),
    paramDependencies: inferDependenciesFromData(assetFilters, {
      sector: [],
      subsector: ['sector'],
      asset_type: ['sector', 'subsector'],
    }),
  },
};

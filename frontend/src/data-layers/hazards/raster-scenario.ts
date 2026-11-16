import { DataParamGroupConfig, Param, resolveParamDependencies } from 'lib/controls/data-params';
import { ModelParameters, valueKey } from 'lib/model-scenarios/scenarios';

const parameterName = (name: string) => {
  const lower = name.toLowerCase();
  return lower === 'rp' ? 'returnperiod' : lower;
};

// Link only parameters whose identity and values are represented by the raster.
// Model-only dimensions (e.g. an ensemble member) cannot silently be discarded.
export function matchRasterScenario(parameters: ModelParameters, config: DataParamGroupConfig) {
  const names = Object.keys(config.paramDefaults);
  const desired: Record<string, Param> = {};
  let complete = Object.keys(parameters).length > 0;
  for (const [name, value] of Object.entries(parameters)) {
    const target = names.find((candidate) => parameterName(candidate) === parameterName(name));
    const domain = config.paramDomains[target] ?? [];
    const option =
      domain.find((candidate) => valueKey(candidate) === valueKey(value)) ??
      domain.find(
        (candidate) =>
          ['string', 'number'].includes(typeof value) && String(candidate) === String(value),
      );
    if (!target || option === undefined || (target in desired && desired[target] !== option)) {
      complete = false;
    } else {
      desired[target] = option;
    }
  }
  const [resolved] = resolveParamDependencies({ ...config.paramDefaults, ...desired }, config);
  complete &&= Object.entries(desired).every(
    ([name, value]) => valueKey(resolved[name]) === valueKey(value),
  );
  return { linked: complete, desired: complete ? desired : {} };
}

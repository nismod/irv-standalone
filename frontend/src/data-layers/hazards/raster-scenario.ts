import { DataParamGroupConfig, Param, resolveParamDependencies } from 'lib/controls/data-params';
import { ModelParameters, valueKey } from 'lib/model-scenarios/scenarios';

export type RasterParamGroupConfig<PGT extends object = object> =
  DataParamGroupConfig<PGT> & { paramCombinations?: Record<string, Param>[] };

const parameterName = (name: string) => {
  const lower = name.toLowerCase();
  return lower === 'rp' ? 'returnperiod' : lower;
};

// Link only parameters whose identity and values are represented by the raster.
// Model-only dimensions (e.g. an ensemble member) cannot silently be discarded.
export function matchRasterScenario(parameters: ModelParameters, config: RasterParamGroupConfig) {
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
  if (config.paramCombinations) {
    complete &&= matchingCombinations(desired, config).length > 0;
  } else {
    const [resolved] = resolveParamDependencies({ ...config.paramDefaults, ...desired }, config);
    complete &&= Object.entries(desired).every(
      ([name, value]) => valueKey(resolved[name]) === valueKey(value),
    );
  }
  return { linked: complete, desired: complete ? desired : {} };
}

function matchingCombinations(desired: Record<string, Param>, config: RasterParamGroupConfig) {
  return config.paramCombinations.filter((row) =>
    Object.entries(desired).every(([name, value]) => valueKey(row[name]) === valueKey(value)),
  );
}

// Choose a whole raster row, including raster-only dimensions such as RP and
// confidence. A globally available RP need not exist for the selected climate.
export function resolveRasterScenario(
  current: Record<string, Param>,
  desired: Record<string, Param>,
  config: RasterParamGroupConfig,
) {
  if (!config.paramCombinations) {
    const returnPeriods = config.paramDomains['returnPeriod'] as Param[] | undefined;
    const preferred = returnPeriods?.length
      ? { ...current, returnPeriod: returnPeriods[returnPeriods.length - 1] }
      : current;
    return resolveParamDependencies({ ...preferred, ...desired }, config);
  }

  let candidates = matchingCombinations(desired, config);
  const returnPeriod = Object.keys(config.paramDefaults).find(
    (name) => parameterName(name) === 'returnperiod',
  );
  if (returnPeriod && candidates.length) {
    const maximum = Math.max(...candidates.map((row) => Number(row[returnPeriod])));
    candidates = candidates.filter((row) => Number(row[returnPeriod]) === maximum);
  }
  const score = (row: Record<string, Param>) =>
    Object.entries(current).filter(([name, value]) => valueKey(row[name]) === valueKey(value)).length;
  const selected = candidates.reduce<Record<string, Param> | undefined>(
    (best, row) => (!best || score(row) > score(best) ? row : best),
    undefined,
  );
  if (!selected) return null;
  const [, options] = resolveParamDependencies(selected, config);
  return [{ ...selected }, options] as const;
}

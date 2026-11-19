import stringify from 'json-stable-stringify';

export type ModelParameters = Record<string, unknown>;
export type ModelType = 'damages_expected' | 'adaptation';

export interface ModelScenario {
  hazard: string;
  parameters: ModelParameters;
  protection_standard?: number;
  adaptation_name?: string;
  adaptation_protection_level?: number;
  hazard_parameters?: Record<string, ModelParameters>;
}

export const parameterKey = (parameters: ModelParameters) => stringify(parameters);
export const valueKey = (value: unknown) => stringify({ value });

export function parameterNames(rows: ModelScenario[]) {
  return [...new Set(rows.flatMap((row) => Object.keys(row.parameters)))].sort();
}

export function parameterLabel(name: string) {
  return { rcp: 'RCP', epoch: 'Year', gwl: 'GWL', slr: 'SLR' }[name] ?? name.replaceAll('_', ' ');
}

export function valueLabel(value: unknown) {
  return typeof value === 'string' ? value : (JSON.stringify(value) ?? 'Not specified');
}

export function scenariosForHazard(rows: ModelScenario[], hazard: string): ModelScenario[] {
  if (hazard !== 'all') return rows.filter((row) => row.hazard === hazard);
  const hazards = new Map<string, ModelScenario[]>();
  for (const row of rows) {
    hazards.set(row.hazard, [...(hazards.get(row.hazard) ?? []), row]);
  }
  let combinations: ModelScenario[] | null = null;
  for (const [name, candidates] of hazards) {
    if (combinations === null) {
      combinations = candidates.map((row) => ({
        ...row, hazard: 'all', hazard_parameters: { [name]: row.parameters },
      }));
      continue;
    }
    const joined = new Map<string, ModelScenario>();
    for (const combination of combinations) {
      for (const row of candidates) {
        if (valueKey(combination.protection_standard) !== valueKey(row.protection_standard)) continue;
        if (Object.entries(row.parameters).some(([key, value]) =>
          Object.hasOwn(combination.parameters, key) &&
          valueKey(combination.parameters[key]) !== valueKey(value),
        )) continue;
        const next = {
          ...combination,
          parameters: { ...combination.parameters, ...row.parameters },
          hazard_parameters: { ...combination.hazard_parameters, [name]: row.parameters },
        };
        joined.set(stringify([next.parameters, next.protection_standard, next.hazard_parameters]), next);
      }
    }
    combinations = [...joined.values()];
  }
  return (combinations ?? []).map((row) => {
    // Identical schemas retain the existing all-hazard API request format.
    if (Object.values(row.hazard_parameters).every((parameters) =>
      parameterKey(parameters) === parameterKey(row.parameters),
    )) {
      const shared = { ...row };
      delete shared.hazard_parameters;
      return shared;
    }
    return row;
  });
}

export function scenariosForHazards(
  rows: ModelScenario[],
  selection: 'all' | string[],
): ModelScenario[] {
  if (selection === 'all') return scenariosForHazard(rows, 'all');
  const hazards = [...new Set(selection)];
  if (!hazards.length || hazards.some((hazard) => !rows.some((row) => row.hazard === hazard)))
    return [];
  if (hazards.length === 1) return scenariosForHazard(rows, hazards[0]);
  return scenariosForHazard(
    rows.filter((row) => hazards.includes(row.hazard)),
    'all',
  ).map((row) => ({
    ...row,
    // Explicitly scope totals even when the selected hazards share a schema.
    hazard_parameters:
      row.hazard_parameters ??
      Object.fromEntries(hazards.map((hazard) => [hazard, row.parameters])),
  }));
}

// Preserve as much of the selection as possible when the scope changes, while
// always returning a complete scenario that exists in the new catalogue.
export function selectParameters(rows: ModelScenario[], preferred: ModelParameters | null) {
  const exact = rows.find((row) => parameterKey(row.parameters) === parameterKey(preferred));
  if (exact) return exact.parameters;
  const score = (row: ModelScenario) =>
    Object.entries(preferred ?? {}).filter(
      ([name, value]) =>
        name in row.parameters && valueKey(row.parameters[name]) === valueKey(value),
    ).length;
  return (
    rows.reduce<ModelScenario | undefined>(
      (best, row) => (!best || score(row) > score(best) ? row : best),
      undefined,
    )?.parameters ?? null
  );
}

export function parameterOptions(rows: ModelScenario[], parameters: ModelParameters, name: string) {
  const names = parameterNames(rows);
  const preceding = names.slice(0, names.indexOf(name));
  const candidates = rows.filter((row) =>
    preceding.every((param) => valueKey(row.parameters[param]) === valueKey(parameters[param])),
  );
  const options = new Map<string, unknown>();
  for (const row of candidates) options.set(valueKey(row.parameters[name]), row.parameters[name]);
  return [...options].map(([key, value]) => ({ key, value, label: valueLabel(value) }));
}

export function changeParameter(
  rows: ModelScenario[],
  parameters: ModelParameters,
  name: string,
  key: string,
) {
  const names = parameterNames(rows);
  const preceding = names.slice(0, names.indexOf(name));
  const candidates = rows.filter(
    (row) =>
      valueKey(row.parameters[name]) === key &&
      preceding.every((param) => valueKey(row.parameters[param]) === valueKey(parameters[param])),
  );
  return selectParameters(candidates, parameters);
}

export function scenarioDimensions(row: ModelScenario) {
  const { parameters, ...dimensions } = row;
  return { ...dimensions, parameters };
}

export function selectResult(
  rows: ModelScenario[],
  parameters: ModelParameters | null,
  preferred: Partial<ModelScenario> = {},
) {
  const selected = selectParameters(rows, parameters);
  if (selected === null) return null;
  let candidates = rows.filter((row) => parameterKey(row.parameters) === parameterKey(selected));
  // An option change can invalidate the old protection level. Keep the chosen
  // option first, then retain its level only if that combination exists.
  for (const name of ['adaptation_name', 'adaptation_protection_level', 'protection_standard']) {
    if (!(name in preferred)) continue;
    const matching = candidates.filter((row) => valueKey(row[name]) === valueKey(preferred[name]));
    if (matching.length) candidates = matching;
  }
  return candidates[0];
}

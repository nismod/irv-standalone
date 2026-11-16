import { parameterLabel } from './parameter-labels';

type ParameterRow = { parameters: Record<string, unknown> };

export function parameterNames(rows: ParameterRow[]) {
  return [...new Set(rows.flatMap((row) => Object.keys(row.parameters)))].sort();
}

// Vega field paths need literal dots and brackets in parameter names escaped.
export function parameterField(name: string) {
  return `parameters.${name.replace(/[.[\]\\]/g, '\\$&')}`;
}

export function expectedDamageDimensions(rows: ParameterRow[]) {
  const names = parameterNames(rows);
  const x = names.find((name) => name === 'epoch')
    ?? names.find((name) => name === 'gwl')
    ?? names.find((name) => rows.some((row) => typeof row.parameters[name] === 'number'))
    ?? names[0];
  const remaining = names.filter((name) => name !== x);
  const series = remaining.find((name) => name === 'rcp') ?? remaining[0];
  return { x, series, selectors: remaining.filter((name) => name !== series) };
}

export function returnPeriodDimensions(rows: ParameterRow[]) {
  const names = parameterNames(rows);
  const series = names.find((name) => name === 'rcp')
    ?? names.find((name) => name === 'gwl')
    ?? names.find((name) => name !== 'epoch');
  return { series, selectors: names.filter((name) => name !== series) };
}

export function parameterSelectionKey(row: ParameterRow, names: string[]) {
  return JSON.stringify(names.map((name) => row.parameters[name]));
}

export function parameterOptions(rows: ParameterRow[], names: string[]) {
  const options = new Map<string, string>();
  for (const row of rows) {
    const key = parameterSelectionKey(row, names);
    const label = names.map((name) => {
      const value = row.parameters[name];
      const text = value != null && typeof value === 'object' ? JSON.stringify(value) : String(value ?? '');
      return names.length === 1 ? text : `${parameterLabel(name)}: ${text}`;
    }).join(', ');
    options.set(key, label);
  }
  return [...options].map(([key, label]) => ({ key, label }))
    .sort((a, b) => a.label.localeCompare(b.label, undefined, { numeric: true }));
}

export function parameterTitle(names: string[]) {
  return names.map(parameterLabel).join(' / ');
}

const parameterLabels: Record<string, string> = {
  gwl: 'GWL',
  rcp: 'RCP',
  slr: 'SLR',
  rp: 'Return period',
  epoch: 'Year',
};

export function parameterLabel(field: string) {
  const name = field.startsWith('parameters.')
    ? field.slice('parameters.'.length).replace(/\\(.)/g, '$1')
    : field;
  return parameterLabels[name.toLowerCase()] ?? name.replaceAll('_', ' ');
}

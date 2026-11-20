import { Stack, Typography } from '@mui/material';
import { ModelParameterControl, type NumericControl } from './ModelParameterControl';
import {
  changeParameter,
  ModelParameters,
  ModelScenario,
  parameterLabel,
  parameterNames,
  parameterOptions,
  valueKey,
} from './scenarios';

export function ModelParameterControls({
  rows,
  parameters,
  onChange,
  error,
  numericControl = 'select',
  emptyMessage = 'No model scenarios available.',
}: {
  rows?: ModelScenario[];
  parameters: ModelParameters | null;
  onChange: (value: ModelParameters) => void;
  error?: string;
  numericControl?: NumericControl;
  emptyMessage?: string;
}) {
  if (error) return <Typography role="alert">{error}</Typography>;
  if (!rows) return <Typography role="status">Loading model scenarios…</Typography>;
  if (parameters === null) return <Typography role="status">{emptyMessage}</Typography>;
  return (
    <Stack spacing={1}>
      {parameterNames(rows).map((name) => (
        <ModelParameterControl
          key={name}
          title={parameterLabel(name)}
          value={parameters[name]}
          options={parameterOptions(rows, parameters, name).map((option) => option.value)}
          numericControl={numericControl}
          onChange={(value) => {
            const next = changeParameter(rows, parameters, name, valueKey(value));
            if (next !== null) onChange(next);
          }}
        />
      ))}
    </Stack>
  );
}

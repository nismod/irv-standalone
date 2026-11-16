import { Stack, Typography } from '@mui/material';
import { ParamDropdown } from 'lib/controls/ParamDropdown';
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
  emptyMessage = 'No model scenarios available.',
}: {
  rows?: ModelScenario[];
  parameters: ModelParameters | null;
  onChange: (value: ModelParameters) => void;
  error?: string;
  emptyMessage?: string;
}) {
  if (error) return <Typography role="alert">{error}</Typography>;
  if (!rows) return <Typography role="status">Loading model scenarios…</Typography>;
  if (parameters === null) return <Typography role="status">{emptyMessage}</Typography>;
  return (
    <Stack spacing={1}>
      {parameterNames(rows).map((name) => (
        <ParamDropdown
          key={name}
          title={parameterLabel(name)}
          value={valueKey(parameters[name])}
          options={parameterOptions(rows, parameters, name).map((option) => ({
            value: option.key,
            label: option.label,
          }))}
          onChange={(key) => {
            const next = changeParameter(rows, parameters, name, key);
            if (next !== null) onChange(next);
          }}
        />
      ))}
    </Stack>
  );
}

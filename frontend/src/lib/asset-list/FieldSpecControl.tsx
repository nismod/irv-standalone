import { Stack } from '@mui/material';
import { ParamDropdown } from 'lib/controls/ParamDropdown';
import { ModelParameterControls } from 'lib/model-scenarios/ModelParameterControls';
import { ModelParameterControl, type NumericControl } from 'lib/model-scenarios/ModelParameterControl';
import {
  ModelParameters,
  ModelScenario,
  ModelType,
  parameterKey,
} from 'lib/model-scenarios/scenarios';

export function FieldSpecControl({
  model,
  onModelChange,
  hazards,
  hazard,
  onHazardChange,
  rows,
  result,
  onParametersChange,
  onDimensionChange,
  error,
  numericControl = 'select',
}: {
  model: ModelType;
  onModelChange: (model: ModelType) => void;
  hazards: string[];
  hazard: string;
  onHazardChange: (hazard: string) => void;
  rows?: ModelScenario[];
  result: ModelScenario | null;
  onParametersChange: (parameters: ModelParameters) => void;
  onDimensionChange: (dimensions: Partial<ModelScenario>) => void;
  error?: string;
  numericControl?: NumericControl;
}) {
  const parameterRows =
    rows?.filter(
      (row) => result && parameterKey(row.parameters) === parameterKey(result.parameters),
    ) ?? [];
  return (
    <Stack spacing={2}>
      <ParamDropdown
        title="Variable Group"
        value={model}
        onChange={onModelChange}
        options={[
          { value: 'damages_expected', label: 'Expected Damages' },
          { value: 'adaptation', label: 'Adaptation Options' },
        ]}
      />
      <ParamDropdown
        title="Hazard"
        value={hazard ?? ''}
        onChange={onHazardChange}
        options={hazards.map((value) => ({
          value,
          label: value === 'all' ? 'All Hazards' : value,
        }))}
      />
      <ModelParameterControls
        rows={rows}
        parameters={result?.parameters ?? null}
        onChange={onParametersChange}
        numericControl={numericControl}
        error={error}
        emptyMessage={
          hazard === 'all' && rows?.length === 0
            ? 'No compatible combination is available across all hazards. Choose a hazard.'
            : undefined
        }
      />
      {result && model === 'damages_expected' && (
        <ModelParameterControl
          title="Protection standard"
          value={result.protection_standard}
          options={[...new Set(parameterRows.map((row) => row.protection_standard))]}
          onChange={(value) => onDimensionChange({ protection_standard: value })}
          numericControl={numericControl}
        />
      )}
      {result && model === 'adaptation' && (
        <>
          <ParamDropdown
            title="Adaptation type"
            value={result.adaptation_name}
            options={[...new Set(parameterRows.map((row) => row.adaptation_name))]}
            onChange={(value) => onDimensionChange({ adaptation_name: value })}
          />
          <ParamDropdown
            title="Protection level"
            value={result.adaptation_protection_level}
            options={parameterRows
              .filter((row) => row.adaptation_name === result.adaptation_name)
              .map((row) => row.adaptation_protection_level)}
            onChange={(value) => onDimensionChange({ adaptation_protection_level: value })}
          />
        </>
      )}
    </Stack>
  );
}

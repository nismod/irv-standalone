import { Box, FormControl, FormLabel } from '@mui/material';
import { useId } from 'react';
import { CustomNumberSlider } from 'lib/controls/CustomSlider';
import { ParamDropdown } from 'lib/controls/ParamDropdown';
import { valueKey, valueLabel } from './scenarios';

export type NumericControl = 'select' | 'slider';

export function ModelParameterControl<Value>({
  title,
  value,
  options,
  onChange,
  numericControl = 'select',
  disabled = false,
}: {
  title: string;
  value: Value;
  options: Value[];
  onChange: (value: Value) => void;
  numericControl?: NumericControl;
  disabled?: boolean;
}) {
  const labelId = useId();
  const isNumeric = (option: unknown): option is number =>
    typeof option === 'number' && Number.isFinite(option);
  if (
    numericControl === 'slider' &&
    isNumeric(value) &&
    options.length &&
    options.every(isNumeric) &&
    options.includes(value)
  ) {
    const marks = [...new Set(options.map(Number))].sort((a, b) => a - b);
    return (
      <FormControl fullWidth disabled={disabled || marks.length < 2}>
        <FormLabel id={labelId}>{title}</FormLabel>
        <Box px={1}>
          <CustomNumberSlider
            aria-labelledby={labelId}
            marks={marks}
            value={value}
            onChange={(next) => {
              const option = options.find((option) => option === next);
              if (option !== undefined) onChange(option);
            }}
            disabled={disabled || marks.length < 2}
            valueLabelDisplay="auto"
          />
        </Box>
      </FormControl>
    );
  }
  return (
    <ParamDropdown
      title={title}
      value={valueKey(value)}
      options={options.map((option) => ({ value: valueKey(option), label: valueLabel(option) }))}
      onChange={(key) => onChange(options.find((option) => valueKey(option) === key))}
      disabled={disabled}
    />
  );
}

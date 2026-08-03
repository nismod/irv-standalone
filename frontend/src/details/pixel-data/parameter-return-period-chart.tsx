import { KeyboardEvent as ReactKeyboardEvent, useMemo } from 'react';
import { ToggleButton, ToggleButtonGroup } from '@mui/material';

import { unique } from 'lib/helpers';
import { useSelect } from 'lib/hooks/use-select';
import type { PixelDataRecord } from 'lib/state/pixel-driller';
import { ReturnPeriodDamageChart } from 'details/features/damages/ReturnPeriodDamageChart';

type EpochReturnPeriodChartProps = {
  records: PixelDataRecord[];
  fieldTitle: string;
  width?: number;
  height?: number;
};

export const PixelParameterReturnPeriodChart = ({
  records,
  fieldTitle,
  width = 280,
  height = 170,
}: EpochReturnPeriodChartProps) => {
  const parameterFields = useMemo(() => {
    const excluded = new Set(['rp', 'value', 'variable', 'unit', 'hazard', 'key', 'path']);
    return Object.keys(records[0] ?? {}).filter((field) => !excluded.has(field));
  }, [records]);
  const selectorField =
    parameterFields.length > 1
      ? parameterFields.find(
          (field) =>
            field === 'epoch' && unique(records.map((record) => record[field])).length > 1,
        ) ??
        parameterFields.find(
          (field) => unique(records.map((record) => record[field])).length > 1,
        )
      : undefined;
  const selectorValues = useMemo(
    () => (selectorField ? unique(records.map((record) => record[selectorField])).sort() : []),
    [records, selectorField],
  );
  const [selectedValue, setSelectedValue] = useSelect(selectorValues);

  const handleEpochKeyDown = (event: ReactKeyboardEvent<HTMLDivElement>) => {
    if (!selectorValues.length || selectedValue == null) {
      return;
    }

    if (event.key === 'Home') {
      event.preventDefault();
      setSelectedValue(selectorValues[0]);
      return;
    }

    if (event.key === 'End') {
      event.preventDefault();
      setSelectedValue(selectorValues[selectorValues.length - 1]);
      return;
    }

    let offset = 0;
    if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
      offset = 1;
    } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
      offset = -1;
    } else {
      return;
    }

    event.preventDefault();
    const currentIndex = selectorValues.indexOf(selectedValue);
    const nextIndex = (currentIndex + offset + selectorValues.length) % selectorValues.length;
    setSelectedValue(selectorValues[nextIndex]);
  };

  const chartData = useMemo(() => {
    const table = records
      .map((record) => ({
        ...record,
        rp: Number(record.rp),
        value: Number(record.value),
      }))
      .filter((record) => Number.isFinite(record.rp) && Number.isFinite(record.value))
      .filter((record) => !selectorField || record[selectorField] === selectedValue)
      .flatMap((record) => ({
        ...record,
        probability: 1 / record.rp,
      }));
    return { table };
  }, [records, selectedValue, selectorField]);

  if (!records.length) {
    return null;
  }

  return (
    <>
      {selectorValues.length ? (
        <ToggleButtonGroup
          exclusive
          size="small"
          value={selectedValue ?? null}
          onKeyDown={handleEpochKeyDown}
          onChange={(_, value) => {
            if (value !== null) {
              setSelectedValue(value);
            }
          }}
          sx={{ my: 2, display: 'flex', flexWrap: 'wrap' }}
        >
          {selectorValues.map((value) => (
            <ToggleButton key={String(value)} value={value} disabled={selectorValues.length === 1}>
              {String(value)}
            </ToggleButton>
          ))}
        </ToggleButtonGroup>
      ) : null}
      <ReturnPeriodDamageChart
        data={chartData}
        field_key="value"
        field_title={fieldTitle}
        actions={false}
        width={width}
        height={height}
        renderer="svg"
        tooltipFields={parameterFields}
        seriesField={parameterFields.find((field) => field !== selectorField) ?? parameterFields[0] ?? 'rp'}
      />
    </>
  );
};

export const EpochReturnPeriodChart = PixelParameterReturnPeriodChart;

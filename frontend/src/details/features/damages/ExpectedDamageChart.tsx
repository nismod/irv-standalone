import { useMemo, useRef, useEffect } from 'react';
import { useVegaEmbed } from 'react-vega';
import { VisualizationSpec } from 'vega-embed';
import { Box } from '@mui/material';

import { parameterLabel } from './parameter-labels';
import { seriesEncoding } from './chartStyles';

export const makeExpectedDamageSpec = (
  field: string,
  field_title: string,
  width: number,
  height: number,
  xField: string,
  xTitle = parameterLabel(xField),
  tooltipFields = [xField],
  seriesField?: string,
  seriesTitle = seriesField ? parameterLabel(seriesField) : null,
  field_min?: string,
  field_max?: string,
) => ({
  $schema: 'https://vega.github.io/schema/vega-lite/v6.json',
  width,
  height,
  data: {
    name: 'table',
  },
  layer: [
    ...(field_min && field_max ? [{
      transform: [{ filter: { and: [
        { field: field_min, valid: true },
        { field: field_max, valid: true },
      ] } }],
      mark: { type: 'errorbar', ticks: true, opacity: 0.5 },
      encoding: {
        y: { field: field_min, type: 'quantitative', title: field_title },
        y2: { field: field_max },
      },
    }] : []),
    {
      mark: { type: 'line', point: { filled: true }, tooltip: true },
      encoding: seriesEncoding(seriesField, seriesTitle),
    },
  ],
  encoding: {
    ...(seriesField ? { color: seriesEncoding(seriesField, seriesTitle).color } : {}),
    x: {
      field: xField,
      type: 'ordinal',
      title: xTitle,
      axis: {
        labelAngle: 0,
        gridDash: [2, 2],
        domainColor: '#ccc',
        tickColor: '#ccc',
      },
    },
    y: {
      field: field,
      type: 'quantitative',
      title: field_title,
      axis: {
        gridDash: [2, 2],
        domainColor: '#ccc',
        tickColor: '#ccc',
      },
    },
    // the tooltip encoding needs to replicate the field definitions in order to customise their ordering
    tooltip: [
      { field: field, type: 'quantitative', format: ',.3r', title: field_title },
      ...(field_min ? [{ field: field_min, type: 'quantitative', format: ',.3r', title: `${field_title} (amin)` }] : []),
      ...(field_max ? [{ field: field_max, type: 'quantitative', format: ',.3r', title: `${field_title} (amax)` }] : []),
      ...tooltipFields.map((field) => ({
        field,
        title: field === xField ? xTitle : field === seriesField ? seriesTitle : parameterLabel(field),
      })),
    ],
  },
});

export const ExpectedDamageChart = ({
  data,
  field,
  field_min = undefined,
  field_max = undefined,
  field_title,
  width,
  height,
  xField,
  xTitle = parameterLabel(xField),
  seriesField = undefined,
  seriesTitle = seriesField ? parameterLabel(seriesField) : null,
  tooltipFields = seriesField ? [xField, seriesField] : [xField],
  ...props
}) => {
  const ref = useRef<HTMLDivElement>(null);
  const spec = useMemo(
    () =>
      makeExpectedDamageSpec(
        field,
        field_title,
        width,
        height,
        xField,
        xTitle,
        tooltipFields,
        seriesField,
        seriesTitle,
        field_min,
        field_max,
      ),
    [field, field_min, field_max, field_title, width, height, xField, xTitle, tooltipFields, seriesField, seriesTitle],
  ) as VisualizationSpec;
  const embed = useVegaEmbed({
    ref,
    spec,
    options: {
      mode: 'vega-lite',
      padding: {
        left: 10,
        right: 10,
        top: 10,
        bottom: 50,
      },
      ...props,
    },
  });

  useEffect(() => {
    embed?.view.data('table', data.table).runAsync();
  }, [embed, data]);

  return <Box ref={ref} />;
};

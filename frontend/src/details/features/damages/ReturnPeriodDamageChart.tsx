import { useMemo, useRef, useEffect } from 'react';
import { useVegaEmbed } from 'react-vega';
import { VisualizationSpec } from 'vega-embed';
import { Box } from '@mui/material';

import { unique } from 'lib/helpers';
import { chartStyles } from './chartStyles';

const makeSpec = (
  rpValues: number[],
  field_key: string,
  field_title: string,
  width: number,
  height: number,
  tooltipFields: string[],
  seriesField: string,
) => ({
  $schema: 'https://vega.github.io/schema/vega-lite/v6.json',
  width,
  height,
  data: {
    name: 'table',
  },
  mark: {
    type: 'line',
    point: {
      filled: true,
    },
    tooltip: true,
  },
  encoding: {
    ...(seriesField === 'rcp'
      ? chartStyles
      : {
          color: {
            field: seriesField,
            type: 'ordinal',
            title: seriesField,
            legend: { orient: 'bottom', direction: 'horizontal' },
          },
          shape: { field: seriesField, type: 'ordinal', legend: null },
        }),
    x: {
      field: 'probability',
      type: 'quantitative',
      title: 'Annual Exceedance Probability',
      axis: {
        gridDash: [2, 2],
        domainColor: '#ccc',
        tickColor: '#ccc',
      },
    },
    y: {
      field: field_key,
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
      { field: field_key, type: 'quantitative', format: ',.3r', title: field_title },
      ...tooltipFields.map((field) => ({ field, title: field })),
    ],
  },
});

export const ReturnPeriodDamageChart = ({
  data,
  field_key,
  field_title,
  width,
  height,
  tooltipFields = ['rcp', 'rp'],
  seriesField = 'rcp',
  ...props
}) => {
  const ref = useRef<HTMLDivElement>(null);
  const spec = useMemo(
    () =>
      makeSpec(
        unique<number>(data.table.map((d) => d.rp))
          .sort()
          .reverse(),
        field_key,
        field_title,
        width,
        height,
        tooltipFields,
        seriesField,
      ),
    [data, field_key, field_title, width, height, seriesField, tooltipFields],
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

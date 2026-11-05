import { useMemo, useRef, useEffect } from 'react';
import { useVegaEmbed } from 'react-vega';
import { VisualizationSpec } from 'vega-embed';
import { Box } from '@mui/material';

import { unique } from 'lib/helpers';
const makeSpec = (
  scenarios: string[],
  field_min: string,
  field: string,
  field_max: string,
  field_title: string,
  width: number,
  height: number,
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
    x: {
      field: 'scenario',
      type: 'ordinal',
      title: 'Model parameters',
      axis: {
        gridDash: [2, 2],
        domainColor: '#ccc',
        tickColor: '#ccc',
        values: scenarios,
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
      { field: 'scenario', title: 'Model parameters' },
    ],
  },
});

export const ExpectedDamageChart = ({
  data,
  field,
  field_min,
  field_max,
  field_title,
  width,
  height,
  ...props
}) => {
  const ref = useRef<HTMLDivElement>(null);
  const spec = useMemo(
    () =>
      makeSpec(
        unique<string>(data.table.map((d) => d.scenario)),
        field_min,
        field,
        field_max,
        field_title,
        width,
        height,
      ),
    [data, field_min, field, field_max, field_title, width, height],
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

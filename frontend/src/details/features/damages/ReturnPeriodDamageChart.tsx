import { useMemo, useRef, useEffect } from 'react';
import { useVegaEmbed } from 'react-vega';
import { VisualizationSpec } from 'vega-embed';
import { Box } from '@mui/material';

import { parameterLabel } from './parameter-labels';
import { seriesEncoding } from './chartStyles';

export const makeReturnPeriodDamageSpec = (
  field_key: string,
  field_title: string,
  width: number,
  height: number,
  tooltipFields: string[],
  seriesField?: string,
  seriesTitle = seriesField ? parameterLabel(seriesField) : null,
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
    ...seriesEncoding(seriesField, seriesTitle),
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
      ...tooltipFields.map((field) => ({
        field,
        title: field === seriesField ? seriesTitle : parameterLabel(field),
      })),
    ],
  },
});

export const ReturnPeriodDamageChart = ({
  data,
  field_key,
  field_title,
  width,
  height,
  seriesField = undefined,
  seriesTitle = seriesField ? parameterLabel(seriesField) : null,
  tooltipFields = seriesField ? [seriesField, 'rp'] : ['rp'],
  ...props
}) => {
  const ref = useRef<HTMLDivElement>(null);
  const spec = useMemo(
    () =>
      makeReturnPeriodDamageSpec(
        field_key,
        field_title,
        width,
        height,
        tooltipFields,
        seriesField,
        seriesTitle,
      ),
    [field_key, field_title, width, height, seriesField, seriesTitle, tooltipFields],
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

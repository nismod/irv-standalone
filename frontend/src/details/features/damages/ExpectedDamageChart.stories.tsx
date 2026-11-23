import type { Meta, StoryObj } from '@storybook/react-vite';
import { ExpectedDamageChart } from './ExpectedDamageChart';
import { expectedDamageDimensions, parameterField, parameterNames } from './chart-parameters';
import { parameterLabel } from './parameter-labels';
import {
  expectedDamageRows,
  gwlSlrParameters,
  rcpYearParameters,
  singleParameters,
} from './damage-story-fixtures';

function chartArgs(scenarios: Record<string, unknown>[]) {
  const table = expectedDamageRows(scenarios);
  const { x, series } = expectedDamageDimensions(table);
  return {
    data: { table },
    field: 'ead_mean',
    field_min: 'ead_amin',
    field_max: 'ead_amax',
    field_title: 'EAD (J$)',
    xField: x ? parameterField(x) : 'hazard',
    xTitle: x ? parameterLabel(x) : null,
    seriesField: series ? parameterField(series) : undefined,
    seriesTitle: series ? parameterLabel(series) : null,
    tooltipFields: parameterNames(table).map(parameterField),
    width: 400,
    height: 240,
    actions: false,
    renderer: 'svg',
  };
}

const meta = {
  title: 'Details/Features/Damages/ExpectedDamageChart',
  component: ExpectedDamageChart,
  args: chartArgs(rcpYearParameters),
} satisfies Meta<typeof ExpectedDamageChart>;
export default meta;
type Story = StoryObj<typeof meta>;

export const RCPAndYear: Story = {};
export const GWLAndSLR: Story = { args: chartArgs(gwlSlrParameters) };
export const SingleParameter: Story = { args: chartArgs(singleParameters) };
export const EconomicLosses: Story = {
  args: {
    ...chartArgs(rcpYearParameters),
    field: 'eael_mean',
    field_min: 'eael_amin',
    field_max: 'eael_amax',
    field_title: 'EAEL (J$/day)',
  },
};
export const MissingBounds: Story = {
  args: {
    ...chartArgs(singleParameters),
    data: {
      table: expectedDamageRows(singleParameters).map((row, index) => ({
        ...row,
        ead_amin: index === 1 ? null : row.ead_amin,
        ead_amax: index === 2 ? null : row.ead_amax,
      })),
    },
  },
};
export const MeansOnly: Story = {
  args: { field_min: undefined, field_max: undefined },
};

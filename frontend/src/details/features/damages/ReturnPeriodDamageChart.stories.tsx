import type { Meta, StoryObj } from '@storybook/react-vite';
import { ReturnPeriodDamageChart } from './ReturnPeriodDamageChart';
import { parameterField } from './chart-parameters';
import { parameterLabel } from './parameter-labels';
import { gwlSlrParameters, rcpYearParameters, returnPeriodDamageRows, singleParameters } from './damage-story-fixtures';

function chartArgs(scenarios: Record<string, unknown>[], series: string) {
  return {
    data: { table: returnPeriodDamageRows(scenarios) },
    field_key: 'damage_mean',
    field_title: 'Damage (J$)',
    seriesField: parameterField(series),
    seriesTitle: parameterLabel(series),
    tooltipFields: [parameterField(series), 'rp'],
    width: 400,
    height: 240,
    actions: false,
    renderer: 'svg',
  };
}

const meta = {
  title: 'Details/Features/Damages/ReturnPeriodDamageChart',
  component: ReturnPeriodDamageChart,
  args: chartArgs(rcpYearParameters.filter((parameters) => parameters.epoch === 2050), 'rcp'),
} satisfies Meta<typeof ReturnPeriodDamageChart>;
export default meta;
type Story = StoryObj<typeof meta>;

export const RCPAndReturnPeriod: Story = {};
export const GWLAndReturnPeriod: Story = {
  args: chartArgs(gwlSlrParameters.filter((parameters) => parameters.slr === 0.5), 'gwl'),
};
export const SingleParameter: Story = { args: chartArgs(singleParameters, 'gwl') };

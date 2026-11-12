import type { Meta, StoryObj } from '@storybook/react-vite';
import { expect, within } from 'storybook/test';
import { DamagesSection } from './DamagesSection';
import { expectedDamageRows, extraParameters, gwlSlrParameters, rcpYearParameters, returnPeriodDamageRows } from './damage-story-fixtures';

function sectionArgs(scenarios: Record<string, unknown>[]) {
  return { fd: {
    id: 1,
    damages_expected: expectedDamageRows(scenarios),
    damages_return_period: returnPeriodDamageRows(scenarios),
  } };
}

const meta = {
  title: 'Details/Features/Damages/DamagesSection',
  component: DamagesSection,
  args: sectionArgs(rcpYearParameters),
  decorators: [(Story) => <div style={{ width: '45ch' }}><Story /></div>],
} satisfies Meta<typeof DamagesSection>;
export default meta;
type Story = StoryObj<typeof meta>;

export const RCPAndYear: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.findByRole('combobox', { name: 'Year' })).resolves.toBeVisible();
    await expect(canvas.findAllByText('RCP', { selector: 'svg text' })).resolves.toHaveLength(3);
  },
};
export const GWLAndSLR: Story = { args: sectionArgs(gwlSlrParameters) };
export const ExtraParameters: Story = { args: sectionArgs(extraParameters) };
export const Empty: Story = {
  args: sectionArgs([]),
  play: async ({ canvasElement }) => {
    expect(within(canvasElement).getAllByText('No direct damages or indirect losses estimated.'))
      .toHaveLength(2);
  },
};

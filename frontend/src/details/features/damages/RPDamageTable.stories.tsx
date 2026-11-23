import type { Meta, StoryObj } from '@storybook/react-vite';
import { RPDamageTable } from './RPDamageTable';
import {
  gwlSlrParameters,
  rcpYearParameters,
  returnPeriodDamageRows,
  singleParameters,
} from './damage-story-fixtures';

const meta = {
  title: 'Details/Features/Damages/RPDamageTable',
  component: RPDamageTable,
  args: { damages: returnPeriodDamageRows(rcpYearParameters) },
  decorators: [
    (Story) => (
      <div style={{ width: '45ch' }}>
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof RPDamageTable>;
export default meta;
type Story = StoryObj<typeof meta>;

export const RCPAndYear: Story = {};
export const GWLAndSLR: Story = { args: { damages: returnPeriodDamageRows(gwlSlrParameters) } };
export const SingleParameter: Story = {
  args: { damages: returnPeriodDamageRows(singleParameters) },
};
export const Empty: Story = { args: { damages: [] } };

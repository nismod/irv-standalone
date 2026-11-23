import type { Meta, StoryObj } from '@storybook/react-vite';
import { DamageTable } from './DamageTable';
import {
  expectedDamageRows,
  gwlSlrParameters,
  rcpYearParameters,
  singleParameters,
} from './damage-story-fixtures';

const meta = {
  title: 'Details/Features/Damages/DamageTable',
  component: DamageTable,
  args: { damages: expectedDamageRows(rcpYearParameters) },
  decorators: [
    (Story) => (
      <div style={{ width: '45ch' }}>
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof DamageTable>;
export default meta;
type Story = StoryObj<typeof meta>;

export const RCPAndYear: Story = {};
export const GWLAndSLR: Story = { args: { damages: expectedDamageRows(gwlSlrParameters) } };
export const SingleParameter: Story = { args: { damages: expectedDamageRows(singleParameters) } };
export const Empty: Story = { args: { damages: [] } };

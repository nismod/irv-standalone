import type { Meta, StoryObj } from '@storybook/react-vite';
import { expect, userEvent, within } from 'storybook/test';
import { useAtom } from 'jotai';
import { ModelParameterControls } from './ModelParameterControls';
import { modelParametersState } from './state';
import { ModelScenario, selectParameters } from './scenarios';

const sparse: ModelScenario[] = [
  { hazard: 'heat', parameters: { gwl: 1.5, slr: 0, member: 'a' } },
  { hazard: 'heat', parameters: { gwl: 2, slr: 0.5, member: 'a' } },
  { hazard: 'heat', parameters: { gwl: 2, slr: 1, member: 'b' } },
];

function ScenarioPicker({ rows, error }: { rows?: ModelScenario[]; error?: string }) {
  const [preferred, setParameters] = useAtom(modelParametersState('damages_expected'));
  const parameters = selectParameters(rows ?? [], preferred);
  return (
    <div style={{ width: 300 }}>
      <ModelParameterControls
        rows={rows}
        parameters={parameters}
        onChange={setParameters}
        error={error}
      />
      <output data-testid="parameters">{JSON.stringify(parameters)}</output>
    </div>
  );
}

const meta = {
  title: 'Controls/Model scenarios',
  component: ScenarioPicker,
  args: { rows: sparse },
} satisfies Meta<typeof ScenarioPicker>;
export default meta;
type Story = StoryObj<typeof meta>;

export const SparseGWLAndSLR: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const body = within(canvasElement.ownerDocument.body);
    await userEvent.click(canvas.getByRole('combobox', { name: 'GWL' }));
    await userEvent.click(await body.findByRole('option', { name: '2' }));
    expect(canvas.getByTestId('parameters')).toHaveTextContent('"gwl":2,"slr":0.5,"member":"a"');
    await userEvent.click(canvas.getByRole('combobox', { name: 'member' }));
    await userEvent.click(await body.findByRole('option', { name: 'b' }));
    expect(canvas.getByTestId('parameters')).toHaveTextContent('"gwl":2,"slr":1,"member":"b"');
    expect(canvas.queryByRole('combobox', { name: 'RCP' })).not.toBeInTheDocument();
  },
};
export const RCPAndYear: Story = {
  args: {
    rows: [
      { hazard: 'flood', parameters: { rcp: 'baseline', epoch: 2010 } },
      { hazard: 'flood', parameters: { rcp: '4.5', epoch: 2050 } },
    ],
  },
};
export const NoParameters: Story = { args: { rows: [{ hazard: 'heat', parameters: {} }] } };
export const Loading: Story = { args: { rows: undefined } };
export const Empty: Story = { args: { rows: [] } };
export const Error: Story = { args: { rows: [], error: 'Unable to load model scenarios.' } };

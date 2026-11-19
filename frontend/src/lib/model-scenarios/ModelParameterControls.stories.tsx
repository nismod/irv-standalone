import type { Meta, StoryObj } from '@storybook/react-vite';
import { expect, userEvent, within } from 'storybook/test';
import { useAtom } from 'jotai';
import { useState } from 'react';
import { ModelParameterControls } from './ModelParameterControls';
import { ModelParameterControl, type NumericControl } from './ModelParameterControl';
import { modelParametersState } from './state';
import { ModelScenario, parameterKey, selectResult } from './scenarios';

const sparse: ModelScenario[] = [
  { hazard: 'heat', parameters: { gwl: 1.5, slr: 0, member: 'a' } },
  { hazard: 'heat', parameters: { gwl: 2, slr: 0.5, member: 'a' } },
  { hazard: 'heat', parameters: { gwl: 2, slr: 1, member: 'b' } },
];

function ScenarioPicker({
  rows,
  error,
  numericControl = 'select',
}: {
  rows?: ModelScenario[];
  error?: string;
  numericControl?: NumericControl;
}) {
  const [preferred, setParameters] = useAtom(modelParametersState('damages_expected'));
  const [protection, setProtection] = useState(0);
  const result = selectResult(rows ?? [], preferred, { protection_standard: protection });
  const parameters = result?.parameters ?? null;
  const protectionLevels = [
    ...new Set(
      (rows ?? [])
        .filter((row) => result && parameterKey(row.parameters) === parameterKey(result.parameters))
        .map((row) => row.protection_standard),
    ),
  ].filter((value) => typeof value === 'number');
  return (
    <div style={{ width: 300 }}>
      <ModelParameterControls
        rows={rows}
        parameters={parameters}
        onChange={setParameters}
        error={error}
        numericControl={numericControl}
      />
      {protectionLevels.length > 1 && (
        <ModelParameterControl
          title="Protection standard"
          value={result.protection_standard}
          options={protectionLevels}
          onChange={setProtection}
          numericControl={numericControl}
        />
      )}
      <output data-testid="parameters">{JSON.stringify(parameters)}</output>
      <output data-testid="protection">{result?.protection_standard}</output>
    </div>
  );
}

const meta = {
  title: 'Controls/Model scenarios',
  component: ScenarioPicker,
  args: { rows: sparse },
  argTypes: { numericControl: { control: 'radio', options: ['select', 'slider'] } },
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

export const NumericSliders: Story = {
  args: {
    numericControl: 'slider',
    rows: [
      { gwl: 0.75, slr: 0, member: 'a' },
      { gwl: 2, slr: 20, member: 'a' },
      { gwl: 2, slr: 80, member: 'a' },
      { gwl: 5, slr: 80, member: 'a' },
    ].flatMap((parameters) =>
      [0, 100].map((protection_standard) => ({ hazard: 'flood', parameters, protection_standard })),
    ),
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const gwl = canvas.getByRole('slider', { name: 'GWL' });
    expect(gwl).toHaveAttribute('aria-valuetext', '0.75');
    expect(canvas.getByRole('slider', { name: 'SLR' })).toBeDisabled();
    expect(canvas.getByRole('combobox', { name: 'member' })).toHaveAttribute(
      'aria-disabled',
      'true',
    );
    gwl.focus();
    await userEvent.keyboard('{ArrowRight}');
    expect(gwl).toHaveAttribute('aria-valuetext', '2');
    expect(canvas.getByTestId('parameters')).toHaveTextContent('"gwl":2,"slr":20');
    const slr = canvas.getByRole('slider', { name: 'SLR' });
    expect(slr).toBeEnabled();
    slr.focus();
    await userEvent.keyboard('{End}');
    expect(slr).toHaveAttribute('aria-valuetext', '80');
    const protection = canvas.getByRole('slider', { name: 'Protection standard' });
    protection.focus();
    await userEvent.keyboard('{End}');
    expect(protection).toHaveAttribute('aria-valuetext', '100');
    expect(canvas.getByTestId('protection')).toHaveTextContent('100');
    gwl.focus();
    await userEvent.keyboard('{End}');
    expect(gwl).toHaveAttribute('aria-valuetext', '5');
    expect(canvas.getByTestId('parameters')).toHaveTextContent('"gwl":5,"slr":80');
    expect(canvas.getByRole('slider', { name: 'SLR' })).toBeDisabled();
    expect(canvas.getByTestId('protection')).toHaveTextContent('100');
  },
};

export const NumericStringsStaySelects: Story = {
  args: {
    numericControl: 'slider',
    rows: ['2', '5'].map((gwl) => ({ hazard: 'flood', parameters: { gwl } })),
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    expect(canvas.queryByRole('slider')).not.toBeInTheDocument();
    await userEvent.click(canvas.getByRole('combobox', { name: 'GWL' }));
    await userEvent.click(
      await within(canvasElement.ownerDocument.body).findByRole('option', { name: '5' }),
    );
    expect(canvas.getByTestId('parameters')).toHaveTextContent('"gwl":"5"');
  },
};

export const NumericSelects: Story = {
  args: { rows: NumericSliders.args.rows },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    expect(canvas.queryByRole('slider')).not.toBeInTheDocument();
    expect(canvas.getByRole('combobox', { name: 'GWL' })).toBeEnabled();
    await userEvent.click(canvas.getByRole('combobox', { name: 'Protection standard' }));
    await userEvent.click(
      await within(canvasElement.ownerDocument.body).findByRole('option', { name: '100' }),
    );
    expect(canvas.getByTestId('protection')).toHaveTextContent('100');
  },
};

export const SingleNumericValue: Story = {
  args: { numericControl: 'slider', rows: [{ hazard: 'flood', parameters: { gwl: 2 } }] },
  play: async ({ canvasElement }) => {
    const slider = within(canvasElement).getByRole('slider', { name: 'GWL' });
    expect(slider).toBeDisabled();
    expect(slider).toHaveAttribute('aria-valuetext', '2');
    expect(slider).toHaveAttribute('aria-valuemin', '2');
    expect(slider).toHaveAttribute('aria-valuemax', '2');
  },
};

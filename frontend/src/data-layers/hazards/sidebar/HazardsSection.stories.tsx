import { StoryObj, Meta } from '@storybook/react-vite';
import { expect, within } from 'storybook/test';

import { HazardsSection } from './HazardsSection';
import { HttpResponse, http } from 'msw';
import rasterSourceDomains from 'mocks/raster_source_domains.json';

function fixedWidthDecorator(Story) {
  return (
    <div style={{ width: '300px' }}>
      <Story />
    </div>
  );
}

const meta = {
  title: 'Sidebar/HazardsSection',
  component: HazardsSection,
  decorators: [fixedWidthDecorator],
  parameters: {
    msw: {
      handlers: [
        http.get('/api/tiles/raster/sources/1/domains', () => {
          return HttpResponse.json(rasterSourceDomains);
        }),
      ],
    }
  },
} as Meta;

export default meta;
type Story = StoryObj<typeof meta>;

export const Exposure: Story = {
  args: {
    view: 'exposure',
  },
  play: ({ canvasElement }) => {
    const canvas = within(canvasElement);
    expect(canvas.queryByText('Hazards')).toBeTruthy();
  },
};

export const Risk: Story = {
  args: {
    view: 'risk',
  },
  play: ({ canvasElement }) => {
    const canvas = within(canvasElement);
    expect(canvas.queryByText('Hazards')).toBeTruthy();
  },
};

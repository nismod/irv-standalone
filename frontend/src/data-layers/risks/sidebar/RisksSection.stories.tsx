import { StoryObj, Meta } from '@storybook/react-vite';
import { expect, within } from 'storybook/test';
import { HttpResponse, http } from 'msw';

import { RisksSection } from './RisksSection';
import rasterSourceDomains from 'mocks/raster_source_domains.json';

function fixedWidthDecorator(Story) {
  return (
    <div style={{ width: '300px' }}>
      <Story />
    </div>
  );
}

const meta = {
  title: 'Sidebar/RisksSection',
  component: RisksSection,
  decorators: [fixedWidthDecorator],
  parameters: {
    msw: {
      handlers: [
        http.get('/api/tiles/raster/sources/:datasetId/domains', () => {
          return HttpResponse.json(rasterSourceDomains);
        }),
      ],
    },
  },
} as Meta;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    view: 'risk',
  },
  play: ({ canvasElement }) => {
    const canvas = within(canvasElement);
    expect(canvas.queryByText('Hotspots')).toBeTruthy();
  },
};

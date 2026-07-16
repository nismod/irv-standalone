import { StoryObj, Meta } from '@storybook/react-vite';
import { expect, waitFor, within } from 'storybook/test';
import { HttpResponse, http } from 'msw';

import { NetworksSection } from './NetworksSection';
import rasterSourceDomains from 'mocks/raster_source_domains.json';

const mockInfrastructureTree = {
  count: 2,
  next: null,
  previous: null,
  results: [
    {
      node_id: 'power',
      node_name: 'Power',
      parent: null,
      children: [
        {
          node_id: 'power-lines',
          node_name: 'Transmission',
          parent: 'power',
          children: [
            {
              node_id: 'elec_edges_high',
              node_name: 'High voltage',
              parent: 'power-lines',
              children: [],
            },
            {
              node_id: 'elec_edges_low',
              node_name: 'Low voltage',
              parent: 'power-lines',
              children: [],
            },
          ],
        },
      ],
    },
    {
      node_id: 'transport',
      node_name: 'Transport',
      parent: null,
      children: [
        {
          node_id: 'road-network',
          node_name: 'Road network',
          parent: 'transport',
          children: [
            {
              node_id: 'roads',
              node_name: 'Roads',
              parent: 'road-network',
              children: [
                {
                  node_id: 'road_edges_class_a',
                  node_name: 'Class A',
                  parent: 'roads',
                  children: [],
                },
                {
                  node_id: 'road_edges_motorway',
                  node_name: 'Toll',
                  parent: 'roads',
                  children: [],
                },
              ],
            },
          ],
        },
      ],
    },
  ],
};

function fixedWidthDecorator(Story) {
  return (
    <div style={{ width: '300px' }}>
      <Story />
    </div>
  );
}

const meta = {
  title: 'Sidebar/NetworksSection',
  component: NetworksSection,
  decorators: [fixedWidthDecorator],
  argTypes: {
    view: {
      control: {
        type: 'select',
      },
      options: ['exposure', 'risk', 'adaptation'],
    },
  },
  parameters: {
    msw: {
      handlers: [
        http.get('/api/map/infrastructure-tree', () => {
          return HttpResponse.json(mockInfrastructureTree);
        }),
        http.get('/api/tiles/raster/sources/:domain/domains', () => {
          return HttpResponse.json(rasterSourceDomains);
        }),
      ],
    },
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
    expect(canvas.queryByText('Infrastructure')).toBeTruthy();
    expect(
      canvas.queryByText(
        'Infrastructure layers are currently following the Adaptation Options selection',
      ),
    ).toBeFalsy();
  },
};

export const Risk: Story = {
  args: {
    view: 'risk',
  },
  play: ({ canvasElement }) => {
    const canvas = within(canvasElement);
    expect(canvas.queryByText('Infrastructure')).toBeTruthy();
    expect(
      canvas.queryByText(
        'Infrastructure layers are currently following the Adaptation Options selection',
      ),
    ).toBeFalsy();
  },
};

export const Adaptation: Story = {
  args: {
    view: 'adaptation',
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    expect(canvas.queryByText('Infrastructure')).toBeTruthy();
    await waitFor(() => {
      expect(
        canvas.queryByText(
          'Infrastructure layers are currently following the Adaptation Options selection',
        ),
      ).toBeTruthy();
    });
  },
};

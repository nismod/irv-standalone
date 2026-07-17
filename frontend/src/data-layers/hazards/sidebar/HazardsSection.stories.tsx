import { StoryObj, Meta } from '@storybook/react-vite';
import { expect, within } from 'storybook/test';
import { HttpResponse, http } from 'msw';

import { HazardsSection } from './HazardsSection';
import rasterSourceDomains from 'mocks/raster_source_domains.json';
import { type PaginatedDatasetList } from 'lib/api-client';

const hazardsResponse: PaginatedDatasetList = {
  count: 5,
  next: null,
  previous: null,
  results: [
    {
      id: 'fluvial',
      label: 'River Flooding',
      group: 'hazards',
      unit: 'm',
      stacking_order: 2,
      display_order: 0,
      has_access: true,
    },
    {
      id: 'surface',
      label: 'Surface Flooding',
      group: 'hazards',
      unit: 'm',
      stacking_order: 3,
      display_order: 1,
      has_access: true,
    },
    {
      id: 'coastal',
      label: 'Coastal Flooding',
      group: 'hazards',
      unit: 'm',
      stacking_order: 4,
      display_order: 2,
      has_access: true,
    },
    {
      id: 'cyclone',
      label: 'Tropical cyclone wind speed',
      group: 'hazards',
      unit: 'm/s',
      stacking_order: 1,
      display_order: 3,
      has_access: true,
    },
    {
      id: 'storm',
      label: 'Tropical cyclone return period',
      group: 'hazards',
      unit: 'yrs',
      stacking_order: 0,
      display_order: 4,
      has_access: true,
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
  title: 'Sidebar/HazardsSection',
  component: HazardsSection,
  decorators: [fixedWidthDecorator],
  parameters: {
    msw: {
      handlers: [
        http.get('/api/map/datasets', () => {
          return HttpResponse.json(hazardsResponse);
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
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    expect(await canvas.findByText('Hazards')).toBeTruthy();

    for (const dataset of hazardsResponse.results) {
      const control = await canvas.findByText(dataset.label);
      expect(control.closest('.MuiAccordion-root')).not.toHaveClass('Mui-disabled');
    }
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

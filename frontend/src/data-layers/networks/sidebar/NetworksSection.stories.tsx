import { StoryObj, Meta } from '@storybook/react-vite';
import { expect, userEvent, waitFor, within } from 'storybook/test';
import { HttpResponse, http } from 'msw';
import { useEffect } from 'react';
import { useSetAtom } from 'jotai';

import { NetworksSection } from './NetworksSection';
import rasterSourceDomains from 'mocks/raster_source_domains.json';
import { type PaginatedDatasetList, type RasterTileSource } from 'lib/api-client';
import {
  sectionStyleOptionsState,
  sectionStyleValueState,
  sectionVisibilityState,
} from 'lib/state/sections';
import { STORAGE_PREFIX } from 'lib/state/map-view/map-url';
import {
  networkTreeExpandedState,
} from '../state/data-selection';

const hazardsResponse: PaginatedDatasetList = {
  count: 2,
  next: null,
  previous: null,
  results: [
    {
      id: 'fluvial',
      label: 'River Flooding',
      group: 'hazards',
      quantity: 'depth',
      unit: 'm',
      tile_source: 1,
      stacking_order: 1,
      display_order: 1,
      has_access: true,
    },
    {
      id: 'coastal',
      label: 'Coastal Flooding',
      group: 'hazards',
      quantity: 'depth',
      unit: 'm',
      tile_source: 1,
      stacking_order: 2,
      display_order: 2,
      has_access: false,
    },
  ],
};

const networksResponse: PaginatedDatasetList = {
  count: 3,
  next: null,
  previous: null,
  results: [
    {
      id: 'road_edges_class_a',
      label: 'Class A roads',
      group: 'networks',
      quantity: 'features',
      unit: 'n/a',
      tile_source: null,
      stacking_order: 1,
      display_order: 1,
      has_access: true,
    },
    {
      id: 'road_edges_motorway',
      label: 'Toll roads',
      group: 'networks',
      quantity: 'features',
      unit: 'n/a',
      tile_source: null,
      stacking_order: 2,
      display_order: 2,
      has_access: false,
    },
    {
      id: 'buildings_resort',
      label: 'Resort buildings',
      group: 'buildings',
      quantity: 'features',
      unit: 'n/a',
      tile_source: null,
      stacking_order: 3,
      display_order: 3,
      has_access: false,
    },
  ],
};

const rasterSourceResponse: RasterTileSource = {
  id: 1,
  keys: ['type', 'rp', 'rcp', 'epoch', 'confidence'],
};

const networkLayerStylesResponse = {
  results: [
    {
      id: 'road_edges_class_a',
      type: 'line',
      label: 'Class A roads',
      color: '#3f51b5',
      minZoom: null,
    },
    {
      id: 'road_edges_motorway',
      type: 'line',
      label: 'Toll roads',
      color: '#f57c00',
      minZoom: null,
    },
  ],
};

const networkStyleOptions = [
  { id: 'type', label: 'Asset type' },
  { id: 'damages', label: 'Damages' },
  { id: 'adaptation', label: 'Adaptation Options' },
  { id: 'protectedFeatures', label: 'Protected Features' },
];

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
    {
      node_id: 'buildings',
      node_name: 'Buildings',
      parent: null,
      children: [
        {
          node_id: 'buildings_resort',
          node_name: 'Resort',
          parent: 'buildings',
          children: [],
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

function storyStyleForView(view: string) {
  switch (view) {
    case 'risk':
      return 'damages';
    case 'adaptation':
      return 'adaptation';
    default:
      return 'type';
  }
}

function StoryState({ Story, view }) {
  const setAssetsVisible = useSetAtom(sectionVisibilityState('assets'));
  const setAssetsStyle = useSetAtom(sectionStyleValueState('assets'));
  const setAssetsStyleOptions = useSetAtom(sectionStyleOptionsState('assets'));
  const setExpanded = useSetAtom(networkTreeExpandedState);

  useEffect(() => {
    sessionStorage.removeItem(`${STORAGE_PREFIX}netTree`);
    const url = new URL(window.location.href);
    url.searchParams.delete('netTree');
    window.history.replaceState({}, '', url.toString());

    setAssetsVisible(true);
    setAssetsStyleOptions(networkStyleOptions);
    setAssetsStyle(storyStyleForView(view));
    setExpanded(['power', 'power-lines', 'transport', 'road-network', 'roads', 'buildings']);
  }, [setAssetsStyle, setAssetsStyleOptions, setAssetsVisible, setExpanded, view]);

  return <Story />;
}

const meta = {
  title: 'Sidebar/NetworksSection',
  component: NetworksSection,
  decorators: [
    fixedWidthDecorator,
    (Story, { args }) => <StoryState Story={Story} view={args.view} />,
  ],
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
        http.get('/api/map/datasets', ({ request }) => {
          const url = new URL(request.url);
          if (url.searchParams.get('group') === 'networks') {
            return HttpResponse.json({
              ...networksResponse,
              count: 2,
              results: networksResponse.results.filter(
                (dataset) => dataset.group === 'networks',
              ),
            });
          }
          if (url.searchParams.get('group') === 'hazards') {
            return HttpResponse.json(hazardsResponse);
          }
          return HttpResponse.json({
            ...networksResponse,
            count: networksResponse.results.length + hazardsResponse.results.length,
            results: [...networksResponse.results, ...hazardsResponse.results],
          });
        }),
        http.get('/api/map/network-layer-styles', () => {
          return HttpResponse.json(networkLayerStylesResponse);
        }),
        http.get('/api/tiles/raster/sources/:datasetId/domains', () => {
          return HttpResponse.json(rasterSourceDomains);
        }),
        http.get('/api/tiles/raster/sources/:sourceId', () => {
          return HttpResponse.json(rasterSourceResponse);
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
    expect(canvas.queryByText('Infrastructure')).toBeTruthy();
    expect(
      canvas.queryByText(
        'Infrastructure layers are currently following the Adaptation Options selection',
      ),
    ).toBeFalsy();
    expect(await canvas.findByRole('checkbox', { name: 'Class A' })).toBeEnabled();
    expect(await canvas.findByRole('checkbox', { name: 'Toll' })).toBeDisabled();
    expect(await canvas.findByRole('checkbox', { name: 'Buildings' })).toBeDisabled();
    expect(await canvas.findByRole('checkbox', { name: 'Resort' })).toBeDisabled();

    const classACheckbox = await canvas.findByRole('checkbox', { name: 'Class A' });
    expect(classACheckbox).not.toBeChecked();

    await userEvent.click(classACheckbox);
    expect(classACheckbox).toBeChecked();

    await userEvent.click(classACheckbox);
    expect(classACheckbox).not.toBeChecked();
  },
};

export const Risk: Story = {
  args: {
    view: 'risk',
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    expect(canvas.queryByText('Infrastructure')).toBeTruthy();
    expect(
      canvas.queryByText(
        'Infrastructure layers are currently following the Adaptation Options selection',
      ),
    ).toBeFalsy();
    expect(await canvas.findByRole('radio', { name: 'River Flooding' })).toBeEnabled();
    expect(await canvas.findByRole('radio', { name: 'Coastal Flooding' })).toBeDisabled();
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

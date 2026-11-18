import { StoryObj, Meta } from '@storybook/react-vite';
import { expect, within } from 'storybook/test';
import { http, HttpResponse } from 'msw';
import { useEffect } from 'react';
import { useAtom } from 'jotai';

import { selectionState } from 'lib/state/interactions/interaction-state';
import mockFeature from 'mocks/details/features/mockFeature.json';
import mockFeatureDetails from 'mocks/details/features/mockFeatureDetails.json';
import rasterSourceDomains from 'mocks/raster_source_domains.json';
import { FeatureSidebar } from './FeatureSidebar';
import { Layer } from 'deck.gl';
import { type RasterTileSource } from 'lib/api-client';

const rasterSourceResponse: RasterTileSource = {
  id: 1,
  keys: ['type', 'rp', 'rcp', 'epoch', 'confidence'],
};

const networkLayerStylesResponse = {
  results: [
    {
      id: 'road_edges_class_b',
      type: 'line',
      label: 'Roads (Class B)',
      color: '#cb3e4e',
      minZoom: null,
    },
  ],
};

function FixedWidthDecorator(Story) {
  return (
    <div style={{ width: '45ch' }}>
      <Story />
    </div>
  );
}

function DataLoaderDecorator(Story, { args }) {
  const [, setFeatureSelection] = useAtom(selectionState('assets'));

  useEffect(() => {
    const mockSelection = {
      interactionGroup: 'assets',
      interactionStyle: 'vector',
      target: {
        feature: args.feature,
      },
      viewLayer: {
        id: args.id,
        group: 'networks',
        fn: () => ({}) as Layer,
      },
    };
    setFeatureSelection(mockSelection);
  }, [setFeatureSelection, args]);

  return <Story />;
}

function sidebarParameters(currency: string) {
  return {
    msw: {
      handlers: [
        http.get('/api/map/config', () => HttpResponse.json({
          count: 1,
          next: null,
          previous: null,
          results: [{
            config_name: 'currency',
            config_value: currency,
            config_type: 'string',
          }],
        })),
        http.get('/api/map/features/1000036526', () => {
          return HttpResponse.json({
            ...mockFeatureDetails,
            properties: {
              ...mockFeatureDetails.properties,
              cost_unit: `${currency}/m`,
            },
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
  };
}

const meta = {
  title: 'Details/FeatureSidebar',
  component: FeatureSidebar,
  decorators: [FixedWidthDecorator, DataLoaderDecorator],
  args: {
    feature: mockFeature,
    id: 'road_edges_class_b',
  },
  parameters: sidebarParameters('JMD'),
} as Meta;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.findByText('Roads (Class B)')).resolves.toBeVisible();
    await expect(canvas.findByText('Risk')).resolves.toBeVisible();
    await expect(canvas.findByText('Return Period Damages')).resolves.toBeVisible();
    await expect(canvas.findByText('Adaptation Options')).resolves.toBeVisible();
    await expect(canvas.findByText('EAD (JMD)', { selector: 'abbr' })).resolves.toBeVisible();
  },
};

export const MauritianRupees: Story = {
  parameters: sidebarParameters('MUR'),
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.findByText('EAD (MUR)', { selector: 'abbr' })).resolves.toBeVisible();
    await expect(canvas.findByRole('columnheader', { name: /EAEL.*\(MUR\/day\)/ }))
      .resolves.toBeVisible();
    await expect(canvas.findByRole('columnheader', { name: 'Damages (MUR)' }))
      .resolves.toBeVisible();
    await expect(canvas.findByRole('columnheader', { name: 'Loss (MUR/day)' }))
      .resolves.toBeVisible();
    await expect(canvas.findAllByRole('columnheader', { name: 'Avoided Risk (MUR)' }))
      .resolves.not.toHaveLength(0);
  },
};

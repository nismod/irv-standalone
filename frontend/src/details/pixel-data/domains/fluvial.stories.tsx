import type { Meta, StoryObj } from '@storybook/react-vite';
import { http, HttpResponse } from 'msw';
import { useHydrateAtoms } from 'jotai/utils';

import { pixelSelectionState } from 'lib/state/pixel-driller';
import { DownloadDataProvider } from '../download/download-context';
import { FluvialDataSection } from './fluvial';

const mockPixelData = {
  key: [
    'fluvial__gwl_0__rp_5',
    'fluvial__gwl_0__rp_20',
    'fluvial__gwl_0__rp_100',
    'fluvial__gwl_2__rp_5',
    'fluvial__gwl_2__rp_20',
    'fluvial__gwl_2__rp_100',
  ],
  hazard: ['fluvial', 'fluvial', 'fluvial', 'fluvial', 'fluvial', 'fluvial'],
  gwl: [0, 0, 0, 2, 2, 2],
  rp: [5, 20, 100, 5, 20, 100],
  unit: ['m', 'm', 'm', 'm', 'm', 'm'],
  variable: ['depth', 'depth', 'depth', 'depth', 'depth', 'depth'],
  band_data: [0.1, 0.45, 1.8, 0.2, 0.7, 2.2],
};

function Decorator(Story) {
  useHydrateAtoms([[pixelSelectionState, { lat: -78.1, lon: 18.1 }]]);
  return (
    <DownloadDataProvider>
      <div style={{ width: '60ch' }}>
        <Story />
      </div>
    </DownloadDataProvider>
  );
}

const meta = {
  title: 'Details/PixelData/Domains/Fluvial',
  component: FluvialDataSection,
  decorators: [Decorator],
} satisfies Meta<typeof FluvialDataSection>;

export default meta;
type Story = StoryObj<typeof meta>;

export const GWLAndReturnPeriod: Story = {
  args: {
    pixel_layer: 'fluvial',
  },
  parameters: {
    msw: {
      handlers: [
        http.get('/api/pixel/:lon/:lat', () => HttpResponse.json(mockPixelData)),
      ],
    },
  },
};

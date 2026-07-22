import { StoryObj, Meta } from '@storybook/react-vite';
import { http, HttpResponse } from 'msw';
import { DataPage } from './DataPage';

const meta = {
  title: 'App/DataPage',
  component: DataPage,
} as Meta;
type Story = StoryObj<typeof meta>;

export default meta;

export const Default: Story = {
  parameters: {
    msw: {
      handlers: [
        http.get('/api/content/data', () =>
          HttpResponse.json([
            {
              slot: 'access_notice',
              markdown:
                'The systemic risk analysis results shown in this tool contain licensed data that must not be shared outside the Government of Jamaica.',
            },
            {
              slot: 'release_notice',
              markdown:
                'The tool has recently been released. Please tell us if anything is not working as it should and suggest potential improvements.',
            },
            {
              slot: 'content',
              markdown:
                'The modelling and analysis presented here aim to support climate adaptation decision-making.\n\n| Infrastructure Sector | Assets |\n| --- | --- |\n| Transport | Road links and railway lines, ports and airports |\n\n## Open-source code\n\n- [github.com/nismod/irv-jamaica](https://github.com/nismod/irv-jamaica)\n\n# Data Sources and Access\n\nData comes from multiple sources, including Government of Jamaica bodies, private sector entities, and open data sources.\n\n[[access-notice]]\n\n## Hazard Data\n\n| Hazard type | Data source |\n| --- | --- |\n| Fluvial flooding | [JBA global flood map product](https://www.jbarisk.com/flood-services/maps-and-analytics/global-flood-maps/) |\n\n## Infrastructure Network Data\n\n| Sector | Sub-sector |\n| --- | --- |\n| Energy | Generation |\n| Transport | Airports |\n\n## Contextual Map Data\n\nBackground map data is copyright [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors.',
            },
          ]),
        ),
      ],
    },
  },
};

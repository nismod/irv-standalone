import { StoryObj, Meta } from '@storybook/react-vite';
import { http, HttpResponse } from 'msw';
import { GuidePage } from './GuidePage';

const meta = {
  title: 'App/GuidePage',
  component: GuidePage,
} as Meta;
type Story = StoryObj<typeof meta>;

export default meta;

export const Default: Story = {
  parameters: {
    msw: {
      handlers: [
        http.get('/api/content/guide', () =>
          HttpResponse.json([
            {
              slot: 'content',
              markdown:
                '# User Guide for the Jamaica Systemic Risk Assessment Tool (J-SRAT)\n\n[How to use this guide](#how-to-use-this-guide)\n\n## How to use this guide\n\n[Back to top](#user-guide-for-the-jamaica-systemic-risk-assessment-tool-j-srat)\n\nThis guide is intended to accompany the interactive web-based platform.\n\n![Homepage](/guide_media/image2.png)\n\n## About this guide\n\nThis document may be cited as follows:\n\n> Example citation.',
            },
          ]),
        ),
      ],
    },
  },
};

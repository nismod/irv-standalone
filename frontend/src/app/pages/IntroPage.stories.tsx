import { StoryObj, Meta } from '@storybook/react-vite';
import { http, HttpResponse } from 'msw';
import { IntroPage } from './IntroPage';

const meta = {
  title: 'App/IntroPage',
  component: IntroPage,
} as Meta;
type Story = StoryObj<typeof meta>;

export default meta;

export const Default: Story = {
  parameters: {
    msw: {
      handlers: [
        http.get('/api/content/intro', () =>
          HttpResponse.json([
            { slot: 'summary', markdown: 'Intro summary' },
            { slot: 'collaboration', markdown: 'Collaboration' },
            { slot: 'funding', markdown: '## Funding and support' },
            { slot: 'background-credit', markdown: 'Background image credit' },
          ]),
        ),
        http.get('/api/content/intro/logos', () =>
          HttpResponse.json([
            {
              slot: 'collaboration',
              src: '/jamaica-coatofarms.png',
              href: 'https://www.gov.jm',
              alt: 'Government of Jamaica',
              height: 150,
            },
            {
              slot: 'funding',
              src: '/logo-ukaid.png',
              href: 'https://www.gov.uk/guidance/uk-aid',
              alt: 'UK AID',
              height: 100,
            },
          ]),
        ),
      ],
    },
  },
};

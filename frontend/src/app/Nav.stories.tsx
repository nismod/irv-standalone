import { StoryObj, Meta } from '@storybook/react-vite';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';

import { navItems } from 'App';
import { globalStyleVariables } from './theme';
import { Nav } from './Nav';

const mapConfigHandler = http.get('/api/map/config', () =>
  HttpResponse.json({
    count: 1,
    next: null,
    previous: null,
    results: [
      {
        config_name: 'appName',
        config_value: 'J-SRAT',
        config_type: 'string',
      },
    ],
  }),
);

function withQueryClient(Story) {
  const queryClient = new QueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      <Story />
    </QueryClientProvider>
  );
}

const meta = {
  title: 'App/Nav',
  component: Nav,
  decorators: [withQueryClient],
  parameters: {
    msw: {
      handlers: [
        mapConfigHandler,
        http.get('/api/auth/me', () =>
          HttpResponse.json({ authenticated: false, user: null }),
        ),
      ],
    },
  },
} as Meta;
type Story = StoryObj<typeof meta>;

export default meta;

export const Default: Story = {
  args: {
    height: globalStyleVariables.navbarHeight,
    navItems,
  },
};

export const LoggedIn: Story = {
  args: {
    height: globalStyleVariables.navbarHeight,
    navItems,
  },
  parameters: {
    msw: {
      handlers: [
        mapConfigHandler,
        http.get('/api/auth/me', () =>
          HttpResponse.json({
            authenticated: true,
            user: {
              id: 1,
              username: 'jsmith',
              first_name: 'Jordan',
              last_name: 'Smith',
              email: 'jordan.smith@example.com',
            },
          }),
        ),
        http.post('/api/auth/logout', () =>
          HttpResponse.json({ authenticated: false, user: null }),
        ),
      ],
    },
  },
};

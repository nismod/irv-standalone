import { Meta, StoryObj } from '@storybook/react-vite';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { expect, userEvent, within } from 'storybook/test';

import { LoginRequiredPage } from './LoginRequiredPage';

function withQueryClient(Story) {
  const queryClient = new QueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      <div style={{ height: '100vh' }}>
        <Story />
      </div>
    </QueryClientProvider>
  );
}

const meta = {
  title: 'App/LoginRequiredPage',
  component: LoginRequiredPage,
  decorators: [withQueryClient],
} as Meta;

type Story = StoryObj<typeof meta>;

export default meta;

export const Default: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);

    expect(await canvas.findByText('Sign in to view maps')).toBeTruthy();
    expect(await canvas.findByLabelText(/Username/i)).toBeTruthy();
    expect(await canvas.findByLabelText(/Password/i)).toBeTruthy();
    expect(await canvas.findByRole('button', { name: 'Sign in' })).toBeTruthy();
  },
};

export const InvalidCredentials: Story = {
  parameters: {
    msw: {
      handlers: [
        http.post('/api/auth/login', () =>
          HttpResponse.json(
            { detail: 'Invalid username or password.' },
            { status: 401 },
          ),
        ),
      ],
    },
  },
  play: async ({ canvasElement }) => {
    document.cookie = 'csrftoken=test-story-token; path=/';

    const canvas = within(canvasElement);

    await userEvent.type(await canvas.findByLabelText(/Username/i), 'testuser');
    await userEvent.type(await canvas.findByLabelText(/Password/i), 'bad-password');
    await userEvent.click(await canvas.findByRole('button', { name: 'Sign in' }));

    expect(await canvas.findByText('Invalid username or password.')).toBeTruthy();
  },
};

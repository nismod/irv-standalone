import { CssBaseline } from '@mui/material';
import { StyledEngineProvider } from '@mui/styled-engine';
import { ThemeProvider } from '@mui/material/styles';
import type { Preview } from '@storybook/react-vite';
import { mswLoader } from 'msw-storybook-addon/csf3';
import { setupWorker } from 'msw/browser';
import { BrowserRouter as Router } from 'react-router-dom';
import { Provider, atom } from 'jotai';

import { theme } from '../src/app/theme';
import { useSyncRecoilState } from '../src/lib/recoil/sync-state';
import { viewStateEffect } from '../src/app/state/view';
import { useStateEffect } from '../src/lib/recoil/state-effects/use-state-effect';
import { viewSectionsState } from '../src/app/config/views';
import { sectionsConfigState } from '../src/app/config/sections';

const initializeMsw = async () => {
  const worker = setupWorker();
  await worker.start({
    serviceWorker: {
      url: `${import.meta.env.BASE_URL}mockServiceWorker.js`,
    },
  });
  return worker;
};

const mockViewState = atom('exposure');
const mockViewStateEffectState = atom((get) => ({
  view: get(mockViewState),
  sectionsConfig: get(sectionsConfigState),
  viewSections: get(viewSectionsState) ?? {},
}));

function SectionStyle({ children, view }) {
  useSyncRecoilState(mockViewState, view);
  useStateEffect(mockViewStateEffectState, viewStateEffect);
  return children;
}

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },

    a11y: {
      // 'todo' - show a11y violations in the test UI only
      // 'error' - fail CI on a11y violations
      // 'off' - skip a11y checks entirely
      test: 'todo',
    },
  },
  decorators: [
    (Story, { args }) => (
      <Provider>
        <StyledEngineProvider injectFirst>
          <ThemeProvider theme={theme}>
            <Router>
              <CssBaseline />
              <SectionStyle view={args.view}>
                <Story />
              </SectionStyle>
            </Router>
          </ThemeProvider>
        </StyledEngineProvider>
      </Provider>
    ),
  ],
  loaders: [mswLoader(initializeMsw)],
  tags: ['autodocs'],
};

export default preview;

import type { Meta, StoryObj } from '@storybook/react-vite';
import { expect, waitFor, within } from 'storybook/test';
import { HttpResponse, http } from 'msw';
import { useEffect, useState } from 'react';
import { Provider, createStore, useAtomValue } from 'jotai';

import { NetworksSection } from './NetworksSection';
import { adaptationScenarioState, networksLayerState } from '../state/layer';
import { selectionState } from 'lib/state/interactions/interaction-state';
import { useSaveViewLayers } from 'lib/state/layers/view-layers';
import {
  protectedFeatureAdaptationsState,
  protectedFeatureLayerDataState,
} from 'lib/state/protected-features';
import {
  sectionStyleOptionsState,
  sectionStyleValueState,
  sectionVisibilityState,
  sidebarSectionExpandedState,
} from 'lib/state/sections';
import { STORAGE_PREFIX } from 'lib/state/map-view/map-url';
import type { VectorTarget } from 'lib/data-map/types';

const layerId = 'coast_nodes_cpf';
const featureId = 123;
const avoidedDamages = 1500;
const scenario = {
  hazard: 'coastal',
  parameters: { gwl: 2 },
  adaptation_name: 'Wall',
  adaptation_protection_level: 50,
};

function handlers(hasAssetScenario: boolean) {
  return [
    http.get('/api/map/raster-layers', () =>
      HttpResponse.json({ count: 0, next: null, previous: null, results: [] }),
    ),
    http.get('/api/map/feature-layers', () => HttpResponse.json({
      count: 1, next: null, previous: null,
      results: [{ id: layerId, layer_name: layerId, dataset: layerId, sector: '', subsector: '', asset_type: '',
        stacking_order: 0, display_order: 0, has_access: true }],
    })),
    http.get('/api/map/datasets', ({ request }) => {
      const isHazards = new URL(request.url).searchParams.get('group') === 'hazards';
      const results = isHazards
        ? []
        : [
            {
              id: layerId,
              label: 'Coastal protection',
              group: 'networks',
              tile_source: null,
              stacking_order: 1,
              display_order: 1,
              has_access: true,
            },
          ];
      return HttpResponse.json({ count: results.length, next: null, previous: null, results });
    }),
    http.get('/api/map/network-layer-styles', () =>
      HttpResponse.json({
        results: [
          {
            id: layerId,
            label: 'Coastal protection',
            type: 'polygon',
            color: '#333333',
            minZoom: 0,
          },
        ],
      }),
    ),
    http.get('/api/map/infrastructure-tree', () =>
      HttpResponse.json({
        count: 1,
        next: null,
        previous: null,
        results: [
          { node_id: layerId, feature_layer: layerId, node_name: 'Coastal protection', parent: null, children: [] },
        ],
      }),
    ),
    http.get('/api/map/model-scenarios/adaptation', ({ request }) => {
      const query = new URL(request.url).searchParams;
      if (query.get('protector_id') === String(featureId)) return HttpResponse.json([scenario]);
      const isDefaultAssetScope =
        query.get('sector') === 'power' &&
        query.get('subsector') === 'transmission' &&
        query.get('asset_type') === 'pole';
      return HttpResponse.json(hasAssetScenario && isDefaultAssetScope ? [scenario] : []);
    }),
    http.get(`/api/map/features/${featureId}/protected-by`, ({ request }) => {
      const parameters = JSON.parse(new URL(request.url).searchParams.get('parameters'));
      if (parameters?.gwl !== scenario.parameters.gwl) return HttpResponse.json([]);
      return HttpResponse.json([
        {
          ...scenario,
          id: featureId,
          string_id: 'coastal-region-123',
          layer: layerId,
          adaptation_cost: 100,
          avoided_ead_mean: avoidedDamages,
          avoided_eael_mean: 500,
        },
      ]);
    }),
  ];
}

function ColouringState() {
  const layers = useAtomValue(networksLayerState);
  const saveViewLayers = useSaveViewLayers();
  // DataMap saves these same production layers before looking up the values
  // used for colouring. Keep this story independent of WebGL and vector tiles.
  useEffect(() => saveViewLayers(layers), [layers, saveViewLayers]);

  const results = useAtomValue(protectedFeatureAdaptationsState);
  const layerData = useAtomValue(protectedFeatureLayerDataState);
  const { catalog } = useAtomValue(adaptationScenarioState);
  const value = layerData.get(layerId)?.[featureId];

  return (
    <dl>
      <dt>Adaptation scenarios for the asset filters</dt>
      <dd data-testid="asset-scenario-count">{catalog ? catalog.rows.length : 'Loading'}</dd>
      <dt>Results for the selected protector</dt>
      <dd data-testid="protected-result-count">{results.length}</dd>
      <dt>Protected-feature value supplied to the map</dt>
      <dd data-testid="protected-map-value">{value ?? 'Missing'}</dd>
    </dl>
  );
}

function ProtectedFeatureColouring() {
  const [store] = useState(() => {
    sessionStorage.removeItem(`${STORAGE_PREFIX}netTree`);
    const url = new URL(window.location.href);
    url.searchParams.delete('netTree');
    window.history.replaceState({}, '', url);

    const next = createStore();
    next.set(sectionVisibilityState('assets'), true);
    next.set(sidebarSectionExpandedState('assets'), true);
    next.set(sectionStyleOptionsState('assets'), [
      { id: 'protectedFeatures', label: 'Protected Features' },
    ]);
    next.set(sectionStyleValueState('assets'), 'protectedFeatures');
    next.set(selectionState('assets'), {
      interactionGroup: 'assets',
      interactionStyle: 'vector',
      viewLayer: { id: layerId, group: 'networks', fn: () => [] },
      target: { feature: { id: featureId } } as VectorTarget,
    });
    return next;
  });

  return (
    <Provider store={store}>
      <div style={{ width: 360 }}>
        <NetworksSection />
        <ColouringState />
      </div>
    </Provider>
  );
}

const meta = {
  title: 'Sidebar/Protected feature colouring',
  component: ProtectedFeatureColouring,
  parameters: {
    docs: {
      description: {
        component:
          'A coastal region can have adaptation results for its own protection. ' +
          'Coastal protection has no entry in the adaptation asset-filter registry, so the ' +
          'real network controls retain the default power/pole filters. Protector results ' +
          'must still supply map values when those unrelated filters have no scenarios.',
      },
    },
  },
} satisfies Meta<typeof ProtectedFeatureColouring>;

export default meta;
type Story = StoryObj<typeof meta>;

async function expectProtectedMapValue(canvasElement: HTMLElement, assetScenarioCount: number) {
  const canvas = within(canvasElement);
  // Sidebar configuration and scenario catalogues can finish loading after
  // the controls mount, especially during parallel browser tests.
  await waitFor(() => {
    expect(canvas.getByRole('checkbox', { name: 'Coastal protection' })).toBeChecked();
    expect(canvas.getByTestId('asset-scenario-count')).toHaveTextContent(
      String(assetScenarioCount),
    );
    expect(canvas.getByTestId('protected-result-count')).toHaveTextContent('1');
  }, { timeout: 10000 });
  await waitFor(() =>
    expect(canvas.getByTestId('protected-map-value')).toHaveTextContent(String(avoidedDamages)),
  );
}

export const WithAssetScenario: Story = {
  parameters: { msw: { handlers: handlers(true) } },
  play: async ({ canvasElement }) => expectProtectedMapValue(canvasElement, 1),
};

export const ProtectorResultsOnly: Story = {
  parameters: { msw: { handlers: handlers(false) } },
  play: async ({ canvasElement }) => expectProtectedMapValue(canvasElement, 0),
};

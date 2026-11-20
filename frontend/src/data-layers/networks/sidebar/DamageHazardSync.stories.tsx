import type { Meta, StoryObj } from '@storybook/react-vite';
import { expect, userEvent, waitFor, within } from 'storybook/test';
import { HttpResponse, http } from 'msw';
import { useEffect, useState } from 'react';
import { Provider, createStore, useAtomValue, useSetAtom } from 'jotai';

import { NetworksSection } from './NetworksSection';
import { HazardsSection } from 'data-layers/hazards/sidebar/HazardsSection';
import { hazardSelectionState } from 'data-layers/hazards/state/data-selection';
import { damageSourceState } from 'lib/state/damage-map';
import {
  sectionStyleOptionsState,
  sectionStyleValueState,
  sectionVisibilityState,
  sidebarSectionExpandedState,
} from 'lib/state/sections';
import { STORAGE_PREFIX } from 'lib/state/map-view/map-url';
import { damageScenarioCatalogState } from '../state/damage-scenarios';

const hazards = [
  { id: 'fluvial', label: 'River Flooding' },
  { id: 'coastal', label: 'Coastal Flooding' },
];
const allHazards = [...hazards, { id: 'pluvial', label: 'Surface Flooding' }];
const scenarios = [
  { rcp: 'baseline', epoch: 2010 },
  { rcp: '4.5', epoch: 2050 },
  { rcp: '8.5', epoch: 2050 },
];
const assetLayer = 'road_edges_class_a';

const datasetsHandler = (availableHazards = hazards) =>
  http.get('/api/map/datasets', ({ request }) => {
    const group = new URL(request.url).searchParams.get('group');
    const results =
      group === 'hazards'
        ? availableHazards.map((hazard, index) => ({
            ...hazard,
            group: 'hazards',
            quantity: 'depth',
            unit: 'm',
            tile_source: 1,
            stacking_order: index,
            display_order: index,
            has_access: true,
          }))
        : [
            {
              id: assetLayer,
              label: 'Class A roads',
              group: 'networks',
              quantity: 'features',
              unit: 'n/a',
              tile_source: null,
              stacking_order: 0,
              display_order: 0,
              has_access: true,
            },
          ];
    return HttpResponse.json({ count: results.length, next: null, previous: null, results });
  });

const handlers = [
  datasetsHandler(),
  http.get('/api/map/infrastructure-tree', () =>
    HttpResponse.json({
      count: 1,
      next: null,
      previous: null,
      results: [{ node_id: assetLayer, node_name: 'Class A roads', parent: null, children: [] }],
    }),
  ),
  http.get('/api/map/network-layer-styles', () =>
    HttpResponse.json({
      results: [
        {
          id: assetLayer,
          label: 'Class A roads',
          type: 'line',
          color: '#3f51b5',
          minZoom: 0,
        },
      ],
    }),
  ),
  http.get('/api/map/model-scenarios/damages_expected', ({ request }) => {
    const layers = new URL(request.url).searchParams.getAll('layer');
    return HttpResponse.json(
      layers.includes(assetLayer)
        ? hazards.flatMap(({ id }) =>
            scenarios.map((parameters) => ({
              hazard: id,
              parameters,
              protection_standard: 0,
            })),
          )
        : [],
    );
  }),
  http.get('/api/tiles/raster/sources/:datasetId/domains', ({ params }) =>
    HttpResponse.json({
      domains: scenarios.flatMap(({ rcp, epoch }) =>
        [100, 500].map((rp) => ({
          type: params.datasetId,
          rp: String(rp),
          rcp: rcp.replace('.', 'x'),
          epoch: String(epoch),
          confidence: 'None',
        })),
      ),
    }),
  ),
];

function InitialDamageSelection({ value }: { value: 'all' | string[] }) {
  const catalog = useAtomValue(damageScenarioCatalogState);
  const setSource = useSetAtom(damageSourceState);
  // Entering damage mode initializes the selection from visible rasters. Apply
  // the story's explicit selection after that effect and catalogue loading.
  useEffect(() => {
    if (catalog?.rows.length) setSource(value);
  }, [catalog, setSource, value]);
  return null;
}

function DamageAndHazardPanels({ initialHazards = 'all' }: { initialHazards?: 'all' | string[] }) {
  const [store] = useState(() => {
    // Use a known asset selection independently of the development app's URL
    // and session storage. The controls and scenario synchronisation are real.
    const url = new URL(window.location.href);
    url.searchParams.set('netTree', assetLayer);
    window.history.replaceState({}, '', url);
    sessionStorage.removeItem(`${STORAGE_PREFIX}netTree`);

    const next = createStore();
    next.set(sectionStyleOptionsState('assets'), [{ id: 'damages', label: 'Damages' }]);
    next.set(sectionStyleValueState('assets'), 'damages');
    next.set(damageSourceState, initialHazards);
    for (const id of ['assets', 'hazards']) {
      next.set(sectionVisibilityState(id), true);
      next.set(sidebarSectionExpandedState(id), true);
    }
    allHazards.forEach(({ id }) => next.set(hazardSelectionState(id), false));
    return next;
  });

  return (
    <Provider store={store}>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 16,
          maxWidth: 960,
          alignItems: 'start',
        }}
      >
        <section aria-label="Damage controls">
          <NetworksSection />
        </section>
        <section aria-label="Hazard controls">
          <HazardsSection />
        </section>
      </div>
      <InitialDamageSelection value={initialHazards} />
    </Provider>
  );
}

const meta = {
  title: 'Sidebar/Damage and hazard synchronisation',
  component: DamageAndHazardPanels,
  parameters: {
    layout: 'padded',
    msw: { handlers },
    docs: {
      description: {
        component:
          'The damage model and both flood rasters share baseline/2010 and ' +
          'RCP 4.5 or 8.5/2050 scenarios. Select a damage hazard and change its year or ' +
          'RCP to see the Hazards panel follow. Hazard controls are read-only in damage ' +
          'mode, and the raster return period is set to the largest available value (500 years). ' +
          'Selecting All Hazards activates every matching hazard raster.',
      },
    },
  },
  beforeEach: () => {
    const url = window.location.href;
    const keys = ['netTree', 'assetsStyle', 'assets', 'hazards', ...allHazards.map(({ id }) => id)];
    const saved = keys.map((key) => [
      STORAGE_PREFIX + key,
      sessionStorage.getItem(STORAGE_PREFIX + key),
    ]);
    return () => {
      window.history.replaceState({}, '', url);
      saved.forEach(([key, value]) => {
        if (value === null) sessionStorage.removeItem(key);
        else sessionStorage.setItem(key, value);
      });
    };
  },
} satisfies Meta<typeof DamageAndHazardPanels>;

export default meta;
type Story = StoryObj<typeof meta>;

export const CompatibleScenarios: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const damagePanel = within(canvas.getByRole('region', { name: 'Damage controls' }));
    const hazardPanel = within(canvas.getByRole('region', { name: 'Hazard controls' }));
    const river = await hazardPanel.findByRole('button', { name: 'River Flooding' });
    const coastal = await hazardPanel.findByRole('button', { name: 'Coastal Flooding' });
    const riverControls = within(river.closest('.MuiAccordion-root') as HTMLElement);
    const coastalControls = within(coastal.closest('.MuiAccordion-root') as HTMLElement);
    const body = within(canvasElement.ownerDocument.body);

    await userEvent.click(await damagePanel.findByRole('radio', { name: 'River Flooding' }));
    // The hazard headers can render before the asynchronously loaded sidebar
    // configuration supplies their parameter controls.
    await riverControls.findByRole('combobox', { name: 'Epoch' }, { timeout: 10000 });
    await waitFor(() => {
      expect(river).toHaveAttribute('aria-expanded', 'true');
      expect(coastal).toHaveAttribute('aria-expanded', 'false');
      expect(riverControls.getByRole('combobox', { name: 'Epoch' })).toHaveTextContent('Present');
      expect(riverControls.getByRole('combobox', { name: 'RCP' })).toHaveTextContent('Baseline');
      expect(riverControls.getByRole('slider', { name: 'Return Period' })).toHaveAttribute(
        'aria-valuetext',
        '500',
      );
    });
    expect(river).toBeDisabled();
    expect(riverControls.getByRole('combobox', { name: 'Epoch' })).toHaveAttribute(
      'aria-disabled',
      'true',
    );
    expect(riverControls.getByRole('combobox', { name: 'RCP' })).toHaveAttribute(
      'aria-disabled',
      'true',
    );
    expect(riverControls.getByRole('slider', { name: 'Return Period' })).toBeDisabled();

    const year = damagePanel.getByRole('slider', { name: 'Year' });
    year.focus();
    await userEvent.keyboard('{End}');
    await waitFor(() => {
      expect(riverControls.getByRole('combobox', { name: 'Epoch' })).toHaveTextContent('2050');
      expect(riverControls.getByRole('combobox', { name: 'RCP' })).toHaveTextContent('4.5');
    });
    await userEvent.click(damagePanel.getByRole('combobox', { name: 'RCP' }));
    await userEvent.click(await body.findByRole('option', { name: '8.5' }));
    await waitFor(() =>
      expect(riverControls.getByRole('combobox', { name: 'RCP' })).toHaveTextContent('8.5'),
    );

    await userEvent.click(damagePanel.getByRole('radio', { name: 'Coastal Flooding' }));
    await waitFor(() => {
      expect(river).toHaveAttribute('aria-expanded', 'false');
      expect(coastal).toHaveAttribute('aria-expanded', 'true');
      expect(coastalControls.getByRole('combobox', { name: 'Epoch' })).toHaveTextContent('2050');
      expect(coastalControls.getByRole('combobox', { name: 'RCP' })).toHaveTextContent('8.5');
    });

    await userEvent.click(damagePanel.getByRole('radio', { name: 'All Hazards' }));
    await waitFor(() => {
      expect(river).toHaveAttribute('aria-expanded', 'true');
      expect(coastal).toHaveAttribute('aria-expanded', 'true');
      expect(riverControls.getByRole('combobox', { name: 'RCP' })).toHaveTextContent('8.5');
      expect(coastalControls.getByRole('combobox', { name: 'RCP' })).toHaveTextContent('8.5');
    });
    // Leave an individual hazard open for visual inspection in Storybook.
    await userEvent.click(damagePanel.getByRole('radio', { name: 'River Flooding' }));
    await waitFor(() => expect(river).toHaveAttribute('aria-expanded', 'true'));
  },
};

export const AllHazardParameters: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'All Hazards combines coastal SLR with river GWL. Both controls select exact per-hazard scenarios for damage totals and activate their matching rasters.',
      },
    },
    msw: {
      handlers: [
        http.get('/api/map/model-scenarios/damages_expected', () =>
          HttpResponse.json([
            ...[0, 20].flatMap((SLR) =>
              [0, 100].map((protection_standard) => ({
                hazard: 'coastal',
                parameters: { SLR },
                protection_standard,
              })),
            ),
            ...[2, 3].flatMap((GWL) =>
              [0, 100].map((protection_standard) => ({
                hazard: 'fluvial',
                parameters: { GWL },
                protection_standard,
              })),
            ),
          ]),
        ),
        http.get('/api/tiles/raster/sources/:datasetId/domains', ({ params }) =>
          HttpResponse.json({
            domains: (params.datasetId === 'coastal'
              ? [{ SLR: '0' }, { SLR: '20' }]
              : [{ GWL: '2' }, { GWL: '3' }]
            ).flatMap((parameters) =>
              [100, 500].map((rp) => ({
                type: params.datasetId,
                ...parameters,
                rp: String(rp),
                confidence: 'None',
              })),
            ),
          }),
        ),
        ...handlers.filter(
          (handler) =>
            !handler.info.path.toString().includes('model-scenarios') &&
            !handler.info.path.toString().includes('/domains'),
        ),
      ],
    },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const damagePanel = within(canvas.getByRole('region', { name: 'Damage controls' }));
    const hazardPanel = within(canvas.getByRole('region', { name: 'Hazard controls' }));
    const gwl = await damagePanel.findByRole('slider', { name: 'GWL' }, { timeout: 10000 });
    const rp = await damagePanel.findByRole('slider', { name: 'Return period (years)' });
    expect(rp).toBeDisabled();
    expect(rp).toHaveAttribute('aria-valuetext', '500');
    expect(damagePanel.getByRole('radio', { name: 'All Hazards' })).toBeChecked();
    const slr = damagePanel.getByRole('slider', { name: 'SLR' });
    expect(slr).toHaveAttribute('aria-valuetext', '0');
    const river = await hazardPanel.findByRole('button', { name: 'River Flooding' });
    const coastal = await hazardPanel.findByRole('button', { name: 'Coastal Flooding' });
    const riverControls = within(river.closest('.MuiAccordion-root') as HTMLElement);
    const coastalControls = within(coastal.closest('.MuiAccordion-root') as HTMLElement);
    await riverControls.findAllByRole('slider', {}, { timeout: 10000 });
    slr.focus();
    await userEvent.keyboard('{End}');
    gwl.focus();
    await userEvent.keyboard('{End}');
    expect(gwl).toHaveAttribute('aria-valuetext', '3');
    expect(slr).toHaveAttribute('aria-valuetext', '20');
    const protection = damagePanel.getByRole('slider', { name: 'Protection standard' });
    protection.focus();
    await userEvent.keyboard('{End}');
    expect(protection).toHaveAttribute('aria-valuetext', '100');
    await waitFor(() => {
      expect(river).toHaveAttribute('aria-expanded', 'true');
      expect(coastal).toHaveAttribute('aria-expanded', 'true');
      expect(
        riverControls.getAllByRole('slider').map((slider) => slider.getAttribute('aria-valuetext')),
      ).toEqual(expect.arrayContaining(['500', '3']));
      expect(
        coastalControls
          .getAllByRole('slider')
          .map((slider) => slider.getAttribute('aria-valuetext')),
      ).toEqual(expect.arrayContaining(['500', '20']));
    });
    riverControls.getAllByRole('slider').forEach((slider) => expect(slider).toBeDisabled());
    coastalControls.getAllByRole('slider').forEach((slider) => expect(slider).toBeDisabled());
    await userEvent.click(damagePanel.getByRole('radio', { name: 'Coastal Flooding' }));
    await waitFor(() => {
      expect(damagePanel.queryByRole('slider', { name: 'GWL' })).not.toBeInTheDocument();
      expect(damagePanel.getByRole('slider', { name: 'SLR' })).toHaveAttribute(
        'aria-valuetext',
        '20',
      );
      expect(river).toHaveAttribute('aria-expanded', 'false');
      expect(hazardPanel.getByRole('button', { name: 'Coastal Flooding' })).toHaveAttribute(
        'aria-expanded',
        'true',
      );
    });
    await userEvent.click(damagePanel.getByRole('radio', { name: 'All Hazards' }));
    await damagePanel.findByRole('slider', { name: 'GWL' });
    await waitFor(() => {
      expect(river).toHaveAttribute('aria-expanded', 'true');
      expect(coastal).toHaveAttribute('aria-expanded', 'true');
    });
  },
};

export const SelectedHazards: Story = {
  args: { initialHazards: ['fluvial', 'pluvial'] },
  parameters: {
    docs: {
      description: {
        story:
          'A partial selection supplied through state still totals river and surface damages and synchronises their rasters. The radio group can replace this with one hazard or All Hazards.',
      },
    },
    msw: {
      handlers: [
        datasetsHandler(allHazards),
        http.get('/api/map/model-scenarios/damages_expected', () =>
          HttpResponse.json([
            ...[0, 20].map((SLR) => ({
              hazard: 'coastal',
              parameters: { SLR },
              protection_standard: 0,
            })),
            ...['fluvial', 'pluvial'].flatMap((hazard) =>
              [2, 3].map((GWL) => ({ hazard, parameters: { GWL }, protection_standard: 0 })),
            ),
          ]),
        ),
        ...AllHazardParameters.parameters.msw.handlers.filter(
          (handler) =>
            !['/api/map/datasets', '/api/map/model-scenarios/damages_expected'].includes(
              String(handler.info.path),
            ),
        ),
      ],
    },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const damagePanel = within(canvas.getByRole('region', { name: 'Damage controls' }));
    const hazardPanel = within(canvas.getByRole('region', { name: 'Hazard controls' }));
    const group = await damagePanel.findByRole('radiogroup', { name: 'Hazard' });
    const coastal = await within(group).findByRole('radio', { name: 'Coastal Flooding' });
    const all = within(group).getByRole('radio', { name: 'All Hazards' });
    const river = within(group).getByRole('radio', { name: 'River Flooding' });
    await waitFor(() =>
      expect(within(group).queryByRole('radio', { checked: true })).not.toBeInTheDocument(),
    );
    expect(damagePanel.queryByRole('slider', { name: 'SLR' })).not.toBeInTheDocument();
    const gwl = await damagePanel.findByRole('slider', { name: 'GWL' });
    gwl.focus();
    await userEvent.keyboard('{End}');
    await waitFor(() => {
      expect(hazardPanel.getByRole('button', { name: 'Coastal Flooding' })).toHaveAttribute(
        'aria-expanded',
        'false',
      );
      expect(hazardPanel.getByRole('button', { name: 'River Flooding' })).toHaveAttribute(
        'aria-expanded',
        'true',
      );
      expect(hazardPanel.getByRole('button', { name: 'Surface Flooding' })).toHaveAttribute(
        'aria-expanded',
        'true',
      );
    });
    await userEvent.click(coastal);
    expect(coastal).toBeChecked();
    expect(river).not.toBeChecked();
    await damagePanel.findByRole('slider', { name: 'SLR' });
    expect(damagePanel.queryByRole('slider', { name: 'GWL' })).not.toBeInTheDocument();
    await waitFor(() => {
      expect(hazardPanel.getByRole('button', { name: 'Coastal Flooding' })).toHaveAttribute(
        'aria-expanded',
        'true',
      );
      expect(hazardPanel.getByRole('button', { name: 'River Flooding' })).toHaveAttribute(
        'aria-expanded',
        'false',
      );
      expect(hazardPanel.getByRole('button', { name: 'Surface Flooding' })).toHaveAttribute(
        'aria-expanded',
        'false',
      );
    });
    await userEvent.click(all);
    expect(all).toBeChecked();
    expect(coastal).not.toBeChecked();
    expect(river).not.toBeChecked();
    await damagePanel.findByRole('slider', { name: 'GWL' });
    await waitFor(() => {
      for (const { label } of allHazards) {
        expect(hazardPanel.getByRole('button', { name: label })).toHaveAttribute(
          'aria-expanded',
          'true',
        );
      }
    });
    await userEvent.click(all);
    expect(all).toBeChecked();
    expect(within(group).getAllByRole('radio', { checked: true })).toHaveLength(1);
  },
};

export const DifferentReturnPeriods: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'Read-only return periods show the maximum available for each matching raster. Coastal flooding uses 1,500 years; river flooding uses 100 years at GWL 2 and 500 years at GWL 3. These describe the hazard maps; damage values remain expected annual estimates.',
      },
    },
    msw: {
      handlers: [
        http.get('/api/tiles/raster/sources/:datasetId/domains', ({ params }) =>
          HttpResponse.json({
            domains:
              params.datasetId === 'coastal'
                ? [0, 20].flatMap((SLR) =>
                    [100, 1500].map((rp) => ({
                      type: params.datasetId,
                      SLR: String(SLR),
                      rp: String(rp),
                      confidence: 'None',
                    })),
                  )
                : [2, 3].flatMap((GWL) =>
                    (GWL === 2 ? [20, 100] : [100, 500]).map((rp) => ({
                      type: params.datasetId,
                      GWL: String(GWL),
                      rp: String(rp),
                      confidence: 'None',
                    })),
                  ),
          }),
        ),
        ...AllHazardParameters.parameters.msw.handlers.filter(
          (handler) => !String(handler.info.path).includes('/domains'),
        ),
      ],
    },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const damagePanel = within(canvas.getByRole('region', { name: 'Damage controls' }));
    const hazardPanel = within(canvas.getByRole('region', { name: 'Hazard controls' }));
    const coastalRP = await damagePanel.findByRole(
      'slider',
      {
        name: 'Coastal Flooding return period (years)',
      },
      { timeout: 10000 },
    );
    const riverRP = damagePanel.getByRole('slider', {
      name: 'River Flooding return period (years)',
    });
    expect(coastalRP).toBeDisabled();
    expect(riverRP).toBeDisabled();
    expect(coastalRP).toHaveAttribute('aria-valuetext', '1500');
    expect(riverRP).toHaveAttribute('aria-valuetext', '100');
    const river = await hazardPanel.findByRole('button', { name: 'River Flooding' });
    const riverControls = within(river.closest('.MuiAccordion-root') as HTMLElement);
    await waitFor(() =>
      expect(riverControls.getByRole('slider', { name: 'Return Period' })).toHaveAttribute(
        'aria-valuetext',
        '100',
      ),
    );

    damagePanel.getByRole('slider', { name: 'GWL' }).focus();
    await userEvent.keyboard('{End}');
    await waitFor(() => {
      expect(
        damagePanel.getByRole('slider', { name: 'River Flooding return period (years)' }),
      ).toHaveAttribute('aria-valuetext', '500');
      expect(riverControls.getByRole('slider', { name: 'Return Period' })).toHaveAttribute(
        'aria-valuetext',
        '500',
      );
    });
    expect(
      damagePanel.getByRole('slider', { name: 'Coastal Flooding return period (years)' }),
    ).toHaveAttribute('aria-valuetext', '1500');
  },
};

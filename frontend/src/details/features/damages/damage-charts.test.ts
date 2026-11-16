import { describe, expect, it } from 'vitest';
import { compile, TopLevelSpec } from 'vega-lite';
import { parse, View } from 'vega';
import { makeExpectedDamageSpec } from './ExpectedDamageChart';
import { makeReturnPeriodDamageSpec } from './ReturnPeriodDamageChart';
import { expectedDamageDimensions, parameterField, parameterOptions, parameterSelectionKey, returnPeriodDimensions } from './chart-parameters';
import { expectedDamageRows, extraParameters, gwlSlrParameters, rcpYearParameters } from './damage-story-fixtures';

async function render(spec: object, values: object[], inspect?: (view: View) => void) {
  const view = new View(parse(compile({ ...spec, data: { values } } as TopLevelSpec).spec), {
    renderer: 'none',
  });
  try {
    const svg = await view.toSVG();
    inspect?.(view);
    return svg;
  } finally {
    view.finalize();
  }
}

describe('parameter chart labels', () => {
  it.each([
    ['ead_mean', 'ead_amin', 'ead_amax', 'EAD (J$)'],
    ['eael_mean', 'eael_amin', 'eael_amax', 'EAEL (J$/day)'],
  ])('renders %s bounds without dropping means when a bound is missing', async (mean, min, max, title) => {
    const rows = [
      { parameters: { gwl: 0 }, [mean]: 10, [min]: 6, [max]: 45 },
      { parameters: { gwl: 2 }, [mean]: 20, [min]: null, [max]: 24 },
      { parameters: { gwl: 4 }, [mean]: 30, [min]: 25, [max]: null },
    ];
    const spec = makeExpectedDamageSpec(
      mean, title, 280, 170, parameterField('gwl'), 'GWL',
      [parameterField('gwl')], undefined, null, min, max,
    );
    const svg = await render(spec, rows, (view) => {
      const domain = view.scale('y').domain();
      expect(domain[0]).toBeLessThanOrEqual(6);
      expect(domain[domain.length - 1]).toBeGreaterThanOrEqual(45);
    });
    expect(svg.match(/aria-roledescription="errorbar"/g)).toHaveLength(1);
    expect(svg.match(/aria-roledescription="point"/g)).toHaveLength(3);
    expect(svg).toContain(`${title} (amin)`);
    expect(svg).toContain(`${title} (amax)`);
  });

  it('keeps the original Year axis, RCP series, colours and symbols with nested parameters', async () => {
    const rows = expectedDamageRows(rcpYearParameters);
    const { x, series, selectors } = expectedDamageDimensions(rows);
    expect({ x, series, selectors }).toEqual({ x: 'epoch', series: 'rcp', selectors: [] });
    const spec = makeExpectedDamageSpec(
      'ead_mean', 'EAD (J$)', 280, 170,
      parameterField(x), 'Year', [parameterField(x), parameterField(series)],
      parameterField(series), 'RCP',
    );
    const svg = await render(spec, rows);
    expect(svg).toContain('>Year</text>');
    expect(svg).toContain('>RCP</text>');
    expect(svg).toContain('#8b8b8b');
    expect(svg).toContain('#003466');
    expect(svg).toContain('#709fcc');
    expect(svg).toContain('#980002');
    expect(spec.layer[spec.layer.length - 1].encoding).toMatchObject({
      shape: { scale: { range: ['circle', 'square', 'triangle-up', 'diamond'] } },
    });
    expect(returnPeriodDimensions(rows)).toEqual({ series: 'rcp', selectors: ['epoch'] });
    expect(parameterOptions(rows, ['epoch']).map((option) => option.label)).toEqual(['2010', '2050', '2080']);
  });

  it('assigns GWL and SLR to separate dimensions instead of flattening scenarios', () => {
    const rows = expectedDamageRows(gwlSlrParameters);
    expect(expectedDamageDimensions(rows)).toEqual({ x: 'gwl', series: 'slr', selectors: [] });
    expect(returnPeriodDimensions(rows)).toEqual({ series: 'gwl', selectors: ['slr'] });
  });

  it('filters extra dimensions without removing any series at the selected value', () => {
    const rows = expectedDamageRows(extraParameters);
    const { x, series, selectors } = expectedDamageDimensions(rows);
    expect({ x, series, selectors }).toEqual({ x: 'epoch', series: 'rcp', selectors: ['slr'] });
    const options = parameterOptions(rows, selectors);
    const selected = rows.filter((row) => parameterSelectionKey(row, selectors) === options[0].key);
    expect(selected).toHaveLength(rcpYearParameters.length);
    expect(new Set(selected.map((row) => row.parameters.rcp)).size).toBe(4);
  });

  it('plots expected damages by year with separate GWL series', async () => {
    const spec = makeExpectedDamageSpec(
      'damage', 'Damage', 280, 170, 'epoch', 'Year', ['epoch', 'gwl'], 'gwl',
    );
    const svg = await render(spec, [
      { epoch: 2030, gwl: 0, damage: 10 },
      { epoch: 2050, gwl: 0, damage: 20 },
      { epoch: 2030, gwl: 2, damage: 30 },
      { epoch: 2050, gwl: 2, damage: 40 },
    ]);
    expect(svg).toContain('>Year</text>');
    expect(svg).toContain('>GWL</text>');
    expect(svg.match(/aria-roledescription="line mark"/g)).toHaveLength(2);
  });

  it('supports an unfamiliar parameter and a caller-supplied title', async () => {
    const spec = makeExpectedDamageSpec(
      'damage', 'Damage', 280, 170, 'discount_rate', 'Discount rate (%)',
    );
    const svg = await render(spec, [
      { discount_rate: 2, damage: 20 },
      { discount_rate: 5, damage: 10 },
    ]);
    expect(svg).toContain('>Discount rate (%)</text>');
    expect(spec.encoding).not.toHaveProperty('color');
  });

  it('uses the actual return-period series field for its legend', async () => {
    const spec = makeReturnPeriodDamageSpec('depth', 'Depth (m)', 280, 170, ['gwl', 'rp'], 'gwl');
    const svg = await render(spec, [
      { probability: 0.2, depth: 0.1, gwl: 0, rp: 5 },
      { probability: 0.05, depth: 0.45, gwl: 0, rp: 20 },
      { probability: 0.2, depth: 0.2, gwl: 2, rp: 5 },
      { probability: 0.05, depth: 0.7, gwl: 2, rp: 20 },
    ]);
    expect(svg).toContain('>GWL</text>');
    expect(svg.match(/aria-roledescription="line mark"/g)).toHaveLength(2);
  });

  it('allows custom return-period series titles and an ungrouped chart', async () => {
    const spec = makeReturnPeriodDamageSpec(
      'depth', 'Depth', 280, 170, ['pathway'], 'pathway', 'Emissions pathway',
    );
    const svg = await render(spec, [{ probability: 0.2, depth: 0.1, pathway: 'low' }]);
    expect(svg).toContain('>Emissions pathway</text>');
    expect(makeReturnPeriodDamageSpec('depth', 'Depth', 280, 170, ['rp']).encoding)
      .not.toHaveProperty('color');
  });
});

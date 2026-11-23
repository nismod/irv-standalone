import type { DamagesExpected, DamagesRp } from 'lib/api-client';

export const rcpYearParameters = [
  { rcp: 'baseline', epoch: 2010 },
  { rcp: '2.6', epoch: 2050 },
  { rcp: '2.6', epoch: 2080 },
  { rcp: '4.5', epoch: 2050 },
  { rcp: '4.5', epoch: 2080 },
  { rcp: '8.5', epoch: 2050 },
  { rcp: '8.5', epoch: 2080 },
];

export const gwlSlrParameters = [0, 0.5].flatMap((slr) => [0, 2, 4].map((gwl) => ({ gwl, slr })));

export const singleParameters = [0, 1.5, 2, 3].map((gwl) => ({ gwl }));

export const extraParameters = [0, 0.5].flatMap((slr) =>
  rcpYearParameters.map((parameters) => ({ ...parameters, slr })),
);

export function expectedDamageRows(scenarios: Record<string, unknown>[]) {
  return scenarios.map(
    (parameters, index) =>
      ({
        id: index + 1,
        key: `expected-${index}`,
        feature: 1,
        hazard: 'fluvial',
        parameters,
        protection_standard: 0,
        ead_mean: 1_130_000 + index * 5_000,
        ead_amin: 900_000 + index * 4_000,
        ead_amax: 1_300_000 + index * 6_000,
        eael_mean: 20_000 + index * 1_000,
        eael_amin: 15_000 + index * 800,
        eael_amax: 25_000 + index * 1_200,
      }) satisfies DamagesExpected & { key: string },
  );
}

export function returnPeriodDamageRows(scenarios: Record<string, unknown>[]) {
  return scenarios.flatMap((parameters, scenarioIndex) =>
    [5, 20, 100].map((rp, rpIndex) => {
      const damage = (scenarioIndex + 1) * rp * 10_000;
      return {
        id: scenarioIndex * 3 + rpIndex + 1,
        key: `rp-${scenarioIndex}-${rp}`,
        feature: 1,
        hazard: 'fluvial',
        parameters,
        rp,
        probability: 1 / rp,
        damage_mean: damage,
        damage_amin: damage * 0.8,
        damage_amax: damage * 1.2,
        loss_mean: damage * 0.01,
        loss_amin: damage * 0.008,
        loss_amax: damage * 0.012,
      } satisfies DamagesRp & { key: string; probability: number };
    }),
  );
}

import { atom } from 'jotai';
import { unwrap } from 'jotai/utils';

async function fetchRiskDomains() {
  //TODO: move this into the Django app.
  const module = await import('app/config/sidebar/RISK_DOMAINS');
  return module.RISK_DOMAINS;
}

export const riskDomainState = unwrap(
  atom(fetchRiskDomains),
  prev => prev || null,
);

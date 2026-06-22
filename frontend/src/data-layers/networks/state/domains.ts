import { atom } from 'jotai';
import { unwrap } from 'jotai/utils';

async function fetchNetworkDomains() {
  //TODO: move this into the Django app.
  const module = await import('app/config/sidebar/NETWORK_DOMAINS');
  return module.NETWORK_DOMAINS;
}

export const networkDomainState = unwrap(
  atom(fetchNetworkDomains),
  prev => prev || null,
);

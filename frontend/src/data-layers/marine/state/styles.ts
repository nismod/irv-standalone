import { makeConfig } from 'lib/helpers';
import { atom } from 'jotai';

const fetchStylesConfig = async () => {
  const module = await import('./styles.json');
  return module.default;
};

const stylesQuery = atom(fetchStylesConfig);

export const stylesConfig = atom(async (get) => {
  const styles = await get(stylesQuery);
  return makeConfig(styles);
});

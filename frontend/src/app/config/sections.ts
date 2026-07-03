import { Atom, Getter, atom } from 'jotai';
import { unwrap } from 'jotai/utils';

import { StyleSelectionOption } from 'lib/state/sections';

export type SectionConfig = { styles?: Record<string, StyleSelectionOption> };
export type SectionsConfig = Record<string, SectionConfig>;
type StylesConfig = Record<string, StyleSelectionOption>;
type StylesModule = { stylesConfig: Atom<Promise<StylesConfig>> };

const layerStylesModules = import.meta.glob('../../data-layers/*/state/styles.ts');

async function loadLayerStylesConfig(layerName: string, get: Getter) {
  const loadModule = layerStylesModules[`../../data-layers/${layerName}/state/styles.ts`];
  if (!loadModule) {
    console.warn(`No styles module found for layer "${layerName}"`);
    return {};
  }

  const module = await loadModule() as StylesModule;
  const stylesConfig = await get(module.stylesConfig);
  return stylesConfig;
}

async function loadSectionConfig(sectionName: string, get: Getter) {
  const sectionConfig: SectionConfig = {};
  try {
    sectionConfig.styles = await loadLayerStylesConfig(sectionName, get);
  } catch (error) {
    console.warn(`Failed to load styles for section "${sectionName}":`, error);
  }
  return sectionConfig;
}

async function buildSectionsConfig(get: Getter) {
  const sectionsConfig: SectionsConfig = {
    assets: await loadSectionConfig('networks', get),
    drought: await loadSectionConfig('droughtRisks', get),
    hazards: await loadSectionConfig('hazards', get),
    risks: await loadSectionConfig('risks', get),
    buildings: await loadSectionConfig('buildings', get),
    regions: await loadSectionConfig('regions', get),
    terrestrial: await loadSectionConfig('terrestrial', get),
    marine: await loadSectionConfig('marine', get),
  };

  return sectionsConfig;
}

const sectionsConfigQuery = atom(async (get) => buildSectionsConfig(get));

export const sectionsConfigState = unwrap(
  sectionsConfigQuery,
  (prev) => prev ?? {},
);

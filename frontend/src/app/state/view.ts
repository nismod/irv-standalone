import difference from 'lodash/difference';
import forEach from 'lodash/forEach';
import keys from 'lodash/keys';
import { atom } from 'jotai';

import { StateEffect } from 'lib/recoil/state-effects/types';
import {
  sectionStyleOptionsState,
  sectionStyleValueState,
  sectionVisibilityState,
  sidebarSectionExpandedState,
} from 'lib/state/sections';

import { SECTIONS_CONFIG } from 'app/config/sections';
import { ViewSectionConfig, ViewSectionsConfig, viewSectionsState } from 'app/config/views';

type SectionKey = string;

// Initialised from the current pathname so the first render has the correct
// value synchronously.  MapPage keeps it in sync via useSyncRecoilState.
export const viewState = atom<string>(window.location.pathname.split('/').find(Boolean) ?? '');

type ViewStateEffectValue = {
  view: string;
  viewSections: ViewSectionsConfig;
};

export const viewStateEffectState = atom<ViewStateEffectValue>((get) => ({
  view: get(viewState),
  viewSections: get(viewSectionsState) ?? {},
}));

function sectionVisibility(section: SectionKey, sectionConfig: ViewSectionConfig) {
  if (section === 'assets') {
    return sectionConfig.visible;
  } else {
    const searchParams = new URLSearchParams(window.location.search);
    return searchParams.has(section) ? searchParams.get(section) === 'true' : sectionConfig.visible;
  }
}

function sectionStyle(section: SectionKey, sectionConfig: ViewSectionConfig) {
  const styleParam = `${section}Style`;
  if (styleParam === 'assetsStyle') {
    return sectionConfig.defaultStyle;
  } else {
    const searchParams = new URLSearchParams(window.location.search);
    return searchParams.has(styleParam)
      ? searchParams.get(styleParam).replaceAll('"', '')
      : sectionConfig.defaultStyle;
  }
}

export const viewStateEffect: StateEffect<ViewStateEffectValue> = (
  { set },
  { view, viewSections } = { view: '', viewSections: {} },
  previousValue,
) => {
  const currentViewSections = viewSections ?? {};
  const previousView = previousValue?.view;
  const previousViewSections = previousValue?.viewSections ?? {};
  const viewSectionsConfig = currentViewSections[view] ?? {};
  const previousViewSectionsConfig = previousViewSections[previousView] ?? {};

  const removedSections = difference(keys(previousViewSectionsConfig), keys(viewSectionsConfig));

  removedSections.forEach((section: SectionKey) => {
    set(sectionVisibilityState(section), false);
  });

  forEach(viewSectionsConfig, (sectionConfig: ViewSectionConfig, section: SectionKey) => {
    set(sectionVisibilityState(section), sectionVisibility(section, sectionConfig));
    set(sidebarSectionExpandedState(section), sectionConfig.expanded);
    const styleOptions = sectionConfig.styles?.map(
      (style) => SECTIONS_CONFIG[section].styles[style],
    );
    set(sectionStyleOptionsState(section), styleOptions);
    set(sectionStyleValueState(section), sectionStyle(section, sectionConfig));
  });
};

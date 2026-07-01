import { atom } from 'jotai';
import { unwrap } from 'jotai/utils';

export interface ViewSectionConfig {
  expanded: boolean;
  visible: boolean;
  styles?: string[];
  defaultStyle?: string;
}

export type ViewSectionsConfig = Record<string, Record<string, ViewSectionConfig>>;

async function fetchViewSectionsConfig() {
  const module = await import('./view-sections.json');
  return module.default as ViewSectionsConfig;
}

const viewSectionsQuery = atom(fetchViewSectionsConfig);

export const viewSectionsState = unwrap(
  viewSectionsQuery,
  (prev) => prev ?? {},
);

import { atom } from 'jotai';
import { unwrap } from 'jotai/utils';

async function fetchPageContent(): Promise<IntroPageContent> {
  const module = await import('./intro.json');
  return module.default as IntroPageContent;
}
const pageContentQuery = atom(fetchPageContent);
export const pageContentState = unwrap(pageContentQuery, (prev) => prev ?? emptyPageContent);

export interface Logo {
  href: string;
  src: string;
  alt: string;
  height: number;
}

export interface IntroPageContent {
  title: string;
  summary: {
    markdown: string;
  };
  collaboration: {
    markdown: string;
    logos: Logo[];
  };
  funding: {
    markdown: string;
    logos: Logo[];
  };
  backgroundImage: {
    src: string;
    credit: string;
  };
}

export const emptyPageContent: IntroPageContent = {
  title: '',
  summary: {
    markdown: '',
  },
  collaboration: {
    markdown: '',
    logos: [],
  },
  funding: {
    markdown: '',
    logos: [],
  },
  backgroundImage: {
    src: '',
    credit: '',
  },
};

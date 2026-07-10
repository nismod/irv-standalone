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
  summary: string;
  sectors: Array<{
    title: string;
    description: string;
  }>;
  collaboration: {
    markdown: string;
    logos: Logo[];
  };
  funding: {
    title: string;
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
  summary: '',
  sectors: [],
  collaboration: {
    markdown: '',
    logos: [],
  },
  funding: {
    title: '',
    markdown: '',
    logos: [],
  },
  backgroundImage: {
    src: '',
    credit: '',
  },
};

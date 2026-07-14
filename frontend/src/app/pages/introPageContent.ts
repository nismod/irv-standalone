import { atom } from 'jotai';
import { unwrap } from 'jotai/utils';

import { contentList, type MarkdownBlock } from 'lib/api-client';

interface IntroPageStaticContent {
  title: string;
  collaboration: {
    logos: Logo[];
  };
  funding: {
    logos: Logo[];
  };
  backgroundImage: {
    src: string;
  };
}

async function fetchPageContent(): Promise<IntroPageContent> {
  const [module, { data: blocks, error }] = await Promise.all([
    import('./intro.json'),
    contentList({
      baseUrl: '/api',
      path: { page: 'intro' },
    }),
  ]);

  if (error) {
    throw new Error(`Failed to load intro page content: ${JSON.stringify(error)}`);
  }

  const staticContent = module.default as IntroPageStaticContent;
  const markdownBySlot = new Map(
    (blocks ?? []).map(({ slot, markdown }: MarkdownBlock) => [slot, markdown]),
  );

  return {
    ...staticContent,
    summary: {
      markdown: markdownBySlot.get('summary') ?? '',
    },
    collaboration: {
      ...staticContent.collaboration,
      markdown: markdownBySlot.get('collaboration') ?? '',
    },
    funding: {
      ...staticContent.funding,
      markdown: markdownBySlot.get('funding') ?? '',
    },
    backgroundImage: {
      ...staticContent.backgroundImage,
      credit: markdownBySlot.get('background-credit') ?? '',
    },
  };
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

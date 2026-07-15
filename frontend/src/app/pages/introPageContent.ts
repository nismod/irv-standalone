import { atom } from 'jotai';
import { unwrap } from 'jotai/utils';

import {
  contentList,
  contentLogosList,
  contentMetadataRetrieve,
  type Logo as ApiLogo,
  type MarkdownBlock,
} from 'lib/api-client';

async function fetchPageContent(): Promise<IntroPageContent> {
  const [
    { data: page, error: pageError },
    { data: blocks, error: blocksError },
    { data: logos, error: logosError },
  ] = await Promise.all([
    contentMetadataRetrieve({
      baseUrl: '/api',
      path: { page: 'intro' },
    }),
    contentList({
      baseUrl: '/api',
      path: { page: 'intro' },
    }),
    contentLogosList({
      baseUrl: '/api',
      path: { page: 'intro' },
    }),
  ]);

  if (pageError || blocksError || logosError) {
    throw new Error(
      `Failed to load intro page content: ${JSON.stringify(
        pageError ?? blocksError ?? logosError,
      )}`,
    );
  }

  const markdownBySlot = new Map(
    (blocks ?? []).map(({ slot, markdown }: MarkdownBlock) => [slot, markdown]),
  );
  const logosBySlot = new Map<string, Logo[]>();
  for (const logo of logos ?? []) {
    const slotLogos = logosBySlot.get(logo.slot);
    if (slotLogos) {
      slotLogos.push(logo);
    } else {
      logosBySlot.set(logo.slot, [logo]);
    }
  }

  return {
    title: page?.title ?? '',
    summary: {
      markdown: markdownBySlot.get('summary') ?? '',
    },
    collaboration: {
      markdown: markdownBySlot.get('collaboration') ?? '',
      logos: logosBySlot.get('collaboration') ?? [],
    },
    funding: {
      markdown: markdownBySlot.get('funding') ?? '',
      logos: logosBySlot.get('funding') ?? [],
    },
    backgroundImage: {
      src: page?.background_image ?? '',
      credit: page?.background_credit ?? '',
    },
  };
}
const pageContentQuery = atom(fetchPageContent);
export const pageContentState = unwrap(pageContentQuery, (prev) => prev ?? emptyPageContent);

export type Logo = ApiLogo;

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

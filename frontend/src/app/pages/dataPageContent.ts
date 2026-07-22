import { atom } from 'jotai';
import { unwrap } from 'jotai/utils';

import { contentList, type MarkdownBlock } from 'lib/api-client';

async function fetchPageContent(): Promise<DataPageContent> {
  const [{ default: defaultPageContent }, { data: blocks, error }] = await Promise.all([
    import('./dataPageContent.json'),
    contentList({
      baseUrl: '/api',
      path: { page: 'data' },
    }),
  ]);

  if (error) {
    throw new Error(`Failed to load data page content: ${JSON.stringify(error)}`);
  }

  const markdownBySlot = new Map(
    (blocks ?? []).map(({ slot, markdown }: MarkdownBlock) => [slot, markdown]),
  );

  return {
    accessNotice: {
      markdown: markdownBySlot.get('access_notice') ?? defaultPageContent.accessNotice.markdown,
    },
    releaseNotice: {
      markdown: markdownBySlot.get('release_notice') ?? defaultPageContent.releaseNotice.markdown,
    },
    content: {
      markdown: markdownBySlot.get('content') ?? defaultPageContent.content.markdown,
    },
  };
}

const pageContentQuery = atom(fetchPageContent);
export const pageContentState = unwrap(pageContentQuery, (prev) => prev ?? emptyPageContent);

export interface DataPageContent {
  accessNotice: {
    markdown: string;
  };
  releaseNotice: {
    markdown: string;
  };
  content: {
    markdown: string;
  };
}

export const emptyPageContent: DataPageContent = {
  accessNotice: {
    markdown: '',
  },
  releaseNotice: {
    markdown: '',
  },
  content: {
    markdown: '',
  },
};

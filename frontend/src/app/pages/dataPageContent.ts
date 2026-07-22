import { atom } from 'jotai';
import { unwrap } from 'jotai/utils';

import { contentList, type MarkdownBlock } from 'lib/api-client';

async function fetchPageContent(): Promise<DataPageContent> {
  const { data: blocks, error } = await contentList({
    baseUrl: '/api',
    path: { page: 'data' },
  });

  if (error) {
    throw new Error(`Failed to load data page content: ${JSON.stringify(error)}`);
  }

  const markdownBySlot = new Map(
    (blocks ?? []).map(({ slot, markdown }: MarkdownBlock) => [slot, markdown]),
  );

  return {
    accessNotice: {
      markdown: markdownBySlot.get('access_notice') ?? '',
    },
    releaseNotice: {
      markdown: markdownBySlot.get('release_notice') ?? '',
    },
    content: {
      markdown: markdownBySlot.get('content') ?? '',
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

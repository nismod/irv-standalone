import { atom } from 'jotai';
import { unwrap } from 'jotai/utils';

import { contentList, type MarkdownBlock } from 'lib/api-client';

async function fetchPageContent(): Promise<GuidePageContent> {
  const { data: blocks, error } = await contentList({
    baseUrl: '/api',
    path: { page: 'guide' },
  });

  if (error) {
    throw new Error(`Failed to load guide page content: ${JSON.stringify(error)}`);
  }

  const markdownBySlot = new Map(
    (blocks ?? []).map(({ slot, markdown }: MarkdownBlock) => [slot, markdown]),
  );

  return {
    content: {
      markdown: markdownBySlot.get('content') ?? '',
    },
  };
}

const pageContentQuery = atom(fetchPageContent);
export const pageContentState = unwrap(pageContentQuery, (prev) => prev ?? emptyPageContent);

export interface GuidePageContent {
  content: {
    markdown: string;
  };
}

export const emptyPageContent: GuidePageContent = {
  content: {
    markdown: '',
  },
};

import { atom } from 'jotai';
import { unwrap } from 'jotai/utils';

import { contentList, type MarkdownBlock } from 'lib/api-client';

async function fetchNoticeContent(): Promise<NoticeContent> {
  const { data: blocks, error } = await contentList({
    baseUrl: '/api',
    path: { page: 'notice' },
  });

  if (error) {
    throw new Error(`Failed to load notice content: ${JSON.stringify(error)}`);
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

const noticeContentQuery = atom(fetchNoticeContent);
export const noticeContentState = unwrap(
  noticeContentQuery,
  (prev) => prev ?? emptyNoticeContent,
);

export interface NoticeContent {
  content: {
    markdown: string;
  };
}

export const emptyNoticeContent: NoticeContent = {
  content: {
    markdown: '',
  },
};

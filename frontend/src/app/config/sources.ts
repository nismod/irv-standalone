import { makeConfig } from 'lib/helpers';

export const SOURCES = makeConfig([
  // {
  //   id: 'tileservergl',
  //   getUrl: ({ dataset }) => `/api/tiles/vector/data/${dataset}.json`,
  // },
  // {
  //   id: 'terracotta',
  //   getUrl: ({ dataset }) => `/api/tiles/vector/data/${dataset}.json`,
  // },
]);

export type SourceName = keyof typeof SOURCES;

import { isValidElement, type ReactNode } from 'react';
import { Typography, Link as MuiLink } from '@mui/material';
import { useAtomValue } from 'jotai';
import Markdown, { type Components } from 'react-markdown';

import ScrollToTop from 'lib/hooks/scroll-to-top';
import { ExtLink } from 'lib/nav';
import { pageContentState } from './guidePageContent';

function slugify(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-');
}

function flattenChildren(children: ReactNode): string {
  return Array.isArray(children)
    ? children.map(flattenChildren).join('')
    : typeof children === 'string' || typeof children === 'number'
      ? String(children)
      : isValidElement<{ children?: ReactNode }>(children)
        ? flattenChildren(children.props.children)
        : '';
}

const markdownComponents: Components = {
  a: ({ ...props }) => {
    if (!props.href) return <>{props.children}</>;

    if (props.href.startsWith('#')) {
      return <MuiLink {...props} />;
    }

    return <ExtLink {...props} />;
  },
  h1: ({ children, ...props }) => (
    <Typography
      variant="h1"
      gutterBottom
      id={slugify(flattenChildren(children))}
      {...props}
    >
      {children}
    </Typography>
  ),
  h2: ({ children, ...props }) => (
    <Typography
      variant="h2"
      gutterBottom
      id={slugify(flattenChildren(children))}
      sx={{ scrollMarginTop: 16 }}
      {...props}
    >
      {children}
    </Typography>
  ),
  h3: ({ children, ...props }) => (
    <Typography
      variant="h3"
      gutterBottom
      id={slugify(flattenChildren(children))}
      sx={{ scrollMarginTop: 16 }}
      {...props}
    >
      {children}
    </Typography>
  ),
  img: ({ ...props }) => <img {...props} width={720} style={{ maxWidth: '100%', height: 'auto' }} />,
};

export const GuidePage = () => {
  const pageContent = useAtomValue(pageContentState);

  return (
    <article>
      <ScrollToTop />
      <Markdown components={markdownComponents}>{pageContent.content.markdown}</Markdown>
    </article>
  );
};

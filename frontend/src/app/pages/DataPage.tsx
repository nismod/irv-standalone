import {
  Alert,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { useAtomValue } from 'jotai';
import Markdown, { type Components } from 'react-markdown';

import ScrollToTop from 'lib/hooks/scroll-to-top';
import { ExtLink } from 'lib/nav';
import { pageContentState } from './dataPageContent';

const markdownComponents: Components = {
  a: ({ ...props }) => {
    if (!props.href) return <>{props.children}</>;
    return <ExtLink {...props} />;
  },
  h1: ({ ...props }) => <Typography variant="h1" gutterBottom {...props} />,
  h2: ({ ...props }) => <Typography variant="h2" gutterBottom {...props} />,
  h3: ({ ...props }) => <Typography variant="h3" gutterBottom {...props} />,
  img: ({ ...props }) => <img {...props} width={180} />,
};

const renderMarkdown = (markdown: string) => (
  <Markdown components={markdownComponents}>{markdown}</Markdown>
);

const inlineMarkdownComponents: Components = {
  ...markdownComponents,
  p: ({ children }) => <>{children}</>,
};

const renderInlineMarkdown = (markdown: string) => (
  <Markdown components={inlineMarkdownComponents}>{markdown}</Markdown>
);

interface ParsedMarkdownTable {
  headers: string[];
  rows: string[][];
}

interface MarkdownContentBlock {
  kind: 'markdown' | 'table' | 'accessNotice';
  markdown: string;
}

function parseMarkdownTable(markdown: string): ParsedMarkdownTable {
  const lines = markdown
    .trim()
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length < 2) {
    throw new Error('Markdown table must include a header row and divider row.');
  }

  const [headerLine, dividerLine, ...rowLines] = lines;
  const headers = parseMarkdownTableLine(headerLine);
  const dividerCells = parseMarkdownTableLine(dividerLine);

  if (headers.length === 0 || dividerCells.length !== headers.length) {
    throw new Error('Markdown table header and divider must have matching column counts.');
  }

  const rows = rowLines.map((line) => {
    const cells = parseMarkdownTableLine(line);
    if (cells.length !== headers.length) {
      throw new Error('Markdown table row has a different column count than the header.');
    }
    return cells;
  });

  return { headers, rows };
}

function parseMarkdownTableLine(line: string): string[] {
  const trimmed = line.trim().replace(/^\|/, '').replace(/\|$/, '');
  return trimmed.split('|').map((cell) => cell.trim());
}

function isMarkdownTableStart(lines: string[], index: number): boolean {
  const currentLine = lines[index]?.trim() ?? '';
  const nextLine = lines[index + 1]?.trim() ?? '';
  return currentLine.startsWith('|') && currentLine.endsWith('|') && /^(\|\s*:?-+:?\s*)+\|$/.test(nextLine);
}

function parseMarkdownContentBlocks(markdown: string): MarkdownContentBlock[] {
  const lines = markdown.trim().split('\n');
  const blocks: MarkdownContentBlock[] = [];
  let buffer: string[] = [];
  let index = 0;

  const flushBuffer = () => {
    const text = buffer.join('\n').trim();
    if (text) {
      blocks.push({ kind: 'markdown', markdown: text });
    }
    buffer = [];
  };

  while (index < lines.length) {
    if (lines[index].trim() === '[[access-notice]]') {
      flushBuffer();
      blocks.push({ kind: 'accessNotice', markdown: '' });
      index += 1;
      continue;
    }

    if (isMarkdownTableStart(lines, index)) {
      flushBuffer();
      const tableLines = [lines[index], lines[index + 1]];
      index += 2;

      while (index < lines.length) {
        const line = lines[index].trim();
        if (!line.startsWith('|') || !line.endsWith('|')) {
          break;
        }
        tableLines.push(lines[index]);
        index += 1;
      }

      blocks.push({ kind: 'table', markdown: tableLines.join('\n') });
      continue;
    }

    buffer.push(lines[index]);
    index += 1;
  }

  flushBuffer();
  return blocks;
}

const MarkdownTable = ({ markdown, ariaLabel }: { markdown: string; ariaLabel: string }) => {
  const { headers, rows } = parseMarkdownTable(markdown);

  return (
    <TableContainer component={Paper} sx={{ my: 2 }}>
      <Table aria-label={ariaLabel}>
        <TableHead>
          <TableRow>
            {headers.map((header) => (
              <TableCell key={header}>{header}</TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((row, rowIndex) => (
            <TableRow key={`${ariaLabel}-${rowIndex}`}>
              {row.map((cell, cellIndex) => (
                <TableCell key={`${ariaLabel}-${rowIndex}-${cellIndex}`}>
                  {renderInlineMarkdown(cell)}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export const DataPage = () => {
  const pageContent = useAtomValue(pageContentState);
  const contentBlocks = parseMarkdownContentBlocks(pageContent.content.markdown);

  return (
    <article>
      <ScrollToTop />

      <Alert severity="info" sx={{ mb: 2 }}>
        {renderMarkdown(pageContent.accessNotice.markdown)}
      </Alert>

      <Alert
        severity="success"
        sx={{ mb: 2 }}
        action={
          <Button color="inherit" size="small">
            <ExtLink href="https://github.com/nismod/irv-jamaica/issues">REPORT</ExtLink>
          </Button>
        }
      >
        {renderMarkdown(pageContent.releaseNotice.markdown)}
      </Alert>

      {contentBlocks.map((block, index) =>
        block.kind === 'table' ? (
          <MarkdownTable
            key={`table-${index}`}
            markdown={block.markdown}
            ariaLabel={`Data page table ${index + 1}`}
          />
        ) : block.kind === 'accessNotice' ? (
          <Alert key={`access-notice-${index}`} severity="info" sx={{ mb: 2 }}>
            {renderMarkdown(pageContent.accessNotice.markdown)}
          </Alert>
        ) : (
          <div key={`markdown-${index}`}>{renderMarkdown(block.markdown)}</div>
        ),
      )}
    </article>
  );
};

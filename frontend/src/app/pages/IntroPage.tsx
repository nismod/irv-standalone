import { Fragment } from 'react';
import { styled } from '@mui/material/styles';
import { Divider, Grid, Paper, Stack, Typography } from '@mui/material';
import { atom, useAtomValue } from 'jotai';
import { unwrap } from 'jotai/utils';
import Markdown, { type Components } from 'react-markdown';

import ScrollToTop from 'lib/hooks/scroll-to-top';
import { ExtLink } from 'lib/nav';

interface Logo {
  href: string;
  src: string;
  alt: string;
  height: number;
}

interface IntroPageContent {
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

const emptyPageContent: IntroPageContent = {
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

async function fetchPageContent(): Promise<IntroPageContent> {
  const module = await import('./intro.json');
  return module.default as IntroPageContent;
}

const pageContentQuery = atom(fetchPageContent);
const pageContentState = unwrap(pageContentQuery, (prev) => prev ?? emptyPageContent);

const HeadingBox = styled(Paper)(({ theme }) => ({
  backgroundColor: 'rgba(0, 92, 97, 0.3)',
  color: '#fff',
  padding: theme.spacing(2),
  borderRadius: 0,
}));

const TextBox = styled(Paper)(() => ({
  backgroundColor: 'rgba(194, 219, 231, 0.9)',
  color: '#333',
  padding: '16px 32px',
  borderRadius: 0,
}));

const markdownComponents: Components = {
  a: ({ node, ...props }) => {
    if (!props.href) return <>{props.children}</>;
    return <ExtLink {...props} />;
  },
};

const smallMarkdownComponents: Components = {
  ...markdownComponents,
  p: ({ children }) => (
    <p>
      <small>{children}</small>
    </p>
  ),
};

const LogoRow = ({ logos }: { logos: Logo[] }) => (
  <Stack
    direction={{ xs: 'column', md: 'row' }}
    divider={<Divider orientation="vertical" flexItem />}
    spacing={2}
    justifyContent="center"
    alignItems="center"
    sx={{ my: 2 }}
  >
    {logos.map((logo) => (
      <ExtLink key={logo.href} href={logo.href}>
        <img height={logo.height} src={logo.src} alt={logo.alt} />
      </ExtLink>
    ))}
  </Stack>
);

export const IntroPage = () => {
  const pageContent = useAtomValue(pageContentState);
  return (
    <div
      className="home"
      style={{
        backgroundImage: pageContent.backgroundImage.src
          ? `url("${pageContent.backgroundImage.src}")`
          : undefined,
      }}
    >
      <article>
        <ScrollToTop />
        <Grid container columnSpacing={8} rowSpacing={4}>
          <Grid
            sx={{ width: '100%' }}
            size={{
              md: 6,
            }}
          >
            <HeadingBox sx={{ mt: -2, pt: 8 }}>
              <Typography variant="h1">{pageContent.title}</Typography>
            </HeadingBox>
          </Grid>
          <Grid
            size={{
              md: 6,
            }}
          >
            <TextBox sx={{ mt: -2, pt: 8 }}>
              <p>{pageContent.summary}</p>
              {pageContent.sectors.map((sector) => (
                <Fragment key={sector.title}>
                  <Typography variant="h2">{sector.title}</Typography>
                  <p>{sector.description}</p>
                </Fragment>
              ))}
            </TextBox>
          </Grid>
          <Grid size={12}>
            <TextBox sx={{ backgroundColor: 'rgba(255, 255, 255, 0.9)' }}>
              <Markdown components={markdownComponents}>
                {pageContent.collaboration.markdown}
              </Markdown>
              <LogoRow logos={pageContent.collaboration.logos} />

              <Typography variant="h2">{pageContent.funding.title}</Typography>

              <Markdown components={markdownComponents}>{pageContent.funding.markdown}</Markdown>

              <LogoRow logos={pageContent.funding.logos} />

              <Markdown components={smallMarkdownComponents}>
                {pageContent.backgroundImage.credit}
              </Markdown>
            </TextBox>
          </Grid>
        </Grid>
      </article>
    </div>
  );
};

import InfoOutlined from '@mui/icons-material/InfoOutlined';
import { Box, Button, Container, DialogActions, Drawer, Stack, Typography } from '@mui/material';
import { useCallback, type ComponentPropsWithoutRef } from 'react';
import { useAtom, useAtomValue } from 'jotai';
import { atomWithStorage } from 'jotai/utils';
import Markdown, { type Components } from 'react-markdown';

import { AppLink, ExtLink } from 'lib/nav';
import { noticeContentState } from './noticeContent';

const noticeAcceptedDateState = atomWithStorage<Date | null>('notice-accepted', null, {
  getItem: (key, initialValue) => {
    const raw = localStorage.getItem(key);
    if (raw == null) return initialValue;
    try {
      const parsed = JSON.parse(raw) as string | null;
      return parsed != null ? new Date(parsed) : null;
    } catch {
      return initialValue;
    }
  },
  setItem: (key, value) => {
    localStorage.setItem(key, JSON.stringify(value));
  },
  removeItem: (key) => {
    localStorage.removeItem(key);
  },
});

const markdownComponents: Components = {
  a: ({ href, ...props }) => {
    if (!href) return <>{props.children}</>;
    if (href.startsWith('/')) {
      return <AppLink to={href} {...props} />;
    }
    return <ExtLink href={href} {...props} />;
  },
  p: ({ ...props }: ComponentPropsWithoutRef<'p'>) => (
    <Typography paragraph sx={{ m: 0 }} {...props} />
  ),
};

export const Notice = () => {
  const [acceptedDate, setAcceptedDate] = useAtom(noticeAcceptedDateState);
  const noticeContent = useAtomValue(noticeContentState);

  const handleAccept = useCallback(() => {
    setAcceptedDate(new Date());
  }, [setAcceptedDate]);

  return (
    <Drawer variant="persistent" anchor="bottom" open={acceptedDate == null}>
      <Container maxWidth="lg">
        <Stack direction="row" alignItems="center" spacing={2} my={5}>
          <Box>
            <InfoOutlined color="primary" />
          </Box>
          <Markdown components={markdownComponents}>{noticeContent.content.markdown}</Markdown>
          <DialogActions>
            <Button variant="contained" onClick={handleAccept}>
              Accept
            </Button>
          </DialogActions>
        </Stack>
      </Container>
    </Drawer>
  );
};

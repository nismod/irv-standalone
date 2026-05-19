import { FormEvent, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Stack,
  TextField,
  Typography,
} from '@mui/material';

import { useLoginMutation } from 'lib/auth/use-auth-session';

export const LoginRequiredPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [submitError, setSubmitError] = useState<string | null>(null);
  const loginMutation = useLoginMutation();

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitError(null);

    try {
      await loginMutation.mutateAsync({ username, password });
      setPassword('');
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Unable to log in.';
      setSubmitError(message);
    }
  };

  return (
    <Box
      alignItems="center"
      display="flex"
      height="100%"
      justifyContent="center"
      px={2}
    >
      <Box
        component="form"
        maxWidth={420}
        onSubmit={handleSubmit}
        sx={{ backgroundColor: 'white', borderRadius: 2, p: 3, width: '100%' }}
      >
        <Stack spacing={2}>
          <Typography component="h1" variant="h5">
            Sign in to view maps
          </Typography>
          <Typography color="text.secondary" variant="body2">
            You need an active account session to access map views.
          </Typography>
          {submitError ? <Alert severity="error">{submitError}</Alert> : null}
          <TextField
            autoComplete="username"
            label="Username"
            onChange={(event) => setUsername(event.target.value)}
            required
            value={username}
          />
          <TextField
            autoComplete="current-password"
            label="Password"
            onChange={(event) => setPassword(event.target.value)}
            required
            type="password"
            value={password}
          />
          <Button
            disabled={loginMutation.isPending}
            type="submit"
            variant="contained"
          >
            {loginMutation.isPending ? 'Signing in...' : 'Sign in'}
          </Button>
        </Stack>
      </Box>
    </Box>
  );
};

import { createClient } from 'lib/api-client/client';
import { authLoginCreate, authMeRetrieve } from 'lib/api-client';
import type { LoginErrorResponse, SessionState } from 'lib/api-client';

export type AuthSession = SessionState;

const apiClient = createClient({
  baseUrl: '/api',
});

function readCookie(name: string): string | null {
  const cookie = document.cookie
    .split(';')
    .map((part) => part.trim())
    .find((part) => part.startsWith(`${name}=`));

  if (!cookie) {
    return null;
  }

  return decodeURIComponent(cookie.slice(name.length + 1));
}

function parseClientError(error: unknown): string {
  if (
    error &&
    typeof error === 'object' &&
    'detail' in error &&
    typeof (error as LoginErrorResponse).detail === 'string'
  ) {
    return (error as LoginErrorResponse).detail;
  }

  if (typeof error === 'string') {
    return error;
  }

  return 'Request failed.';
}

async function ensureCsrfToken(): Promise<string | null> {
  const token = readCookie('csrftoken');
  if (token) {
    return token;
  }

  await authMeRetrieve({
    client: apiClient,
  });

  return readCookie('csrftoken');
}

export async function fetchAuthSession(): Promise<AuthSession> {
  const { data, error } = await authMeRetrieve({
    client: apiClient,
  });

  if (error) {
    throw new Error(parseClientError(error));
  }

  return data as AuthSession;
}

export async function loginWithPassword(username: string, password: string): Promise<AuthSession> {
  const csrfToken = await ensureCsrfToken();

  const { data, error } = await authLoginCreate({
    client: apiClient,
    body: { username, password },
    headers: {
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
  });

  if (error) {
    throw new Error(parseClientError(error));
  }

  return data as AuthSession;
}

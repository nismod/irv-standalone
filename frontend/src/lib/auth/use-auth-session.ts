import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { AuthSession, fetchAuthSession, loginWithPassword } from './session-api';

export const authSessionQueryKey = ['auth', 'session'] as const;

export function useAuthSessionQuery() {
  return useQuery({
    queryKey: authSessionQueryKey,
    queryFn: fetchAuthSession,
    staleTime: 60 * 1000,
  });
}

export function useLoginMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ username, password }: { username: string; password: string }) =>
      loginWithPassword(username, password),
    onSuccess: (session: AuthSession) => {
      queryClient.setQueryData(authSessionQueryKey, session);
    },
  });
}

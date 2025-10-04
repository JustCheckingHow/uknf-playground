'use client';

import { useAuthContext } from '@/src/providers/AuthProvider';

export function useAuth() {
  return useAuthContext();
}

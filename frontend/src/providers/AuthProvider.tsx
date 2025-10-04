'use client';

import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';

import type { ProfileResponse, User } from '@/src/types';
import { apiClient, setAuthToken } from '@/src/lib/api';

interface AuthContextValue {
  user: User | null;
  profile: ProfileResponse | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [token, setTokenState] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const storedToken = typeof window !== 'undefined' ? localStorage.getItem('uknf-token') : null;
    if (storedToken) {
      setAuthToken(storedToken);
      setTokenState(storedToken);
      refreshProfile().finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const refreshProfile = useCallback(async () => {
    try {
      const response = await apiClient.get<ProfileResponse>('/auth/profile');
      setProfile(response.data);
      setUser(response.data.user);
    } catch (error) {
      console.error('Nie udało się pobrać profilu użytkownika', error);
      setProfile(null);
      setUser(null);
      setAuthToken(undefined);
      setTokenState(null);
      if (typeof window !== 'undefined') {
        localStorage.removeItem('uknf-token');
      }
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const response = await apiClient.post<{ token: string; user: User }>('/auth/login', { email, password });
      const authToken = response.data.token;
      setAuthToken(authToken);
      setTokenState(authToken);
      if (typeof window !== 'undefined') {
        localStorage.setItem('uknf-token', authToken);
      }
      setUser(response.data.user);
      await refreshProfile();
      return true;
    } catch (error) {
      console.error('Nie udało się zalogować', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [refreshProfile]);

  const logout = useCallback(async () => {
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      console.warn('Wylogowanie zakończone ostrzeżeniem', error);
    }
    setUser(null);
    setProfile(null);
    setAuthToken(undefined);
    setTokenState(null);
    if (typeof window !== 'undefined') {
      localStorage.removeItem('uknf-token');
    }
    router.push('/login');
  }, [router]);

  const value = useMemo(
    () => ({ user, profile, token, isLoading, login, logout, refreshProfile }),
    [isLoading, login, logout, profile, refreshProfile, token, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext must be used within AuthProvider');
  }
  return context;
}

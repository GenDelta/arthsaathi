/**
 * Auth store (Zustand slice) — ARCHITECTURE.md §1.2, AGENT_INSTRUCTIONS.md §3
 *
 * Manages: access token, refresh token, user profile, login/logout actions.
 * Token storage: in-memory (access) + localStorage with explicit consent note (refresh).
 */

import { create } from 'zustand';

interface User {
  id: string;
  name: string;
  role: 'CITIZEN' | 'NGO_ADMIN' | 'NGO_EDUCATOR' | 'SPONSOR_VIEWER';
  language_pref: string;
  organization_id: string | null;
}

interface AuthState {
  accessToken: string | null;
  user: User | null;
  isAuthenticated: boolean;

  setAuth: (accessToken: string, user: User) => void;
  clearAuth: () => void;
  setAccessToken: (token: string) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  isAuthenticated: false,

  setAuth: (accessToken, user) =>
    set({ accessToken, user, isAuthenticated: true }),

  clearAuth: () =>
    set({ accessToken: null, user: null, isAuthenticated: false }),

  setAccessToken: (token) => set({ accessToken: token }),
}));

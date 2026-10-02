"use client";

/**
 * Auth store (Zustand slice) — ARCHITECTURE.md §1.2, AGENT_INSTRUCTIONS.md §3
 *
 * Manages: access token, refresh token, user profile, login/logout actions.
 * Token storage: in-memory (access) + localStorage with explicit consent note (refresh).
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { authApi, type MeResponse } from "@/lib/api-client";

type Role = "CITIZEN" | "NGO_ADMIN" | "NGO_EDUCATOR" | "SPONSOR_VIEWER";

interface User {
  id: string;
  name: string;
  role: Role;
  language_pref: string;
  organization_id: string | null;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isOnboarded: boolean;
  isLoading: boolean;

  setAuth: (accessToken: string, refreshToken: string, user: User, isOnboarded?: boolean) => void;
  setAccessToken: (token: string) => void;
  setOnboarded: (value: boolean) => void;
  clearAuth: () => void;
  fetchMe: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      isOnboarded: false,
      isLoading: false,

      setAuth(accessToken, refreshToken, user, isOnboarded = false) {
        set({ accessToken, refreshToken, user, isAuthenticated: true, isOnboarded });
      },

      setAccessToken(token) {
        set({ accessToken: token });
      },

      setOnboarded(value) {
        set({ isOnboarded: value });
      },

      clearAuth() {
        set({ accessToken: null, refreshToken: null, user: null, isAuthenticated: false, isOnboarded: false });
      },

      async fetchMe() {
        const token = get().accessToken;
        if (!token) return;
        set({ isLoading: true });
        try {
          const me: MeResponse = await authApi.me(token);
          set({
            user: {
              id: me.id,
              name: me.name,
              role: me.role as Role,
              language_pref: me.language_pref,
              organization_id: me.organization_id,
            },
            isAuthenticated: true,
            isOnboarded: me.is_onboarded,
          });
        } catch (err) {
          // If the token is invalid (e.g., DB wiped, user deleted, expired),
          // clear the local auth state so the user is logged out cleanly.
          get().clearAuth();
        } finally {
          set({ isLoading: false });
        }
      },
    }),
    {
      name: "arthsaathi-auth",
      // Only persist tokens — not user data (always re-fetched on load)
      partialize: (s) => ({
        accessToken: s.accessToken,
        refreshToken: s.refreshToken,
      }),
    },
  ),
);

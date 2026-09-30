"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import { Sidebar } from "@/components/layout/Sidebar";
import { MobileNav } from "@/components/layout/MobileNav";
import { Loader2 } from "lucide-react";
import { NotificationProvider } from "@/components/providers/NotificationProvider";
import { SupervisorChat } from "@/components/SupervisorChat";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isOnboarded, accessToken, fetchMe } = useAuthStore();
  const router = useRouter();
  const [isMounted, setIsMounted] = useState(false);
  const [isRehydrating, setIsRehydrating] = useState(true);

  // Step 1: Mount guard — avoids SSR mismatch
  useEffect(() => {
    setIsMounted(true);
  }, []);

  // Step 2: After mount, if we have a stored token but isAuthenticated is false
  // (happens on page refresh — Zustand restores tokens but not derived booleans),
  // call fetchMe() to revalidate the token and restore the full session.
  useEffect(() => {
    if (!isMounted) return;

    if (accessToken && !isAuthenticated) {
      // Token exists in localStorage but session isn't active yet — rehydrate
      fetchMe().finally(() => setIsRehydrating(false));
    } else {
      // Either already authenticated, or no token at all
      setIsRehydrating(false);
    }
  }, [isMounted, accessToken, isAuthenticated, fetchMe]);

  // Step 3: Once rehydration is done, enforce auth guard
  useEffect(() => {
    if (isRehydrating || !isMounted) return;

    if (!isAuthenticated) {
      router.replace("/auth");
    } else if (!isOnboarded) {
      router.replace("/onboarding");
    }
  }, [isRehydrating, isMounted, isAuthenticated, isOnboarded, router]);

  // Show spinner while we're checking the token
  if (!isMounted || isRehydrating) {
    return (
      <div className="h-dvh w-full flex items-center justify-center bg-background">
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
      </div>
    );
  }

  // Not authenticated — redirect is in flight, show spinner
  if (!isAuthenticated || !isOnboarded) {
    return (
      <div className="h-dvh w-full flex items-center justify-center bg-background">
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
      </div>
    );
  }

  return (
    <NotificationProvider>
      <div className="flex h-dvh overflow-hidden bg-background">
        <Sidebar />
        <main className="flex-1 overflow-y-auto pb-16 md:pb-0 relative">
          <div className="max-w-7xl mx-auto p-4 md:p-8">
            {children}
          </div>
        </main>
        <SupervisorChat />
        <MobileNav />
      </div>
    </NotificationProvider>
  );
}

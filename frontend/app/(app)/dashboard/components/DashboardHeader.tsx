"use client";

import Link from "next/link";
import { useAuthStore } from "@/store/useAuthStore";
import { UserCircle } from "lucide-react";

export function DashboardHeader() {
  const { user } = useAuthStore();
  const userName = user?.name || "Friend"; 
  const today = new Intl.DateTimeFormat('en-IN', { 
    weekday: 'long', month: 'long', day: 'numeric' 
  }).format(new Date());

  return (
    <div className="flex items-center justify-between">
      <div className="flex flex-col gap-1">
        <h1 className="font-outfit text-3xl font-bold text-text-primary">
          Hello, {userName}
        </h1>
        <p className="text-text-secondary text-sm">
          {today}
        </p>
      </div>
      <Link 
        href="/profile" 
        className="md:hidden p-2 bg-surface border border-border rounded-full text-text-secondary hover:text-accent hover:border-accent transition-colors"
      >
        <UserCircle size={28} />
      </Link>
    </div>
  );
}

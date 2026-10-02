"use client";

import { useState, useCallback, useEffect } from "react";
import { DashboardHeader } from "./components/DashboardHeader";
import { OverviewCards, getDatePresets } from "./components/OverviewCards";
import { GuardianNudges } from "./components/GuardianNudges";
import { RecentTransactions } from "./components/RecentTransactions";
import { PdfUpload } from "./components/PdfUpload";
import { VoiceLog } from "./components/VoiceLog";
import { SurfaceCard } from "@/components/ui/SurfaceCard";
import { SpendingBreakdown } from "./components/SpendingBreakdown";
import { ChevronDown } from "lucide-react";

const DATE_PRESETS = getDatePresets();

export default function DashboardPage() {
  const [refresh, setRefresh] = useState(0);
  const bump = useCallback(() => setRefresh((n) => n + 1), []);

  useEffect(() => {
    const handleGlobalRefresh = () => bump();
    window.addEventListener("refresh_transactions", handleGlobalRefresh);
    return () => window.removeEventListener("refresh_transactions", handleGlobalRefresh);
  }, [bump]);

  // Shared date filter — drives both OverviewCards and RecentTransactions
  const [presetValue, setPresetValue] = useState("all");
  const activePreset = DATE_PRESETS.find((p) => p.value === presetValue) ?? DATE_PRESETS[DATE_PRESETS.length - 1];

  return (
    <div className="flex flex-col gap-6 w-full animate-fade-up">
      <DashboardHeader />

      {/*
        Bento Grid Layout:
        Mobile: 1 column (Nudges first, then Overview, then Transactions)
        Desktop: 3 columns (Overview + Transactions take 2, Nudges take 1)
      */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Mobile: Guardian Nudges appear FIRST (order-1) / Desktop: Sidebar (order-2) */}
        <div className="order-1 lg:order-2 lg:col-span-1 space-y-6">
          <GuardianNudges
            refresh={refresh}
            start_date={activePreset.start_date}
            end_date={activePreset.end_date}
          />
          <SpendingBreakdown
            refresh={refresh}
            start_date={activePreset.start_date}
            end_date={activePreset.end_date}
          />
        </div>

        {/* Mobile: Stats appear SECOND (order-2) / Desktop: Main area (order-1) */}
        <div className="order-2 lg:order-1 lg:col-span-2 space-y-6">

          {/* ── Shared date filter ─────────────────────────────────────────── */}
          <div className="flex items-center gap-3">
            <span className="text-text-secondary text-sm">Period:</span>
            <div className="relative">
              <select
                value={presetValue}
                onChange={(e) => setPresetValue(e.target.value)}
                className="
                  appearance-none bg-[#111] border border-white/10
                  text-text-primary text-sm pl-3 pr-8 py-1.5 rounded-lg
                  focus:outline-none focus:border-amber-400/60
                  cursor-pointer hover:border-white/20 transition-colors
                "
              >
                {DATE_PRESETS.map((p) => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
              <ChevronDown
                size={12}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-text-secondary pointer-events-none"
              />
            </div>
          </div>

          {/* Overview stats — re-fetch when refresh bumps or period changes */}
          <OverviewCards
            refresh={refresh}
            start_date={activePreset.start_date}
            end_date={activePreset.end_date}
            periodLabel={activePreset.label}
          />

          {/* Input row: PDF upload + voice logger */}
          <SurfaceCard id="pdf-upload" className="p-4 flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <PdfUpload onSuccess={bump} />
            <div className="hidden sm:block h-8 w-px bg-white/10 flex-shrink-0" />
            <div className="sm:hidden w-full h-px bg-white/10" />
            <div className="flex-1 w-full">
              <VoiceLog onSuccess={bump} />
            </div>
          </SurfaceCard>

          {/* Transaction list — filtered by same period + type */}
          <RecentTransactions
            refresh={refresh}
            start_date={activePreset.start_date}
            end_date={activePreset.end_date}
          />
        </div>

      </div>
    </div>
  );
}

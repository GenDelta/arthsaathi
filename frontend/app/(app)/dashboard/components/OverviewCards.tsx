"use client";

import { useEffect, useState } from "react";
import { SurfaceCard } from "@/components/ui/SurfaceCard";
import { ArrowUpRight, ArrowDownRight, Wallet } from "lucide-react";
import { useAuthStore } from "@/store/useAuthStore";
import { transactionsApi, type TransactionSummary } from "@/lib/api-client";

function formatINR(amount: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

function SkeletonCard() {
  return (
    <SurfaceCard className="flex flex-col gap-3 p-5 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="h-4 w-24 bg-white/10 rounded" />
        <div className="h-8 w-8 rounded-full bg-white/10" />
      </div>
      <div>
        <div className="h-8 w-32 bg-white/10 rounded mb-2" />
        <div className="h-3 w-20 bg-white/10 rounded" />
      </div>
    </SurfaceCard>
  );
}

export interface DatePreset {
  value: string;
  label: string;
  start_date?: string;
  end_date?: string;
}

export function getDatePresets(): DatePreset[] {
  const now = new Date();
  // Use local date parts to avoid UTC offset shifting the date (e.g. IST = UTC+5:30)
  const fmt = (d: Date) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  const today = fmt(now);

  const startOfWeek = new Date(now);
  startOfWeek.setDate(now.getDate() - 7);

  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);

  const start3M = new Date(now);
  start3M.setMonth(now.getMonth() - 3);

  const startOfYear = new Date(now.getFullYear(), 0, 1);

  return [
    { value: "week",   label: "This Week",     start_date: fmt(startOfWeek), end_date: today },
    { value: "month",  label: "This Month",    start_date: fmt(startOfMonth), end_date: today },
    { value: "3m",     label: "Last 3 Months", start_date: fmt(start3M),     end_date: today },
    { value: "year",   label: "This Year",     start_date: fmt(startOfYear), end_date: today },
    { value: "all",    label: "All Time" },
  ];
}

interface OverviewCardsProps {
  refresh?: number;
  start_date?: string;
  end_date?: string;
  periodLabel?: string;
}

export function OverviewCards({
  refresh = 0,
  start_date,
  end_date,
  periodLabel = "All time",
}: OverviewCardsProps) {
  const { accessToken } = useAuthStore();
  const [summary, setSummary] = useState<TransactionSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    setLoading(true);
    setError(null);

    transactionsApi
      .list(accessToken, { start_date, end_date, limit: 500 })
      .then((res) => setSummary(res.summary))
      .catch((err) => setError(err.message || "Failed to load summary"))
      .finally(() => setLoading(false));
  }, [accessToken, refresh, start_date, end_date]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <SkeletonCard /><SkeletonCard /><SkeletonCard />
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <SurfaceCard className="md:col-span-3 p-5 text-center text-text-secondary text-sm">
          {error ?? "No summary data available."}
        </SurfaceCard>
      </div>
    );
  }

  const stats = [
    {
      label: "Total Income",
      amount: formatINR(summary.total_income),
      sub: periodLabel,
      icon: ArrowUpRight,
      iconColor: "text-emerald-400",
      iconBg: "bg-emerald-400/10",
    },
    {
      label: "Total Expenses",
      amount: formatINR(summary.total_expenses),
      sub: periodLabel,
      icon: ArrowDownRight,
      iconColor: "text-red-400",
      iconBg: "bg-red-400/10",
    },
    {
      label: "Net Savings",
      amount: formatINR(summary.net_savings),
      sub: `${summary.count} transaction${summary.count !== 1 ? "s" : ""}`,
      icon: Wallet,
      iconColor: summary.net_savings >= 0 ? "text-amber-400" : "text-red-400",
      iconBg: summary.net_savings >= 0 ? "bg-amber-400/10" : "bg-red-400/10",
    },
  ];

  const totalFlow = (summary?.total_income || 0) + (summary?.total_expenses || 0);
  const incPct = totalFlow > 0 ? ((summary?.total_income || 0) / totalFlow) * 100 : 50;
  const expPct = totalFlow > 0 ? ((summary?.total_expenses || 0) / totalFlow) * 100 : 50;

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {stats.map((stat) => (
          <SurfaceCard key={stat.label} className="flex flex-col gap-3 p-5">
            <div className="flex items-center justify-between">
              <span className="text-text-secondary text-sm font-medium">{stat.label}</span>
              <div className={`p-2 rounded-full ${stat.iconBg} ${stat.iconColor}`}>
                <stat.icon size={16} />
              </div>
            </div>
            <div>
              <div className="font-mono text-3xl text-text-primary tracking-tight">
                {stat.amount}
              </div>
              <div className="text-xs text-text-secondary mt-1 font-medium">{stat.sub}</div>
            </div>
          </SurfaceCard>
        ))}
      </div>

      {/* Visual Cash Flow Bar */}
      {totalFlow > 0 && (
        <SurfaceCard className="p-4 flex flex-col gap-3 border-white/5">
          <div className="flex items-center justify-between text-xs font-medium px-1">
            <span className="text-emerald-400">Income ({incPct.toFixed(0)}%)</span>
            <span className="text-red-400">Expense ({expPct.toFixed(0)}%)</span>
          </div>
          <div className="flex h-2.5 w-full rounded-full overflow-hidden bg-white/5">
            <div className="bg-emerald-400 h-full transition-all duration-500" style={{ width: `${incPct}%` }} />
            <div className="bg-red-400 h-full transition-all duration-500" style={{ width: `${expPct}%` }} />
          </div>
        </SurfaceCard>
      )}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { SurfaceCard } from "@/components/ui/SurfaceCard";
import { useAuthStore } from "@/store/useAuthStore";
import { transactionsApi, type BreakdownResponse } from "@/lib/api-client";
import { PieChart, ListFilter } from "lucide-react";

interface SpendingBreakdownProps {
  refresh?: number;
  start_date?: string;
  end_date?: string;
}

function formatINR(amount: number): string {
  if (amount >= 1000) return `₹${(amount / 1000).toFixed(1)}k`;
  return `₹${amount.toFixed(0)}`;
}

export function SpendingBreakdown({ refresh = 0, start_date, end_date }: SpendingBreakdownProps) {
  const { accessToken } = useAuthStore();
  const [breakdown, setBreakdown] = useState<BreakdownResponse | null>(null);
  const [loading, setLoading] = useState(true);

  // Tab: "expense" | "income"
  const [tab, setTab] = useState<"expense" | "income">("expense");

  useEffect(() => {
    if (!accessToken) return;
    setLoading(true);
    transactionsApi
      .getBreakdown(accessToken, start_date, end_date)
      .then((res) => setBreakdown(res))
      .catch((err) => console.error("Failed to load breakdown:", err))
      .finally(() => setLoading(false));
  }, [accessToken, start_date, end_date, refresh]);

  const items = tab === "expense" ? breakdown?.expense : breakdown?.income;

  return (
    <SurfaceCard id="spending-breakdown" className="p-5 flex flex-col gap-5 border-white/5">
      <div className="flex items-center justify-between border-b border-border pb-3">
        <h2 className="font-outfit font-semibold text-lg text-text-primary flex items-center gap-2">
          <PieChart size={20} className="text-text-secondary" />
          Breakdown
        </h2>
        
        {/* Tab toggle */}
        <div className="flex bg-[#111] border border-border rounded-lg p-0.5">
          <button
            onClick={() => setTab("expense")}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
              tab === "expense" ? "bg-red-400/10 text-red-400" : "text-text-secondary hover:text-text-primary"
            }`}
          >
            Expenses
          </button>
          <button
            onClick={() => setTab("income")}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
              tab === "income" ? "bg-emerald-400/10 text-emerald-400" : "text-text-secondary hover:text-text-primary"
            }`}
          >
            Income
          </button>
        </div>
      </div>

      <div className="flex flex-col gap-4 min-h-[160px]">
        {loading ? (
          <div className="flex flex-col gap-4 mt-2 animate-pulse">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="flex flex-col gap-2">
                <div className="flex justify-between h-3 bg-white/10 rounded w-1/3" />
                <div className="h-2 bg-white/5 rounded-full overflow-hidden w-full" />
              </div>
            ))}
          </div>
        ) : !items || items.length === 0 ? (
          <div className="flex flex-col items-center justify-center flex-1 text-center gap-2 text-text-secondary h-full py-8">
            <ListFilter size={32} className="opacity-20 mb-2" />
            <p className="text-sm">No data available.</p>
            <p className="text-xs opacity-70">No {tab}s found for this period.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {items.map((item) => (
              <div key={item.category} className="flex flex-col gap-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-text-primary font-medium tracking-wide">
                    {item.category.replace(/_/g, " ")}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="text-text-primary font-mono">{formatINR(item.amount)}</span>
                    <span className="text-text-secondary text-xs w-8 text-right">{item.percentage}%</span>
                  </div>
                </div>
                {/* Visual bar */}
                <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${tab === "expense" ? "bg-red-400" : "bg-emerald-400"}`}
                    style={{ width: `${item.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </SurfaceCard>
  );
}

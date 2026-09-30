"use client";

import { useEffect, useState } from "react";
import { SurfaceCard } from "@/components/ui/SurfaceCard";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ShieldAlert, TrendingUp, Info, X } from "lucide-react";
import { useAuthStore } from "@/store/useAuthStore";
import { guardianApi, transactionsApi, type Nudge, type Transaction } from "@/lib/api-client";
import { useRouter } from "next/navigation";

interface GuardianNudgesProps {
  refresh?: number;
  start_date?: string;
  end_date?: string;
}

export function GuardianNudges({ refresh = 0, start_date, end_date }: GuardianNudgesProps) {
  const { accessToken } = useAuthStore();
  const [nudges, setNudges] = useState<Nudge[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Modal State
  const [activeInsight, setActiveInsight] = useState<Nudge | null>(null);
  const [insightData, setInsightData] = useState<Transaction[] | null>(null);
  const [insightLoading, setInsightLoading] = useState(false);

  const router = useRouter();

  useEffect(() => {
    if (!accessToken) return;
    setLoading(true);
    guardianApi
      .getNudges(accessToken, start_date, end_date)
      .then((res) => setNudges(res.nudges))
      .catch((err) => console.error("Failed to load nudges:", err))
      .finally(() => setLoading(false));
  }, [accessToken, start_date, end_date, refresh]);

  function getIcon(type: string) {
    if (type === "GUARDIAN_ALERT") return <ShieldAlert size={16} className="text-danger shrink-0" />;
    if (type === "MICRO_SAVINGS") return <TrendingUp size={16} className="text-success shrink-0" />;
    return <Info size={16} className="text-amber-400 shrink-0" />;
  }

  function getVariant(type: string) {
    if (type === "GUARDIAN_ALERT") return "outline";
    return "primary";
  }

  function handleAction(nudge: Nudge) {
    if (nudge.id === "dry_spell_period" || nudge.id === "low_savings_period") {
      router.push("/schemes");
    } else if (nudge.id === "welcome_log") {
      document.getElementById("pdf-upload")?.scrollIntoView({ behavior: "smooth", block: "center" });
    } else if (nudge.id === "debt_track_period" || nudge.id === "high_spend_period" || nudge.id.startsWith("tracked_debt_")) {
      // Open Robust Deep Dive Modal
      setActiveInsight(nudge);
      setInsightLoading(true);
      setInsightData(null);
      
      if (nudge.id === "debt_track_period") {
        transactionsApi.list(accessToken!, { category: "DEBT_REPAYMENT", start_date, end_date })
          .then((res) => setInsightData(res.transactions))
          .finally(() => setInsightLoading(false));
      } else if (nudge.id.startsWith("tracked_debt_")) {
        // Extract the entity name from the title: "Debt Progress: {entity}"
        const entity = nudge.title.replace("Debt Progress: ", "");
        transactionsApi.list(accessToken!, { type: "EXPENSE", query: entity, start_date, end_date })
          .then((res) => setInsightData(res.transactions))
          .finally(() => setInsightLoading(false));
      } else {
        transactionsApi.list(accessToken!, { type: "EXPENSE", start_date, end_date })
          .then((res) => setInsightData(res.transactions.slice(0, 3))) // top 3 recent/largest
          .finally(() => setInsightLoading(false));
      }
    }
  }

  function closeInsight() {
    setActiveInsight(null);
  }


  const [trackModalOpen, setTrackModalOpen] = useState(false);
  const [trackEntity, setTrackEntity] = useState("");
  const [trackAmount, setTrackAmount] = useState("");
  const [trackLoading, setTrackLoading] = useState(false);

  async function handleTrackDebt() {
    if (!accessToken || !trackEntity || !trackAmount) return;
    setTrackLoading(true);
    try {
      await guardianApi.trackDebt(accessToken, trackEntity, parseFloat(trackAmount));
      setTrackModalOpen(false);
      setTrackEntity("");
      setTrackAmount("");
      // Force reload of nudges
      setLoading(true);
      const res = await guardianApi.getNudges(accessToken, start_date, end_date);
      setNudges(res.nudges);
    } catch (e) {
      console.error("Failed to track debt:", e);
    } finally {
      setTrackLoading(false);
    }
  }

  return (
    <SurfaceCard className="p-5 flex flex-col gap-4 border-accent/20 bg-accent/[0.02]">
      <div className="flex items-center justify-between border-b border-border pb-3">
        <h2 className="font-outfit font-semibold text-lg text-text-primary flex items-center gap-2">
          <ShieldAlert size={20} className="text-accent" />
          Guardian Insights
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setTrackModalOpen(true)}
            className="text-xs font-medium bg-white/5 hover:bg-white/10 text-text-secondary hover:text-text-primary px-2 py-1 rounded transition-colors"
          >
            + Track Debt
          </button>
          {!loading && nudges.length > 0 && (
            <Badge variant="warning">{nudges.length} New</Badge>
          )}
        </div>
      </div>

      <div className="flex flex-col gap-4 min-h-[200px]">
        {loading ? (
          <div className="flex flex-col gap-4 animate-pulse">
            <div className="h-32 w-full bg-[#111] border border-border rounded-lg" />
            <div className="h-32 w-full bg-[#111] border border-border rounded-lg" />
          </div>
        ) : nudges.length === 0 ? (
          <div className="flex flex-col items-center justify-center flex-1 text-center gap-2 text-text-secondary h-full py-8">
            <ShieldAlert size={32} className="opacity-20 mb-2" />
            <p className="text-sm">You are all caught up!</p>
            <p className="text-xs opacity-70">No new insights right now.</p>
          </div>
        ) : (
          nudges.map((nudge) => (
            <div key={nudge.id} className="flex flex-col gap-3 p-4 rounded-lg bg-[#111] border border-border transition-all hover:border-white/10">
              <div className="flex items-start justify-between gap-2">
                <span className="font-medium text-sm text-text-primary">{nudge.title}</span>
                {getIcon(nudge.type)}
              </div>
              <p className="text-xs text-text-secondary leading-relaxed">
                {nudge.message}
              </p>
              <div className="flex gap-2 mt-1">
                <Button size="sm" variant={getVariant(nudge.type)} className="w-full" onClick={() => handleAction(nudge)}>
                  {nudge.actionLabel}
                </Button>
                {nudge.type === "MICRO_SAVINGS" && (
                  <Button size="sm" variant="ghost" className="w-full" onClick={() => setNudges(n => n.filter(x => x.id !== nudge.id))}>
                    Dismiss
                  </Button>
                )}
              </div>
            </div>
          ))
        )}
      </div>


      {/* Deep Dive Modal */}
      {activeInsight && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
          onClick={(e) => {
            if (e.target === e.currentTarget) closeInsight();
          }}
        >
          <SurfaceCard className="relative w-full max-w-md p-6 flex flex-col gap-5 shadow-2xl animate-fade-up">
            <button
              onClick={closeInsight}
              className="absolute top-4 right-4 text-text-secondary hover:text-text-primary transition-colors"
              aria-label="Close"
            >
              <X size={18} />
            </button>
            
            <div className="flex flex-col gap-2 border-b border-border pb-4">
              <div className="flex items-center gap-2">
                {getIcon(activeInsight.type)}
                <h2 className="font-outfit font-semibold text-lg text-text-primary">
                  {activeInsight.title}
                </h2>
              </div>
              <p className="text-text-secondary text-sm">
                {activeInsight.message}
              </p>
            </div>

            <div className="flex flex-col gap-3 min-h-[150px]">
              {insightLoading ? (
                <div className="flex items-center justify-center h-full text-text-secondary">
                  <svg className="animate-spin h-5 w-5 text-accent" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                </div>
              ) : insightData && insightData.length > 0 ? (
                <div className="flex flex-col gap-2">
                  <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1">
                    {activeInsight.id === "debt_track_period" 
                      ? "Recent Debt Repayments" 
                      : activeInsight.id.startsWith("tracked_debt_")
                      ? "Matching Payments"
                      : "Top Recent Expenses"}
                  </span>
                  {insightData.map((tx) => (
                    <div key={tx.id} className="flex justify-between items-center p-3 rounded-lg bg-[#111] border border-border">
                      <div className="flex flex-col overflow-hidden">
                        <span className="text-sm font-medium text-text-primary truncate">{tx.description || tx.category}</span>
                        <span className="text-xs text-text-secondary">{tx.occurred_at || tx.created_at.split("T")[0]}</span>
                      </div>
                      <span className="font-mono text-sm text-text-primary shrink-0 pl-3">
                        ₹{tx.amount.toFixed(0)}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex items-center justify-center h-full text-text-secondary text-sm">
                  No matching transactions found.
                </div>
              )}
            </div>
            <Button className="w-full" variant="primary" onClick={closeInsight}>
              Got it
            </Button>
          </SurfaceCard>
        </div>
      )}

      {/* Track Specific Debt Modal */}
      {trackModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
          onClick={(e) => {
            if (e.target === e.currentTarget) setTrackModalOpen(false);
          }}
        >
          <SurfaceCard className="relative w-full max-w-md p-6 flex flex-col gap-5 shadow-2xl animate-fade-up">
            <button
              onClick={() => setTrackModalOpen(false)}
              className="absolute top-4 right-4 text-text-secondary hover:text-text-primary transition-colors"
            >
              <X size={18} />
            </button>
            <div className="flex flex-col gap-1">
              <h2 className="font-outfit font-semibold text-lg text-text-primary">
                Track Specific Debt
              </h2>
              <p className="text-text-secondary text-sm">
                Enter the name of the entity or person you owe. We will skim your transactions to track repayments automatically.
              </p>
            </div>
            
            <div className="flex flex-col gap-3">
              <input
                type="text"
                placeholder="Entity Name (e.g. Slice Bank, Ramesh)"
                value={trackEntity}
                onChange={(e) => setTrackEntity(e.target.value)}
                className="w-full bg-[#111] border border-white/10 text-text-primary text-sm p-3 rounded-lg focus:outline-none focus:border-accent"
              />
              <input
                type="number"
                placeholder="Total Debt Amount (₹)"
                value={trackAmount}
                onChange={(e) => setTrackAmount(e.target.value)}
                className="w-full bg-[#111] border border-white/10 text-text-primary text-sm p-3 rounded-lg focus:outline-none focus:border-accent"
              />
            </div>
            
            <Button
              className="w-full"
              variant="primary"
              onClick={handleTrackDebt}
              disabled={trackLoading || !trackEntity || !trackAmount}
            >
              {trackLoading ? "Saving..." : "Start Tracking"}
            </Button>
          </SurfaceCard>
        </div>
      )}
    </SurfaceCard>
  );
}

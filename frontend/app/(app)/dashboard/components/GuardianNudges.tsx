"use client";

import { SurfaceCard } from "@/components/ui/SurfaceCard";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ShieldAlert, TrendingUp } from "lucide-react";

const NUDGES = [
  {
    id: "n1",
    type: "GUARDIAN_ALERT",
    title: "High Spending Detected",
    message: "You've spent 60% of this week's income on discretionary items.",
    actionLabel: "Review",
  },
  {
    id: "n2",
    type: "MICRO_SAVINGS",
    title: "Save ₹34 Today",
    message: "You earned ₹850 today. Consider saving 4% toward your emergency fund.",
    actionLabel: "Save Now",
  }
];

export function GuardianNudges() {
  return (
    <SurfaceCard className="p-5 flex flex-col gap-4 border-accent/20 bg-accent/[0.02]">
      <div className="flex items-center justify-between border-b border-border pb-3">
        <h2 className="font-outfit font-semibold text-lg text-text-primary flex items-center gap-2">
          <ShieldAlert size={20} className="text-accent" />
          Guardian Insights
        </h2>
        <Badge variant="warning">2 New</Badge>
      </div>

      <div className="flex flex-col gap-4">
        {NUDGES.map((nudge) => (
          <div key={nudge.id} className="flex flex-col gap-3 p-4 rounded-lg bg-[#111] border border-border">
            <div className="flex items-start justify-between gap-2">
              <span className="font-medium text-sm text-text-primary">{nudge.title}</span>
              {nudge.type === "GUARDIAN_ALERT" ? (
                <ShieldAlert size={16} className="text-danger shrink-0" />
              ) : (
                <TrendingUp size={16} className="text-success shrink-0" />
              )}
            </div>
            <p className="text-xs text-text-secondary leading-relaxed">
              {nudge.message}
            </p>
            <div className="flex gap-2 mt-1">
              <Button size="sm" variant={nudge.type === "GUARDIAN_ALERT" ? "outline" : "primary"} className="w-full">
                {nudge.actionLabel}
              </Button>
              {nudge.type === "MICRO_SAVINGS" && (
                <Button size="sm" variant="ghost" className="w-full">Dismiss</Button>
              )}
            </div>
          </div>
        ))}
      </div>
    </SurfaceCard>
  );
}

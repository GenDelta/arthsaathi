"use client";

import { SurfaceCard } from "@/components/ui/SurfaceCard";
import { ArrowUpRight, ArrowDownRight, Wallet } from "lucide-react";

const STATS = [
  { label: "Total Income", amount: "₹12,450", trend: "+4%", icon: ArrowUpRight, color: "text-success" },
  { label: "Total Expenses", amount: "₹3,200", trend: "-1%", icon: ArrowDownRight, color: "text-danger" },
  { label: "Net Savings", amount: "₹9,250", trend: "Goal: ₹10k", icon: Wallet, color: "text-accent" },
];

export function OverviewCards() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {STATS.map((stat, idx) => (
        <SurfaceCard key={idx} className="flex flex-col gap-3 p-5">
          <div className="flex items-center justify-between">
            <span className="text-text-secondary text-sm font-medium">{stat.label}</span>
            <div className={`p-2 rounded-full bg-[#111] ${stat.color}`}>
              <stat.icon size={16} />
            </div>
          </div>
          <div>
            <div className="font-mono text-3xl text-text-primary tracking-tight">
              {stat.amount}
            </div>
            <div className="text-xs text-text-secondary mt-1 font-medium">
              {stat.trend} this month
            </div>
          </div>
        </SurfaceCard>
      ))}
    </div>
  );
}

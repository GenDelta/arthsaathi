"use client";

import { SurfaceCard } from "@/components/ui/SurfaceCard";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";

const TRANSACTIONS = [
  { id: 1, title: "Zomato deliveries", category: "GIG_WAGE", amount: "₹850", type: "INCOME", date: "Today, 6:30 PM" },
  { id: 2, title: "Lunch", category: "FOOD", amount: "₹120", type: "EXPENSE", date: "Yesterday, 1:00 PM" },
  { id: 3, title: "Swiggy deliveries", category: "GIG_WAGE", amount: "₹1,200", type: "INCOME", date: "Sep 25, 8:00 PM" },
  { id: 4, title: "Auto rickshaw", category: "TRANSPORT", amount: "₹45", type: "EXPENSE", date: "Sep 25, 9:00 AM" },
];

export function RecentTransactions() {
  return (
    <SurfaceCard className="p-0 overflow-hidden">
      <div className="flex items-center justify-between p-5 border-b border-border">
        <h3 className="font-outfit font-semibold text-text-primary text-lg">Recent Activity</h3>
        <Button variant="ghost" size="sm">View All</Button>
      </div>
      <div className="flex flex-col divide-y divide-border">
        {TRANSACTIONS.map((tx) => (
          <div key={tx.id} className="flex items-center justify-between p-5 hover:bg-[#111] transition-colors cursor-default">
            <div className="flex items-center gap-4">
              <div className={`p-2.5 rounded-full ${tx.type === "INCOME" ? "bg-success/10 text-success" : "bg-danger/10 text-danger"}`}>
                {tx.type === "INCOME" ? <ArrowUpRight size={18} /> : <ArrowDownRight size={18} />}
              </div>
              <div className="flex flex-col">
                <span className="font-medium text-text-primary text-sm">{tx.title}</span>
                <span className="text-xs text-text-secondary mt-0.5">{tx.date}</span>
              </div>
            </div>
            <div className="flex flex-col items-end gap-1">
              <span className={`font-mono font-medium ${tx.type === "INCOME" ? "text-success" : "text-text-primary"}`}>
                {tx.type === "INCOME" ? "+" : "-"}{tx.amount}
              </span>
              <Badge variant={tx.type === "INCOME" ? "success" : "default"} className="text-[10px] px-2 py-0">
                {tx.category.replace("_", " ")}
              </Badge>
            </div>
          </div>
        ))}
      </div>
    </SurfaceCard>
  );
}

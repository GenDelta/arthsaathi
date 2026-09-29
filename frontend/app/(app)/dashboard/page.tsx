"use client";

import { DashboardHeader } from "./components/DashboardHeader";
import { OverviewCards } from "./components/OverviewCards";
import { GuardianNudges } from "./components/GuardianNudges";
import { RecentTransactions } from "./components/RecentTransactions";

export default function DashboardPage() {
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
          <GuardianNudges />
        </div>

        {/* Mobile: Stats appear SECOND (order-2) / Desktop: Main area (order-1) */}
        <div className="order-2 lg:order-1 lg:col-span-2 space-y-6">
          <OverviewCards />
          <RecentTransactions />
        </div>

      </div>
    </div>
  );
}

"use client";

import { SchemeCard } from "./components/SchemeCard";
import { Badge } from "@/components/ui/Badge";
import { Filter } from "lucide-react";

const MOCK_SCHEMES = [
  { 
    id: "s1", 
    name: "PM-SYM (Pradhan Mantri Shram Yogi Maandhan)", 
    match: 91, 
    summary: "Monthly pension of ₹3,000 after age 60 for gig workers and unorganized sector laborers.",
    tags: ["Pension", "Gig Worker"]
  },
  { 
    id: "s2", 
    name: "PM-KISAN", 
    match: 84, 
    summary: "₹6,000 per year direct income support for small and marginal farmers, paid in three installments.",
    tags: ["Agriculture", "Income Support"]
  },
  { 
    id: "s3", 
    name: "PMSBY (Pradhan Mantri Suraksha Bima Yojana)", 
    match: 79, 
    summary: "Accidental death and disability insurance of ₹2 lakh at just ₹20 per year premium.",
    tags: ["Insurance", "Low Premium"]
  },
];

export default function SchemesPage() {
  return (
    <div className="flex flex-col gap-6 w-full animate-fade-up">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-border pb-6">
        <div className="flex flex-col gap-1">
          <h1 className="font-outfit text-3xl font-bold text-text-primary">
            Eligible Schemes
          </h1>
          <p className="text-text-secondary text-sm">
            Based on your occupation (Gig Worker) and income.
          </p>
        </div>
        <button className="flex items-center gap-2 text-sm text-text-secondary hover:text-text-primary transition-colors px-3 py-1.5 border border-border rounded-lg bg-[#0A0A0A]">
          <Filter size={16} /> Filters
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {MOCK_SCHEMES.map((scheme) => (
          <SchemeCard key={scheme.id} scheme={scheme} />
        ))}
      </div>
    </div>
  );
}

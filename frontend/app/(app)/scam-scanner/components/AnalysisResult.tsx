"use client";

import { SurfaceCard } from "@/components/ui/SurfaceCard";
import { Badge } from "@/components/ui/Badge";
import { ShieldAlert, ShieldCheck, Info } from "lucide-react";
import { ClauseMatchResult } from "@/lib/api-client";
import ReactMarkdown from "react-markdown";

interface AnalysisResultProps {
  riskLevel: string | null;
  riskSummary: string | null;
  matchedClauses: ClauseMatchResult[];
}

export function AnalysisResult({ riskLevel, riskSummary, matchedClauses }: AnalysisResultProps) {
  const isHighRisk = riskLevel === "HIGH";
  const isMediumRisk = riskLevel === "MEDIUM";
  
  const borderColor = isHighRisk ? "border-danger/30" : isMediumRisk ? "border-warning/30" : "border-success/30";
  const bgColor = isHighRisk ? "bg-danger/[0.02]" : isMediumRisk ? "bg-warning/[0.02]" : "bg-success/[0.02]";
  const iconColor = isHighRisk ? "text-danger" : isMediumRisk ? "text-warning" : "text-success";
  
  return (
    <SurfaceCard className={`flex flex-col gap-6 ${borderColor} ${bgColor}`}>
      <div className="flex flex-col gap-2 pb-4 border-b border-border">
        <div className="flex justify-between items-start">
          <h2 className="text-xl font-outfit font-semibold text-text-primary flex items-center gap-2">
            {isHighRisk || isMediumRisk ? (
              <ShieldAlert className={iconColor} size={24} />
            ) : (
              <ShieldCheck className={iconColor} size={24} />
            )}
            {isHighRisk ? "High Risk Detected" : isMediumRisk ? "Moderate Risk Detected" : "Low Risk - Looks Safe"}
          </h2>
          <Badge variant={isHighRisk ? "danger" : isMediumRisk ? "warning" : "success"}>
            {riskLevel}
          </Badge>
        </div>
        <div className="text-sm text-text-secondary leading-relaxed space-y-2 [&>ul]:list-disc [&>ul]:pl-5 [&>ol]:list-decimal [&>ol]:pl-5">
          <ReactMarkdown>
            {riskSummary || "No specific risks were flagged in this document."}
          </ReactMarkdown>
        </div>
      </div>

      {matchedClauses && matchedClauses.length > 0 && (
        <div className="flex flex-col gap-4">
          <h3 className="font-medium text-sm text-text-primary">Flagged Content</h3>
          
          {matchedClauses.map((clause, idx) => (
            <div key={idx} className="flex flex-col gap-3 p-4 bg-[#111] border border-border/50 rounded-lg">
              <div className="flex items-center justify-between">
                <Badge variant={isHighRisk ? "danger" : "warning"} className="text-[10px]">
                  {clause.clause_category}
                </Badge>
              </div>
              <div className="flex gap-2 items-start mt-1 text-text-secondary text-sm">
                <Info size={16} className="shrink-0 mt-0.5" />
                <p>{clause.explanation}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </SurfaceCard>
  );
}

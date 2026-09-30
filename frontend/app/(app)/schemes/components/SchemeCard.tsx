"use client";

import { useState } from "react";
import { SurfaceCard } from "@/components/ui/SurfaceCard";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ArrowRight, Building2, CheckCircle, X, Info } from "lucide-react";
import { SchemeMatch } from "@/lib/api-client";

export function SchemeCard({ scheme }: { scheme: SchemeMatch }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <SurfaceCard className="flex flex-col h-full p-5 gap-4 relative overflow-hidden">
        {scheme.confidence_score && (
          <div className="absolute top-4 right-4 flex flex-col items-center justify-center w-12 h-12 rounded-full border-2 border-accent bg-accent/10">
            <span className="font-mono font-bold text-accent text-sm">{scheme.confidence_score}%</span>
          </div>
        )}
        <div className="flex flex-col gap-3 pr-12">
          <Badge variant="outline" className="text-[10px] w-fit flex gap-1 items-center bg-accent/5">
            <Building2 size={12} /> {scheme.ministry}
          </Badge>
          <h3 className="font-outfit font-semibold text-lg text-text-primary leading-tight">
            {scheme.title}
          </h3>
        </div>

        <p className="text-sm text-text-secondary leading-relaxed font-medium">
          {scheme.benefit_summary}
        </p>
        
        <div className="bg-[#111] border border-border p-3 rounded-lg flex flex-col gap-2 flex-1">
           <p className="text-xs text-text-muted flex gap-2 items-start"><CheckCircle size={14} className="text-accent shrink-0 mt-0.5" /> <span className="flex-1">{scheme.eligibility}</span></p>
        </div>

        <div className="flex gap-2 pt-2 mt-auto">
          <Button variant="primary" className="flex-1" onClick={() => setIsOpen(true)}>
            View Details & Apply <ArrowRight size={16} />
          </Button>
        </div>
      </SurfaceCard>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-surface border border-border rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto flex flex-col shadow-2xl">
            <div className="sticky top-0 bg-surface/90 backdrop-blur-md border-b border-border p-4 flex items-center justify-between z-10">
              <h2 className="font-outfit font-bold text-xl text-text-primary flex-1 pr-4">{scheme.title}</h2>
              <button 
                onClick={() => setIsOpen(false)}
                className="p-2 hover:bg-white/10 rounded-full transition-colors text-text-secondary hover:text-text-primary"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6 flex flex-col gap-8">
              <div className="flex flex-col gap-2">
                <div className="flex items-center gap-2 text-text-primary">
                  <Building2 size={18} className="text-accent" />
                  <span className="font-semibold">Issuing Authority</span>
                </div>
                <p className="text-text-secondary ml-7">{scheme.ministry}</p>
              </div>

              <div className="flex flex-col gap-2">
                <div className="flex items-center gap-2 text-text-primary">
                  <Info size={18} className="text-accent" />
                  <span className="font-semibold">Benefits Summary</span>
                </div>
                <p className="text-text-secondary ml-7 leading-relaxed">{scheme.benefit_summary}</p>
              </div>

              <div className="flex flex-col gap-2">
                <div className="flex items-center gap-2 text-text-primary">
                  <CheckCircle size={18} className="text-accent" />
                  <span className="font-semibold">Why You Qualify (Eligibility)</span>
                </div>
                <p className="text-text-secondary ml-7 leading-relaxed">{scheme.eligibility}</p>
              </div>

              <div className="flex flex-col gap-3 p-5 rounded-xl bg-accent/5 border border-accent/20">
                <h3 className="font-outfit font-semibold text-accent text-lg">Application Steps</h3>
                <div className="text-text-primary leading-relaxed text-sm whitespace-pre-wrap">
                  {scheme.application_steps}
                </div>
              </div>
            </div>
            
            <div className="p-4 border-t border-border bg-[#111] flex justify-end gap-3 rounded-b-2xl">
              <Button variant="outline" onClick={() => setIsOpen(false)}>Close</Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}


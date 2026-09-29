"use client";

import { SurfaceCard } from "@/components/ui/SurfaceCard";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { CheckCircle2, ArrowRight } from "lucide-react";

interface SchemeCardProps {
  scheme: {
    name: string;
    match: number;
    summary: string;
    tags: string[];
  };
}

export function SchemeCard({ scheme }: SchemeCardProps) {
  return (
    <SurfaceCard className="flex flex-col h-full p-5 gap-4">
      <div className="flex items-start justify-between gap-2">
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap gap-2">
            {scheme.tags.map(tag => (
              <Badge key={tag} variant="outline" className="text-[10px]">
                {tag}
              </Badge>
            ))}
          </div>
          <h3 className="font-outfit font-semibold text-lg text-text-primary leading-tight">
            {scheme.name}
          </h3>
        </div>
        <div className="flex flex-col items-center justify-center shrink-0 w-12 h-12 rounded-full border-2 border-accent bg-accent/10">
          <span className="font-mono font-bold text-accent text-sm">{scheme.match}%</span>
        </div>
      </div>

      <p className="text-sm text-text-secondary leading-relaxed flex-1">
        {scheme.summary}
      </p>

      <div className="flex gap-2 pt-2 border-t border-border mt-auto">
        <Button variant="primary" className="flex-1">
          Apply <ArrowRight size={16} />
        </Button>
        <Button variant="outline" className="px-3" aria-label="Dismiss">
          Dismiss
        </Button>
      </div>
    </SurfaceCard>
  );
}

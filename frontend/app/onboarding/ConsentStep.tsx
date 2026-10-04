"use client";

import { useState } from "react";
import { SurfaceCard } from "@/components/ui/SurfaceCard";
import { Button } from "@/components/ui/Button";
import { ShieldCheck, ChevronDown, ChevronUp } from "lucide-react";

interface ConsentStepProps {
  onComplete: (grantedPurposes: string[]) => void;
  loading: boolean;
}

export function ConsentStep({ onComplete, loading }: ConsentStepProps) {
  const [statement, setStatement] = useState<boolean | null>(null);
  const [voice, setVoice] = useState<boolean | null>(null);
  const [expanded, setExpanded] = useState(false);

  // Can continue if all required/optional decisions are made (true/false)
  // Actually, only statement processing is required to be decided to move on, but we want a choice for all.
  const canContinue = statement !== null && voice !== null;

  return (
    <SurfaceCard className="max-w-2xl mx-auto p-6 flex flex-col gap-6 bg-[#0A0A0A]">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-500">
          <ShieldCheck size={24} />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-text-primary">Data Privacy & Consent</h2>
          <p className="text-sm text-text-secondary mt-1">
            ArthSaathi needs permission to process your data safely.
          </p>
        </div>
      </div>

      <div className="bg-white/[0.02] border border-white/10 rounded-lg p-4">
        <button 
          onClick={() => setExpanded(!expanded)}
          className="flex items-center justify-between w-full text-left"
        >
          <span className="text-sm font-medium text-text-primary">Read the full Privacy Notice</span>
          {expanded ? <ChevronUp size={16} className="text-text-secondary" /> : <ChevronDown size={16} className="text-text-secondary" />}
        </button>
        {expanded && (
          <div className="mt-4 text-xs text-text-secondary space-y-3 leading-relaxed">
            <p><strong className="text-text-primary">WHAT WE COLLECT</strong><br/>
            When you upload a bank statement, we read the transactions inside it (Date, amount, and description) and your account holder name to check the statement is yours. We do NOT keep a copy of the PDF or the image.</p>
            
            <p><strong className="text-text-primary">WHY WE USE IT</strong><br/>
            To show you your income and spending, alert you when spending is unusually high, check if a lender you paid is flagged as predatory, and suggest government schemes that match your profile.</p>
            
            <p><strong className="text-text-primary">WHO CAN SEE IT</strong><br/>
            Only you. We never sell or share your personal data.</p>
            
            <p><strong className="text-text-primary">HOW LONG WE KEEP IT</strong><br/>
            Until you delete it or withdraw consent.</p>
            
            <p><strong className="text-text-primary">HOW TO DELETE</strong><br/>
            Go to Profile &gt; Privacy &amp; Permissions &gt; Delete My Financial Data.</p>
            
            <p><strong className="text-text-primary">PASSWORDS FOR ENCRYPTED PDFs</strong><br/>
            If your PDF has a password, we use it only to open the file in memory. We do not store the password.</p>
          </div>
        )}
      </div>

      <div className="space-y-4">
        <div className="flex items-start gap-4">
          <div className="flex-1">
            <p className="text-sm font-medium text-text-primary">Process Bank Statements <span className="text-amber-500 text-xs ml-2">REQUIRED</span></p>
            <p className="text-xs text-text-secondary mt-1">Allows ArthSaathi to read uploaded PDFs to track your spending and check for predatory lenders.</p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Button size="sm" variant={statement === true ? "primary" : "outline"} onClick={() => setStatement(true)}>Allow</Button>
            <Button size="sm" variant={statement === false ? "primary" : "outline"} onClick={() => setStatement(false)}>Deny</Button>
          </div>
        </div>

        <div className="flex items-start gap-4">
          <div className="flex-1">
            <p className="text-sm font-medium text-text-primary">Process Voice Logs <span className="text-text-secondary text-xs ml-2">OPTIONAL</span></p>
            <p className="text-xs text-text-secondary mt-1">Allows logging transactions by speaking to the app. Audio/text is sent to our AI model.</p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Button size="sm" variant={voice === true ? "primary" : "outline"} onClick={() => setVoice(true)}>Allow</Button>
            <Button size="sm" variant={voice === false ? "primary" : "outline"} onClick={() => setVoice(false)}>Deny</Button>
          </div>
        </div>


      </div>

      <div className="pt-4 border-t border-white/10 flex justify-end">
        <Button 
          variant="primary" 
          disabled={!canContinue || loading} 
          onClick={() => {
            const purposes = [];
            if (statement) purposes.push("STATEMENT_PROCESSING");
            if (voice) purposes.push("VOICE_PROCESSING");
            onComplete(purposes);
          }}
        >
          {loading ? "Saving..." : "Continue"}
        </Button>
      </div>
    </SurfaceCard>
  );
}

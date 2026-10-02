"use client";

import { UploadArea } from "./components/UploadArea";
import { AnalysisResult } from "./components/AnalysisResult";
import { useState, useEffect } from "react";
import { scamApi, ScanStatusResponse } from "@/lib/api-client";
import { useAuthStore } from "@/store/useAuthStore";
import { Button } from "@/components/ui/Button";

export default function ScamScannerPage() {
  const { accessToken } = useAuthStore();
  const [status, setStatus] = useState<"IDLE" | "EXTRACTING" | "VERIFY" | "ANALYZING" | "RESULT">("IDLE");
  const [docId, setDocId] = useState<string | null>(null);
  const [extractedText, setExtractedText] = useState("");
  const [result, setResult] = useState<ScanStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const handleUpload = async (file: File) => {
    if (!accessToken) return;
    try {
      setStatus("EXTRACTING");
      setError(null);
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      const res = await scamApi.initScan(file, accessToken);
      setDocId(res.document_id);
      setExtractedText(res.extracted_text || "");
      setStatus("VERIFY");
    } catch (err: any) {
      setError(err.message || "Upload failed");
      setStatus("IDLE");
    }
  };

  const handleVerify = async () => {
    if (!accessToken || !docId) return;
    try {
      setStatus("ANALYZING");
      await scamApi.verifyScan(docId, extractedText, accessToken);
      pollResult(docId);
    } catch (err: any) {
      setError(err.message || "Verification failed");
      setStatus("VERIFY");
    }
  };

  const pollResult = (id: string) => {
    if (!accessToken) return;
    const interval = setInterval(async () => {
      try {
        const res = await scamApi.getScanStatus(id, accessToken);
        if (res.status === "ANALYZED" || res.status === "FAILED") {
          clearInterval(interval);
          setResult(res);
          setStatus("RESULT");
        }
      } catch (err) {
        // Ignore polling errors to keep trying
      }
    }, 2000);
  };

  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState<ScanStatusResponse[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const loadHistory = async () => {
    if (!accessToken) return;
    setLoadingHistory(true);
    try {
      const docs = await scamApi.getHistory(accessToken);
      setHistory(docs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    if (showHistory) {
      loadHistory();
    }
  }, [showHistory]);

  return (
    <div className="flex flex-col gap-6 w-full max-w-5xl mx-auto animate-fade-up">
      <div className="flex flex-col gap-1 text-center mb-4 relative">
        <h1 className="font-outfit text-3xl font-bold text-text-primary">
          Scam Scanner
        </h1>
        <p className="text-text-secondary text-sm">
          Upload a message screenshot, contract, or email to check for fraudulent/predatory clauses.
        </p>
        <button 
          onClick={() => setShowHistory(!showHistory)}
          className="absolute right-0 top-0 text-sm text-accent hover:text-accent-hover underline decoration-accent/30 underline-offset-4 transition-colors"
        >
          {showHistory ? "Back to Scan" : "History"}
        </button>
      </div>
      
      {error && (
        <div className="p-4 bg-danger/10 border border-danger/30 text-danger rounded-lg text-sm">
          {error}
        </div>
      )}

      {showHistory ? (
        <div className="flex flex-col gap-4">
          {loadingHistory ? (
            <div className="flex justify-center p-8"><div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" /></div>
          ) : history.length === 0 ? (
            <p className="text-text-secondary text-center p-8 bg-[#0A0A0A] border border-border rounded-xl">No historical scans found.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {history.map(doc => (
                <div key={doc.document_id} className="p-4 bg-[#0A0A0A] border border-border rounded-xl flex flex-col gap-2 cursor-pointer hover:border-[#444] transition-colors"
                  onClick={async () => {
                    // Quick way to load a past result
                    if (!accessToken) return;
                    setShowHistory(false);
                    setStatus("ANALYZING");
                    try {
                      const res = await scamApi.getScanStatus(doc.document_id, accessToken);
                      setResult(res);
                      setStatus("RESULT");
                    } catch (e) {
                      setStatus("IDLE");
                    }
                  }}
                >
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-mono text-text-secondary">{doc.document_id.split("-")[0]}</span>
                    <span className={`text-xs font-bold px-2 py-1 rounded-md ${
                      doc.risk_level === 'HIGH' ? 'bg-danger/20 text-danger' :
                      doc.risk_level === 'MEDIUM' ? 'bg-[#F59E0B]/20 text-[#F59E0B]' :
                      doc.risk_level === 'LOW' ? 'bg-success/20 text-success' : 'bg-[#222] text-text-secondary'
                    }`}>
                      {doc.risk_level || doc.status}
                    </span>
                  </div>
                  <p className="text-sm text-text-primary line-clamp-2 mt-1">{doc.risk_summary || "No summary available."}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <>
          {status === "IDLE" && <UploadArea onUpload={handleUpload} />}
          
          {status === "EXTRACTING" && (
        <div className="flex flex-col items-center justify-center p-12 border border-border bg-[#0A0A0A] rounded-xl gap-4">
          <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          <p className="text-text-primary font-medium animate-pulse">Extracting text via OCR...</p>
        </div>
      )}

      {status === "VERIFY" && (
        <div className="flex flex-col gap-4 p-6 border border-border bg-[#0A0A0A] rounded-xl">
          <h3 className="text-lg font-outfit font-semibold text-text-primary">Verify Text</h3>
          <p className="text-sm text-text-secondary">Please review and correct any OCR errors before we analyze the document.</p>
          <textarea 
            value={extractedText}
            onChange={(e) => setExtractedText(e.target.value)}
            className="w-full h-48 bg-[#111] border border-border rounded-lg p-3 text-sm text-text-primary focus:outline-none focus:border-accent"
          />
          <div className="flex justify-end gap-3 mt-2">
            <Button variant="outline" onClick={() => setStatus("IDLE")}>Cancel</Button>
            <Button onClick={handleVerify}>Run Scam Analysis</Button>
          </div>
        </div>
      )}

      {status === "ANALYZING" && (
        <div className="flex flex-col items-center justify-center p-12 border border-border bg-[#0A0A0A] rounded-xl gap-4">
          <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          <p className="text-text-primary font-medium animate-pulse">Running AI Scam Analysis...</p>
        </div>
      )}

      {status === "RESULT" && result && (
        <div className="space-y-6">
          {result.status === "FAILED" ? (
             <div className="p-4 bg-danger/10 border border-danger/30 text-danger rounded-lg text-sm">
               Analysis failed: {result.error_message}
             </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
              {previewUrl && (
                <div className="rounded-xl border border-border bg-[#0A0A0A] p-2 sticky top-24">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img 
                    src={previewUrl} 
                    alt="Scanned Document" 
                    className="w-full h-auto max-h-[60vh] object-contain rounded-lg"
                  />
                </div>
              )}
              <div className="flex flex-col gap-6">
                <AnalysisResult 
                  riskLevel={result.risk_level} 
                  riskSummary={result.risk_summary} 
                  matchedClauses={result.matched_clauses} 
                />
              </div>
            </div>
          )}
          <div className="flex justify-center">
            <button 
              onClick={() => { 
                setStatus("IDLE"); 
                setResult(null); 
                setExtractedText(""); 
                if (previewUrl) URL.revokeObjectURL(previewUrl);
                setPreviewUrl(null);
              }} 
              className="text-text-secondary text-sm hover:text-text-primary underline decoration-border underline-offset-4"
            >
              Scan another document
            </button>
          </div>
        </div>
      )}
        </>
      )}
    </div>
  );
}

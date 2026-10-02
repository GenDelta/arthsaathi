"use client";

import { useRef, useState, type DragEvent, type ChangeEvent } from "react";
import { SurfaceCard } from "@/components/ui/SurfaceCard";
import { Button } from "@/components/ui/Button";
import { UploadCloud, X, FileText, Lock, CheckCircle2 } from "lucide-react";
import { useAuthStore } from "@/store/useAuthStore";
import { transactionsApi } from "@/lib/api-client";

interface PdfUploadProps {
  /** Called after a successful upload so the parent can refresh lists. */
  onSuccess?: () => void;
}

function Spinner() {
  return (
    <svg
      className="animate-spin h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v8H4z"
      />
    </svg>
  );
}

export function PdfUpload({ onSuccess }: PdfUploadProps) {
  const { accessToken } = useAuthStore();

  const [open, setOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [password, setPassword] = useState("");
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successCount, setSuccessCount] = useState<number | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);

  function reset() {
    setFile(null);
    setPassword("");
    setError(null);
    setSuccessCount(null);
    setLoading(false);
  }

  function close() {
    setOpen(false);
    reset();
  }

  function pickFile(f: File) {
    if (f.type !== "application/pdf") {
      setError("Only PDF files are supported.");
      return;
    }
    setError(null);
    setFile(f);
  }

  function onInputChange(e: ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) pickFile(f);
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f) pickFile(f);
  }

  async function handleUpload() {
    if (!file || !accessToken) return;
    setLoading(true);
    setError(null);
    try {
      const res = await transactionsApi.uploadPdf(
        accessToken,
        file,
        password || undefined
      );
      setSuccessCount(res.inserted);
      onSuccess?.();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      {/* Trigger button */}
      <Button
        variant="outline"
        size="sm"
        onClick={() => setOpen(true)}
        className="gap-2"
      >
        <UploadCloud size={16} />
        Upload Bank Statement
      </Button>

      {/* Modal backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
          onClick={(e) => {
            if (e.target === e.currentTarget) close();
          }}
        >
          <SurfaceCard className="relative w-full max-w-md p-6 flex flex-col gap-5 shadow-2xl">
            {/* Close */}
            <button
              onClick={close}
              className="absolute top-4 right-4 text-text-secondary hover:text-text-primary transition-colors"
              aria-label="Close"
            >
              <X size={18} />
            </button>

            <div>
              <h2 className="font-outfit font-semibold text-lg text-text-primary">
                Upload Bank Statement
              </h2>
              <p className="text-text-secondary text-sm mt-1">
                We&apos;ll extract your transactions automatically.
              </p>
            </div>

            {/* Success state */}
            {successCount !== null ? (
              <div className="flex flex-col items-center gap-3 py-6 text-center">
                <CheckCircle2 size={40} className="text-emerald-400" />
                <p className="text-text-primary font-semibold text-lg">
                  {successCount} transaction{successCount !== 1 ? "s" : ""}{" "}
                  imported!
                </p>
                <Button variant="ghost" size="sm" onClick={close}>
                  Done
                </Button>
              </div>
            ) : (
              <>
                {/* Dropzone */}
                <div
                  onDragOver={(e) => {
                    e.preventDefault();
                    setDragging(true);
                  }}
                  onDragLeave={() => setDragging(false)}
                  onDrop={onDrop}
                  onClick={() => inputRef.current?.click()}
                  className={`
                    flex flex-col items-center justify-center gap-3
                    border-2 border-dashed rounded-xl p-8 cursor-pointer
                    transition-colors select-none
                    ${
                      dragging
                        ? "border-amber-400 bg-amber-400/5"
                        : "border-white/15 hover:border-white/30 bg-white/[0.03]"
                    }
                  `}
                >
                  <input
                    ref={inputRef}
                    type="file"
                    accept=".pdf,application/pdf"
                    className="hidden"
                    onChange={onInputChange}
                  />
                  {file ? (
                    <>
                      <FileText size={32} className="text-amber-400" />
                      <p className="text-text-primary text-sm font-medium text-center break-all">
                        {file.name}
                      </p>
                      <p className="text-text-secondary text-xs">
                        {(file.size / 1024).toFixed(1)} KB — click to replace
                      </p>
                    </>
                  ) : (
                    <>
                      <UploadCloud size={32} className="text-text-secondary" />
                      <p className="text-text-secondary text-sm text-center">
                        Drag & drop a PDF here, or{" "}
                        <span className="text-amber-400 font-medium">
                          click to browse
                        </span>
                      </p>
                    </>
                  )}
                </div>

                {/* Optional password */}
                <div className="flex items-center gap-2 bg-white/[0.04] rounded-lg px-3 py-2.5 border border-white/10">
                  <Lock size={14} className="text-text-secondary flex-shrink-0" />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="PDF password (optional)"
                    className="bg-transparent text-sm text-text-primary placeholder:text-text-secondary/60 flex-1 outline-none"
                  />
                </div>

                {error && (
                  <p className="text-red-400 text-sm text-center">{error}</p>
                )}

                <Button
                  variant="primary"
                  onClick={handleUpload}
                  disabled={!file || loading}
                  className="w-full gap-2"
                >
                  {loading ? (
                    <>
                      <Spinner /> Uploading…
                    </>
                  ) : (
                    <>
                      <UploadCloud size={16} /> Upload &amp; Import
                    </>
                  )}
                </Button>
              </>
            )}
          </SurfaceCard>
        </div>
      )}
    </>
  );
}

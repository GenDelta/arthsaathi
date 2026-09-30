"use client";

import { useState, useRef, type FormEvent } from "react";
import { Button } from "@/components/ui/Button";
import { Mic2, MicOff, CheckCircle2, Square } from "lucide-react";
import { useAuthStore } from "@/store/useAuthStore";
import { transactionsApi } from "@/lib/api-client";

interface VoiceLogProps {
  onSuccess?: () => void;
}

// Extend window for Web Speech API (not yet in TS lib)
declare global {
  interface Window {
    SpeechRecognition?: new () => SpeechRecognition;
    webkitSpeechRecognition?: new () => SpeechRecognition;
  }
}

function Spinner() {
  return (
    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
    </svg>
  );
}

export function VoiceLog({ onSuccess }: VoiceLogProps) {
  const { accessToken } = useAuthStore();

  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const recognitionRef = useRef<SpeechRecognition | null>(null);

  // ── Web Speech API ────────────────────────────────────────────────────────

  const committedRef = useRef(""); // text typed before recording started

  function startListening() {
    const SR = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    if (!SR) {
      setError("Speech recognition is not supported in this browser. Try Chrome.");
      return;
    }

    const recognition = new SR();
    recognition.lang = "en-IN";
    recognition.continuous = false;
    recognition.interimResults = true; // needed to get real-time updates

    // Save whatever the user had typed before speaking
    committedRef.current = text;

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      // Build the full transcript from all results so far (replaces, never appends)
      let finalTranscript = "";
      let interimTranscript = "";
      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
        } else {
          interimTranscript += result[0].transcript;
        }
      }
      // Replace text = pre-recording committed text + latest recognized speech
      const spoken = finalTranscript || interimTranscript;
      const prefix = committedRef.current ? `${committedRef.current} ` : "";
      setText(prefix + spoken);
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      if (event.error !== "aborted") {
        setError(`Mic error: ${event.error}`);
      }
      setListening(false);
    };

    recognition.onend = () => setListening(false);

    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
    setError(null);
  }

  function stopListening() {
    recognitionRef.current?.stop();
    setListening(false);
  }

  // ── Submit ────────────────────────────────────────────────────────────────

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || !accessToken) return;

    setLoading(true);
    setError(null);
    setToast(null);

    try {
      const res = await transactionsApi.voice(accessToken, trimmed);
      const tx = res.transaction;
      const amount = new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: tx.currency || "INR",
        maximumFractionDigits: 0,
      }).format(tx.amount);
      setToast(`Logged: ${tx.type === "INCOME" ? "+" : "−"}${amount} — ${tx.description}`);
      setText("");
      onSuccess?.();
      setTimeout(() => setToast(null), 4000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to log entry.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <form onSubmit={handleSubmit} className="flex items-center gap-2">

        {/* Mic toggle button */}
        <button
          type="button"
          onClick={listening ? stopListening : startListening}
          disabled={loading}
          title={listening ? "Stop recording" : "Start voice input"}
          className={`
            flex-shrink-0 p-2.5 rounded-full transition-all duration-200
            ${listening
              ? "bg-red-500/20 text-red-400 ring-2 ring-red-500/40 animate-pulse"
              : "bg-amber-400/10 text-amber-400 hover:bg-amber-400/20"
            }
            disabled:opacity-50
          `}
        >
          {listening ? <Square size={16} fill="currentColor" /> : <Mic2 size={16} />}
        </button>

        {/* Text input */}
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={listening ? "Listening…" : "Speak or type — e.g. Earned ₹500 from delivery"}
          disabled={loading}
          className="
            flex-1 bg-[#111] border border-white/10 rounded-lg
            px-3 py-2 text-sm text-text-primary
            placeholder:text-text-secondary/60
            focus:outline-none focus:border-amber-400/50
            disabled:opacity-50 transition-colors
          "
        />

        {/* Submit */}
        <Button
          type="submit"
          variant="primary"
          size="sm"
          disabled={!text.trim() || loading}
          className="gap-1.5 flex-shrink-0"
        >
          {loading ? <Spinner /> : null}
          {loading ? "Logging…" : "Log"}
        </Button>
      </form>

      {/* Feedback */}
      {listening && (
        <p className="text-amber-400 text-xs pl-12 flex items-center gap-1.5">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
          Recording — speak now, then press the mic to stop
        </p>
      )}
      {error && <p className="text-red-400 text-xs pl-12">{error}</p>}
      {toast && (
        <div className="flex items-center gap-2 pl-12 text-emerald-400 text-xs">
          <CheckCircle2 size={13} className="flex-shrink-0" />
          {toast}
        </div>
      )}
    </div>
  );
}

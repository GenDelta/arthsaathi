"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { onboardingApi } from "@/lib/api-client";
import { useAuthStore } from "@/store/useAuthStore";
import { SurfaceCard } from "@/components/ui/SurfaceCard";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { translations, Language } from "@/lib/i18n";
import { Loader2, Send } from "lucide-react";

export default function OnboardingPage() {
  const router = useRouter();
  const { accessToken, user, fetchMe } = useAuthStore();

  // Default to English — user can always switch later from dashboard
  const lang: Language = "en";
  const t = translations[lang].onboarding;

  const [messages, setMessages] = useState<{ role: "user" | "ai"; content: string }[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState<Record<string, any>>({});
  const [complete, setComplete] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const hasInitialized = useRef(false);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (!accessToken) {
      router.replace("/auth");
      return;
    }
    // Fire initial greeting from the agent exactly once (prevent Strict Mode double-fire)
    if (!hasInitialized.current) {
      hasInitialized.current = true;
      handleChat("");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleChat(msg: string) {
    if (!accessToken) return;
    setLoading(true);
    try {
      const res = await onboardingApi.chat(msg, lang, profile, accessToken);
      setProfile(res.current_profile);

      if (res.reply) {
        setMessages((prev) => [...prev, { role: "ai", content: res.reply }]);
      }

      if (res.is_complete) {
        setComplete(true);
        await onboardingApi.complete(res.current_profile, accessToken);
        await fetchMe();
        setTimeout(() => {
          router.replace("/dashboard");
        }, 2500);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!inputValue.trim() || loading || complete) return;

    const msg = inputValue.trim();
    setInputValue("");
    setMessages((prev) => [...prev, { role: "user", content: msg }]);
    handleChat(msg);
  }

  return (
    <div className="flex flex-col h-dvh bg-background">
      {/* Header — matches the app's top-bar style, full width */}
      <header className="px-6 py-4 border-b border-border bg-[#0A0A0A] flex items-center gap-3 shrink-0">
        <div className="w-8 h-8 bg-accent/10 text-accent rounded-full flex items-center justify-center font-outfit font-bold text-sm border border-accent/20">
          ₹
        </div>
        <div>
          <h1 className="font-outfit font-semibold text-base text-text-primary leading-none">
            ArthSaathi
          </h1>
          <p className="text-xs text-text-secondary mt-0.5">Setting up your profile</p>
        </div>
      </header>

      {/* Chat Area — centered column, comfortable reading width */}
      <div className="flex-1 overflow-y-auto py-6 px-4">
        <div className="max-w-2xl mx-auto flex flex-col gap-4">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <SurfaceCard
                className={`max-w-[75%] p-3 ${
                  m.role === "user"
                    ? "bg-accent/10 border-accent/20 text-text-primary"
                    : "bg-[#0A0A0A] text-text-secondary"
                }`}
              >
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{m.content}</p>
              </SurfaceCard>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <SurfaceCard className="p-3 bg-[#0A0A0A] flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-accent" />
                <p className="text-sm text-text-secondary">{t.typing}</p>
              </SurfaceCard>
            </div>
          )}

          {complete && (
            <div className="flex justify-center mt-4">
              <p className="text-accent text-sm font-medium bg-accent/10 px-4 py-2 rounded-full border border-accent/20">
                {t.complete}
              </p>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Bar — full width footer, input constrained to match chat column */}
      <div className="px-4 py-4 border-t border-border bg-[#0A0A0A] shrink-0">
        <form onSubmit={onSubmit} className="max-w-2xl mx-auto flex gap-3">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={t.placeholder}
            disabled={loading || complete}
            className="flex-1"
          />
          <Button
            type="submit"
            disabled={!inputValue.trim() || loading || complete}
            className="px-4 shrink-0"
          >
            <Send className="w-4 h-4" />
          </Button>
        </form>
      </div>
    </div>
  );
}

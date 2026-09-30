"use client";

import { useState, useEffect, Suspense } from "react";
import { ChatInput } from "./components/ChatInput";
import { StoryMessage } from "./components/StoryMessage";
import { BookOpen } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";

type Message = { id: string; role: "user" | "storyteller"; content: string };

const SUGGESTIONS = [
  "Explain Compound Interest",
  "How do Micro-loans work?",
  "Why is Insurance important?"
];

function KathaChat() {
  const { accessToken } = useAuthStore();
  const searchParams = useSearchParams();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if (!initialized && accessToken) {
      setInitialized(true);
      const q = searchParams.get("q");
      if (q) {
        handleSend(q);
      }
    }
  }, [searchParams, accessToken, initialized]);

  const handleSend = async (text: string) => {
    if (!text.trim() || !accessToken) return;
    
    setMessages(prev => [...prev, { id: Date.now().toString(), role: "user", content: text }]);
    setIsStreaming(true);

    const storyId = (Date.now() + 1).toString();
    setMessages(prev => [...prev, { id: storyId, role: "storyteller", content: "" }]);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/katha/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`
        },
        body: JSON.stringify({ message: text })
      });

      if (!res.ok) throw new Error("Stream failed");
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        let buffer = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          
          const lines = buffer.split("\n\n");
          buffer = lines.pop() || ""; // Keep the incomplete line in the buffer
          
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const dataStr = line.replace("data: ", "");
              try {
                const data = JSON.parse(dataStr);
                if (data.text) {
                  setMessages(prev => prev.map(m => 
                    m.id === storyId ? { ...m, content: m.content + data.text } : m
                  ));
                }
              } catch (e) {
                console.error("SSE parse error", e);
              }
            }
          }
        }
      }
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev.filter(m => m.id !== storyId), { 
        id: storyId, role: "storyteller", content: "I'm sorry, I couldn't fetch a story right now." 
      }]);
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100dvh-8rem)] md:h-[calc(100dvh-4rem)] w-full max-w-3xl mx-auto animate-fade-up relative">
      <div className="flex flex-col gap-1 border-b border-border pb-4 shrink-0">
        <h1 className="font-outfit text-3xl font-bold text-text-primary flex items-center gap-2">
          <BookOpen className="text-accent" /> Katha Mode
        </h1>
        <p className="text-text-secondary text-sm">
          Learn financial concepts through short, relatable stories.
        </p>
      </div>
      
      <div className="flex-1 overflow-y-auto py-6 space-y-6 scrollbar-hide">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center opacity-50">
            <BookOpen size={48} className="mb-4 text-border" />
            <p className="text-text-secondary max-w-sm">
              Ask about a financial concept, and I will explain it using a short story related to your daily life.
            </p>
          </div>
        ) : (
          messages.map(msg => (
            <StoryMessage key={msg.id} message={msg} />
          ))
        )}
        {isStreaming && (
          <div className="flex items-center gap-3 text-text-secondary text-sm font-medium animate-pulse">
            <div className="w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin" />
            Crafting story...
          </div>
        )}
      </div>

      <div className="shrink-0 pt-4 bg-background">
        {messages.length === 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {SUGGESTIONS.map(s => (
              <button 
                key={s} 
                onClick={() => handleSend(s)}
                className="px-3 py-1.5 rounded-full border border-border text-xs text-text-secondary hover:text-text-primary hover:border-[#444] bg-[#0A0A0A] transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
        )}
        <ChatInput onSend={handleSend} disabled={isStreaming} />
      </div>
    </div>
  );
}

export default function KathaPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-text-secondary">Loading Katha Mode...</div>}>
      <KathaChat />
    </Suspense>
  );
}

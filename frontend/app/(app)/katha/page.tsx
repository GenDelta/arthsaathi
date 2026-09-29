"use client";

import { useState } from "react";
import { ChatInput } from "./components/ChatInput";
import { StoryMessage } from "./components/StoryMessage";
import { BookOpen } from "lucide-react";

type Message = { id: string; role: "user" | "storyteller"; content: string };

const SUGGESTIONS = [
  "Explain Compound Interest",
  "How do Micro-loans work?",
  "Why is Insurance important?"
];

export default function KathaPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const handleSend = (text: string) => {
    if (!text.trim()) return;
    
    setMessages(prev => [...prev, { id: Date.now().toString(), role: "user", content: text }]);
    setIsStreaming(true);

    // Mock streaming delay
    setTimeout(() => {
      setMessages(prev => [
        ...prev, 
        { 
          id: (Date.now() + 1).toString(), 
          role: "storyteller", 
          content: "Imagine you are planting a mango tree. The first year, it bears 10 fruits. If you save the seeds and plant them alongside the original, the next year you have 20. Then 40. This is compound interest—your money earning money on itself over time, growing an orchard from a single seed." 
        }
      ]);
      setIsStreaming(false);
    }, 1500);
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

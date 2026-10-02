"use client";

import { useState } from "react";
import { Send } from "lucide-react";

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [val, setVal] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (val.trim()) {
      onSend(val);
      setVal("");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative flex items-center w-full">
      <input
        type="text"
        value={val}
        onChange={(e) => setVal(e.target.value)}
        disabled={disabled}
        placeholder="Type a topic (e.g. Loans, Savings...)"
        className="w-full bg-surface border border-border rounded-xl pl-4 pr-12 py-3 text-sm text-text-primary placeholder:text-text-secondary focus-visible:outline-none focus-visible:border-accent focus-visible:ring-1 focus-visible:ring-accent disabled:opacity-50"
      />
      <button 
        type="submit" 
        disabled={disabled || !val.trim()}
        className="absolute right-2 p-2 rounded-lg text-accent hover:bg-accent/10 disabled:opacity-50 disabled:hover:bg-transparent transition-colors"
      >
        <Send size={18} />
      </button>
    </form>
  );
}

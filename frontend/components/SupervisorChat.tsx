"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, X, Send, Loader2, Bot, User, Mic } from "lucide-react";
import { Button } from "./ui/Button";

type Message = { id: string; role: "user" | "bot"; text: string };

export function SupervisorChat() {
  const { accessToken } = useAuthStore();
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeAgent, setActiveAgent] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  // 1. Load history
  useEffect(() => {
    const saved = localStorage.getItem("arthsaathi_supervisor_chat");
    if (saved) {
      try { setMessages(JSON.parse(saved)); } catch (e) {}
    }
  }, []);

  // 2. Save history
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem("arthsaathi_supervisor_chat", JSON.stringify(messages));
    }
  }, [messages]);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => {
        endRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    }
  }, [messages, activeAgent, isOpen]);

  const handleSend = async () => {
    if (!input.trim() || !accessToken) return;

    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { id: Date.now().toString(), role: "user", text: userMsg }]);
    setLoading(true);
    setActiveAgent("Router");

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/supervisor/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ message: userMsg }),
      });

      if (!res.ok) throw new Error("Failed to chat");
      
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) return;

      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";
        
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.replace("data: ", "");
            if (dataStr === "[DONE]") {
              setLoading(false);
              setActiveAgent(null);
              break;
            }
            try {
              const data = JSON.parse(dataStr);
              if (data.type === "agent_activity") {
                const nodeMap: Record<string, string> = {
                  "router": "Intent Router",
                  "transaction": "Transaction Logger",
                  "scam": "Scam Scanner",
                  "scheme": "Scheme Matchmaker",
                  "katha": "Katha Storyteller",
                  "general": "ArthSaathi Brain",
                  "output_guard": "Safety Guard"
                };
                setActiveAgent(nodeMap[data.node] || data.node);
              } else if (data.type === "final_response") {
                setMessages((prev) => [
                  ...prev,
                  { id: Date.now().toString(), role: "bot", text: data.response },
                ]);
              } else if (data.type === "action") {
                if (data.action === "transaction_logged") {
                  window.dispatchEvent(new CustomEvent("refresh_transactions"));
                } else if (data.action === "navigate" && data.path) {
                  router.push(data.path);
                  setIsOpen(false);
                }
              }
            } catch (e) {}
          }
        }
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { id: Date.now().toString(), role: "bot", text: "Sorry, I am offline right now." },
      ]);
    } finally {
      setLoading(false);
      setActiveAgent(null);
    }
  };

  return (
    <>
      {/* Floating Action Button */}
      <AnimatePresence>
        {!isOpen && (
          <motion.button
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            exit={{ scale: 0 }}
            onClick={() => setIsOpen(true)}
            className="fixed bottom-20 md:bottom-8 right-4 md:right-8 z-40 bg-accent hover:bg-accent/90 text-black p-4 rounded-full shadow-2xl flex items-center justify-center transition-colors"
          >
            <MessageSquare className="w-6 h-6" />
          </motion.button>
        )}
      </AnimatePresence>

      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="fixed bottom-20 md:bottom-8 right-4 md:right-8 z-50 w-[calc(100vw-2rem)] md:w-96 bg-surface border border-border rounded-2xl shadow-2xl flex flex-col overflow-hidden"
            style={{ height: "500px", maxHeight: "80vh" }}
          >
            {/* Header */}
            <div className="bg-surface-light px-4 py-3 border-b border-border flex items-center justify-between shrink-0">
              <div className="flex items-center gap-2">
                <Bot className="w-5 h-5 text-accent" />
                <h3 className="font-outfit font-semibold text-text-primary">ArthSaathi Agent</h3>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="text-text-secondary hover:text-text-primary transition-colors p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
              {messages.length === 0 && (
                <div className="flex-1 flex flex-col items-center justify-center text-center text-text-secondary gap-3 px-4">
                  <Bot className="w-10 h-10 text-text-tertiary" />
                  <p className="text-sm">
                    Hi! I am the ArthSaathi Supervisor. Ask me anything, log a transaction, check a scheme, or ask me to check a loan message for fraud.
                  </p>
                </div>
              )}
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex items-start gap-2 max-w-[85%] ${
                    msg.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"
                  }`}
                >
                  <div
                    className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                      msg.role === "user" ? "bg-accent text-black" : "bg-surface-light text-accent border border-border"
                    }`}
                  >
                    {msg.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                  </div>
                  <div
                    className={`p-3 rounded-2xl text-sm ${
                      msg.role === "user"
                        ? "bg-accent/10 text-text-primary border border-accent/20 rounded-tr-none"
                        : "bg-surface-light text-text-primary border border-border rounded-tl-none"
                    }`}
                  >
                    {msg.text}
                  </div>
                </div>
              ))}
              {loading && activeAgent && (
                <div className="flex items-start gap-2 max-w-[85%] mr-auto">
                  <div className="shrink-0 w-8 h-8 rounded-full bg-surface-light text-accent border border-border flex items-center justify-center">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="p-3 rounded-2xl text-sm bg-surface-light text-text-primary border border-border rounded-tl-none flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-accent" />
                    <span className="text-text-secondary font-medium tracking-tight flex gap-1">
                      {activeAgent} <span className="animate-pulse">is thinking...</span>
                    </span>
                  </div>
                </div>
              )}
              <div ref={endRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-border bg-surface shrink-0">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSend()}
                  placeholder="Ask me anything..."
                  className="flex-1 bg-surface-light border border-border rounded-full px-4 py-2 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/50 transition-all"
                />
                <Button
                  onClick={handleSend}
                  disabled={!input.trim() || loading}
                  className="rounded-full w-10 h-10 p-0 flex items-center justify-center shrink-0"
                >
                  <Send className="w-4 h-4 ml-0.5" />
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

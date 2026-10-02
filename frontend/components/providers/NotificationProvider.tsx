"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/store/useAuthStore";
import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, Info, X } from "lucide-react";

interface Alert {
  id: string;
  type: string;
  title: string;
  message: string;
}

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const { accessToken } = useAuthStore();
  const [alerts, setAlerts] = useState<Alert[]>([]);

  useEffect(() => {
    if (!accessToken) return;

    // Connect to the Guardian SSE stream
    const url = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/guardian/stream`;
    
    // We cannot easily pass Bearer token in native EventSource, so we pass it in the query
    // Wait, native EventSource doesn't support custom headers. Let's use fetch reader for SSE!
    const abortController = new AbortController();
    
    const connectStream = async () => {
      try {
        const res = await fetch(url, {
          headers: { Authorization: `Bearer ${accessToken}` },
          signal: abortController.signal
        });
        
        if (!res.body) return;
        
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n\n");
          buffer = lines.pop() || "";
          
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.replace("data: ", ""));
                const newAlert: Alert = { ...data, id: Date.now().toString() + Math.random() };
                setAlerts((prev) => [...prev, newAlert]);
                
                // Auto dismiss after 10s
                setTimeout(() => {
                  setAlerts((prev) => prev.filter(a => a.id !== newAlert.id));
                }, 10000);
              } catch (e) {}
            }
          }
        }
      } catch (err: any) {
        if (err.name !== 'AbortError') {
          console.error("SSE stream error", err);
          // Reconnect after 5s
          setTimeout(connectStream, 5000);
        }
      }
    };

    connectStream();
    
    return () => abortController.abort();
  }, [accessToken]);

  const dismiss = (id: string) => {
    setAlerts((prev) => prev.filter(a => a.id !== id));
  };

  return (
    <>
      {children}
      {/* Toast Container */}
      <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full">
        <AnimatePresence>
          {alerts.map((alert) => (
            <motion.div
              key={alert.id}
              initial={{ opacity: 0, y: -20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
              className={`flex items-start gap-3 p-4 rounded-xl border border-border shadow-2xl relative overflow-hidden bg-surface`}
            >
              {/* Colored left border indicator based on type */}
              <div className={`absolute left-0 top-0 bottom-0 w-1 ${
                alert.type === "FRAUD_ALERT" ? "bg-red-500" : 
                alert.type === "HIGH_SPEND_ALERT" ? "bg-amber-500" : "bg-blue-500"
              }`} />
              
              <div className="shrink-0 pt-0.5">
                {alert.type === "FRAUD_ALERT" ? (
                  <AlertTriangle className="text-red-500 h-5 w-5" />
                ) : (
                  <Info className="text-accent h-5 w-5" />
                )}
              </div>
              <div className="flex-1 min-w-0 pr-6">
                <h4 className="font-outfit font-semibold text-text-primary text-sm truncate">
                  {alert.title}
                </h4>
                <p className="text-xs text-text-secondary mt-1 leading-relaxed">
                  {alert.message}
                </p>
              </div>
              <button 
                onClick={() => dismiss(alert.id)}
                className="absolute top-2 right-2 text-text-tertiary hover:text-text-primary transition-colors p-1"
              >
                <X className="h-4 w-4" />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </>
  );
}

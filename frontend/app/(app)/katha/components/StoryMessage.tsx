"use client";

import { cn } from "@/lib/cn";
import { User, Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";

interface StoryMessageProps {
  message: {
    role: "user" | "storyteller";
    content: string;
  };
}

export function StoryMessage({ message }: StoryMessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex gap-4 w-full", isUser ? "flex-row-reverse" : "flex-row")}>
      <div className={cn(
        "flex items-center justify-center shrink-0 w-8 h-8 rounded-full",
        isUser ? "bg-[#222] text-text-secondary" : "bg-accent text-black"
      )}>
        {isUser ? <User size={16} /> : <Sparkles size={16} />}
      </div>
      
      <div className={cn(
        "flex flex-col gap-2 max-w-[85%] md:max-w-[75%]",
        isUser ? "items-end" : "items-start"
      )}>
        <div className={cn(
          "px-4 py-3 rounded-2xl text-sm leading-relaxed max-w-none",
          isUser 
            ? "bg-[#222] text-text-primary rounded-tr-sm" 
            : "bg-surface border border-border text-text-primary rounded-tl-sm"
        )}>
          {isUser ? (
            message.content
          ) : (
            <ReactMarkdown 
              components={{
                p: ({node, ...props}) => <p className="mb-2 last:mb-0" {...props} />,
                strong: ({node, ...props}) => <strong className="font-semibold text-accent" {...props} />,
                ul: ({node, ...props}) => <ul className="list-disc pl-4 mb-2" {...props} />,
                ol: ({node, ...props}) => <ol className="list-decimal pl-4 mb-2" {...props} />,
                li: ({node, ...props}) => <li className="mb-1" {...props} />,
                h3: ({node, ...props}) => <h3 className="text-lg font-bold mt-3 mb-1 text-accent" {...props} />,
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>
      </div>
    </div>
  );
}

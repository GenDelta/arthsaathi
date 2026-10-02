"use client";

import { useRef } from "react";
import { FileText, UploadCloud } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface UploadAreaProps {
  onUpload: (file: File) => void;
}

export function UploadArea({ onUpload }: UploadAreaProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUpload(file);
    }
  };

  return (
    <div 
      className="flex flex-col items-center justify-center p-12 border-2 border-dashed border-border bg-[#0A0A0A] rounded-xl transition-colors hover:border-[#444] group cursor-pointer" 
      onClick={() => fileInputRef.current?.click()}
    >
      <input 
        type="file" 
        ref={fileInputRef} 
        className="hidden" 
        accept="image/jpeg, image/png, application/pdf"
        onChange={handleFileChange}
      />
      <div className="p-4 rounded-full bg-[#111] text-text-secondary group-hover:text-accent transition-colors mb-4">
        <FileText size={32} />
      </div>
      <h3 className="text-lg font-outfit font-semibold text-text-primary mb-1">
        Tap to upload document
      </h3>
      <p className="text-sm text-text-secondary mb-6 text-center max-w-sm">
        Supports PDF, JPG, and PNG files up to 5MB. Clear, legible images work best.
      </p>
      <Button variant="outline" className="pointer-events-none">
        <UploadCloud size={18} /> Choose File
      </Button>
    </div>
  );
}

"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { LayoutDashboard, Scan, Layers, MessageSquare, ChevronLeft, ChevronRight, LogOut, UserCircle } from "lucide-react";
import { cn } from "@/lib/cn";
import { useAuthStore } from "@/store/useAuthStore";

const NAV_ITEMS = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/scam-scanner", icon: Scan, label: "Scanner" },
  { href: "/schemes", icon: Layers, label: "Schemes" },
  { href: "/katha", icon: MessageSquare, label: "Katha Mode" },
];

export function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const pathname = usePathname();
  const router = useRouter();
  const { clearAuth } = useAuthStore();

  const handleLogout = () => {
    clearAuth();
    router.push("/auth");
  };

  return (
    <motion.aside
      initial={{ width: 240 }}
      animate={{ width: isCollapsed ? 80 : 240 }}
      className="hidden md:flex flex-col bg-surface border-r border-border h-full sticky top-0"
    >
      <div className="h-16 flex items-center justify-between px-4 border-b border-border">
        {!isCollapsed && (
          <motion.span 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="font-outfit font-bold text-lg text-accent"
          >
            ArthSaathi
          </motion.span>
        )}
        <button 
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-1.5 rounded-md text-text-secondary hover:text-text-primary hover:bg-[#111] transition-colors mx-auto"
        >
          {isCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
        </button>
      </div>

      <nav className="flex-1 px-3 py-6 space-y-2">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link 
              key={item.href} 
              href={item.href}
              className={cn(
                "flex items-center h-10 px-3 rounded-lg transition-colors group",
                isActive 
                  ? "bg-[#1A1500] text-accent" 
                  : "text-text-secondary hover:bg-[#111] hover:text-text-primary"
              )}
            >
              <item.icon size={20} className="shrink-0" />
              {!isCollapsed && (
                <span className="ml-3 font-medium whitespace-nowrap">{item.label}</span>
              )}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-border flex flex-col gap-2">
        <Link
          href="/profile"
          className={cn(
            "flex items-center w-full h-10 px-3 rounded-lg transition-colors group",
            pathname.startsWith("/profile")
              ? "bg-[#1A1500] text-accent"
              : "text-text-secondary hover:bg-[#111] hover:text-text-primary"
          )}
        >
          <UserCircle size={20} className="shrink-0" />
          {!isCollapsed && <span className="ml-3 font-medium">Profile</span>}
        </Link>
        <button 
          onClick={handleLogout}
          className="flex items-center w-full h-10 px-3 rounded-lg text-text-secondary hover:bg-[#111] hover:text-danger transition-colors"
        >
          <LogOut size={20} className="shrink-0" />
          {!isCollapsed && <span className="ml-3 font-medium">Log out</span>}
        </button>
      </div>
    </motion.aside>
  );
}

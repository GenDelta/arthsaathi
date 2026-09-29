"use client";

import { useEffect, useState } from "react";
import { profileApi, ProfileResponse } from "@/lib/api-client";
import { useAuthStore } from "@/store/useAuthStore";
import { SurfaceCard } from "@/components/ui/SurfaceCard";
import { Loader2, User, Phone, Briefcase, IndianRupee, Wallet, LogOut } from "lucide-react";

export default function ProfilePage() {
  const { accessToken } = useAuthStore();
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    
    profileApi.getProfile(accessToken)
      .then((data) => setProfile(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [accessToken]);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="w-8 h-8 text-accent animate-spin" />
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="flex h-full items-center justify-center flex-col gap-4">
        <p className="text-danger font-medium">{error || "Failed to load profile"}</p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-3xl mx-auto flex flex-col gap-8 animate-fade-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-outfit text-3xl font-bold text-text-primary mb-2">My Profile</h1>
          <p className="text-text-secondary">Your personal and financial details securely stored.</p>
        </div>
        <button
          onClick={() => {
            useAuthStore.getState().clearAuth();
            window.location.href = "/auth";
          }}
          className="md:hidden flex items-center gap-2 px-4 py-2 bg-danger/10 text-danger rounded-lg text-sm font-medium hover:bg-danger/20 transition-colors"
        >
          <LogOut size={16} />
          Log out
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Personal Details */}
        <SurfaceCard className="p-6 flex flex-col gap-6">
          <h2 className="text-lg font-outfit font-semibold text-text-primary border-b border-border pb-2">Personal Details</h2>
          
          <div className="flex items-start gap-4">
            <div className="p-2 bg-accent/10 rounded-lg shrink-0">
              <User className="text-accent w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-text-secondary uppercase tracking-wider font-semibold">Full Name</p>
              <p className="text-text-primary font-medium mt-1">{profile.name}</p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="p-2 bg-accent/10 rounded-lg shrink-0">
              <Phone className="text-accent w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-text-secondary uppercase tracking-wider font-semibold">Mobile Number</p>
              <p className="text-text-primary font-medium mt-1 font-mono tracking-wider">{profile.phone_number}</p>
            </div>
          </div>
        </SurfaceCard>

        {/* Work & Financial Details */}
        <SurfaceCard className="p-6 flex flex-col gap-6">
          <h2 className="text-lg font-outfit font-semibold text-text-primary border-b border-border pb-2">Work & Financials</h2>
          
          <div className="flex items-start gap-4">
            <div className="p-2 bg-accent/10 rounded-lg shrink-0">
              <Briefcase className="text-accent w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-text-secondary uppercase tracking-wider font-semibold">Employment</p>
              <p className="text-text-primary font-medium mt-1">
                {profile.employment_type?.replace("_", " ")} 
                {profile.occupation ? ` — ${profile.occupation}` : ""}
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="p-2 bg-accent/10 rounded-lg shrink-0">
              <IndianRupee className="text-accent w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-text-secondary uppercase tracking-wider font-semibold">Income</p>
              <p className="text-text-primary font-medium mt-1">
                {profile.average_income ? `₹${profile.average_income.toLocaleString('en-IN')}` : "Not specified"} 
                {profile.income_frequency ? ` (${profile.income_frequency.toLowerCase()})` : ""}
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="p-2 bg-accent/10 rounded-lg shrink-0">
              <Wallet className="text-accent w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-text-secondary uppercase tracking-wider font-semibold">Financial Concerns</p>
              <p className="text-text-primary font-medium mt-1 text-sm leading-relaxed">
                {profile.financial_pain_points || "None specified"}
              </p>
            </div>
          </div>
        </SurfaceCard>
      </div>
    </div>
  );
}

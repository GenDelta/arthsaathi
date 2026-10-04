"use client";

import { useEffect, useState } from "react";
import { profileApi, ProfileResponse } from "@/lib/api-client";
import { useAuthStore } from "@/store/useAuthStore";
import { consentApi, ConsentStatus } from "@/lib/api-client";
import { ShieldCheck, Trash2 } from "lucide-react";
import { SurfaceCard } from "@/components/ui/SurfaceCard";
import { Button } from "@/components/ui/Button";
import { Loader2, User, Phone, Briefcase, IndianRupee, Wallet, LogOut } from "lucide-react";

export default function ProfilePage() {
  const { accessToken } = useAuthStore();
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [consents, setConsents] = useState<ConsentStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (!accessToken) return;
    
    Promise.all([
      profileApi.getProfile(accessToken),
      consentApi.status(accessToken)
    ])
      .then(([profileData, consentData]) => {
        setProfile(profileData);
        setConsents(consentData.consents);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [accessToken]);

  async function handleWithdraw(purpose: string) {
    if (!accessToken) return;
    try {
      await consentApi.revoke(accessToken, purpose);
      const data = await consentApi.status(accessToken);
      setConsents(data.consents);
    } catch (e) {
      console.error("Failed to revoke", e);
    }
  }

  async function handleDeleteData() {
    if (!accessToken) return;
    setIsDeleting(true);
    try {
      await consentApi.deleteData(accessToken);
      window.location.reload();
    } catch (e) {
      console.error("Failed to delete", e);
      setIsDeleting(false);
    }
  }

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
              <User className="text-accent w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-text-secondary uppercase tracking-wider font-semibold">Demographics</p>
              <p className="text-text-primary font-medium mt-1">
                {profile.gender || "Not specified"} &bull; {profile.date_of_birth || "DOB Not specified"}
              </p>
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
          
          <div className="flex items-start gap-4">
            <div className="p-2 bg-accent/10 rounded-lg shrink-0">
              <Briefcase className="text-accent w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-text-secondary uppercase tracking-wider font-semibold">State of Residence</p>
              <p className="text-text-primary font-medium mt-1">{profile.state_of_residence || "Not specified"}</p>
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

        {/* Privacy & Consent */}
        <SurfaceCard className="p-6 col-span-1 md:col-span-2 lg:col-span-3 flex flex-col gap-6">
          <div className="flex items-center gap-3 border-b border-white/10 pb-4">
            <div className="w-10 h-10 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-500">
              <ShieldCheck size={20} />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-text-primary">Privacy & Permissions</h2>
              <p className="text-sm text-text-secondary">Manage how ArthSaathi uses your data</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {consents.map(c => (
              <div key={c.purpose} className="flex items-center justify-between p-4 border border-white/10 rounded-lg bg-white/[0.02]">
                <div>
                  <p className="text-sm font-medium text-text-primary">{c.purpose.replace('_', ' ')}</p>
                  <p className="text-xs text-text-secondary mt-1">
                    {c.granted ? "Granted" : "Withdrawn"} ({c.notice_version})
                  </p>
                </div>
                {c.granted && (
                  <Button variant="outline" size="sm" onClick={() => handleWithdraw(c.purpose)}>
                    Withdraw
                  </Button>
                )}
              </div>
            ))}
            {consents.length === 0 && <p className="text-sm text-text-secondary">No active permissions.</p>}
          </div>
          
          <div className="pt-4 border-t border-red-500/10 mt-2">
            <h3 className="text-sm font-semibold text-red-400 mb-2">Danger Zone</h3>
            {showDeleteConfirm ? (
              <div className="p-4 border border-red-500/30 rounded-lg bg-red-500/5 flex flex-col gap-3 animate-fade-up">
                <p className="text-sm font-medium text-red-400">Are you absolutely sure?</p>
                <p className="text-xs text-text-secondary">This will permanently wipe all your transactions and analysis data. This action cannot be undone.</p>
                <div className="flex items-center gap-3 mt-2">
                  <Button variant="primary" onClick={handleDeleteData} disabled={isDeleting} className="bg-red-500 text-white hover:bg-red-600 border-0">
                    {isDeleting ? "Deleting..." : "Yes, Delete Everything"}
                  </Button>
                  <Button variant="outline" onClick={() => setShowDeleteConfirm(false)} disabled={isDeleting}>
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <>
                <Button variant="outline" onClick={() => setShowDeleteConfirm(true)} className="text-red-400 border-red-500/20 hover:bg-red-500/10">
                  <Trash2 size={16} className="mr-2" /> Delete My Financial Data
                </Button>
                <p className="text-xs text-text-secondary mt-2">
                  This will permanently erase all transactions, nudges, and risk analysis data from our servers.
                </p>
              </>
            )}
          </div>
        </SurfaceCard>
      </div>
    </div>
  );
}

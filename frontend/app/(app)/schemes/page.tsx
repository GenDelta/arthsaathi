"use client";

import { useEffect, useState } from "react";
import { SchemeCard } from "./components/SchemeCard";
import { Badge } from "@/components/ui/Badge";
import { Filter, Loader2, Sparkles, User, Briefcase } from "lucide-react";
import { schemesApi, profileApi, SchemeMatch, ProfileResponse } from "@/lib/api-client";
import { useAuthStore } from "@/store/useAuthStore";
import { SurfaceCard } from "@/components/ui/SurfaceCard";

export default function SchemesPage() {
  const { accessToken } = useAuthStore();
  const [schemes, setSchemes] = useState<SchemeMatch[]>([]);
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!accessToken) return;
    
    Promise.all([
      schemesApi.match(accessToken),
      profileApi.getProfile(accessToken)
    ])
    .then(([schemesData, profileData]) => {
      setSchemes(schemesData.schemes);
      setProfile(profileData);
    })
    .catch(console.error)
    .finally(() => setLoading(false));
  }, [accessToken]);

  if (loading) {
    return (
      <div className="flex flex-col h-[60vh] items-center justify-center gap-4 text-text-secondary">
        <Loader2 className="w-8 h-8 text-accent animate-spin" />
        <p className="animate-pulse">Matching schemes using AI across Central & State databases...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8 w-full animate-fade-up max-w-6xl mx-auto">
      
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-border pb-6">
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <Sparkles className="text-accent w-6 h-6" />
            <h1 className="font-outfit text-3xl font-bold text-text-primary">
              AI Scheme Matchmaker
            </h1>
          </div>
          <p className="text-text-secondary text-sm md:text-base max-w-2xl">
            We analyzed 3,400+ government programs. These are the top schemes tailored for you based on your extracted profile.
          </p>
        </div>
      </div>

      {profile && (
        <SurfaceCard className="p-4 flex flex-wrap gap-x-8 gap-y-4 bg-accent/5 border-accent/20">
            <div className="flex items-center gap-3">
              <User className="text-accent w-5 h-5" />
              <div>
                <p className="text-[10px] uppercase text-text-muted font-bold tracking-wider">Demographics</p>
                <p className="text-sm text-text-primary font-medium">{profile.gender || "Any"} &bull; {profile.state_of_residence || "India"} &bull; {profile.date_of_birth || "Age unverified"}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <Briefcase className="text-accent w-5 h-5" />
              <div>
                <p className="text-[10px] uppercase text-text-muted font-bold tracking-wider">Occupation</p>
                <p className="text-sm text-text-primary font-medium">{profile.employment_type?.replace("_", " ")} {profile.occupation ? `(${profile.occupation})` : ""}</p>
              </div>
            </div>
        </SurfaceCard>
      )}

      {schemes.length === 0 ? (
        <div className="text-center py-12 text-text-muted bg-[#111] rounded-xl border border-border">
          <p>No highly-relevant schemes found for your specific profile at this time.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {schemes
            .sort((a, b) => (b.confidence_score || 0) - (a.confidence_score || 0))
            .map((scheme) => (
              <SchemeCard key={scheme.id} scheme={scheme} />
          ))}
        </div>
      )}
    </div>
  );
}


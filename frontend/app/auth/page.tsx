"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { authApi } from "@/lib/api-client";
import { useAuthStore } from "@/store/useAuthStore";
import { SurfaceCard } from "@/components/ui/SurfaceCard";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { translations, Language } from "@/lib/i18n";
import { ShieldCheck, ScanLine, KeyRound } from "lucide-react";

type Step = "phone" | "scan" | "verify";

export default function AuthPage() {
  const router = useRouter();
  const { setAuth, fetchMe } = useAuthStore();

  const [lang, setLang] = useState<Language>("en");
  const [step, setStep] = useState<Step>("phone");
  const [phone, setPhone] = useState("");
  const [totpCode, setTotpCode] = useState("");
  const [qrCodeUri, setQrCodeUri] = useState<string | null>(null);
  const [secret, setSecret] = useState<string | null>(null);
  const [isNewUser, setIsNewUser] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const t = translations[lang].auth;
  const common = translations[lang].common;

  function formatPhone(raw: string): string {
    const digits = raw.replace(/\D/g, "");
    return `+91${digits.slice(-10)}`;
  }

  async function handlePhoneSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    
    const digits = phone.replace(/\D/g, "");
    if (digits.length !== 10) {
      setError(t.invalidPhone);
      return;
    }

    setLoading(true);
    try {
      const formattedPhone = formatPhone(phone);
      const res = await authApi.totpSetup(formattedPhone);
      setQrCodeUri(res.qr_code_uri);
      setSecret(res.secret);
      setIsNewUser(res.is_new_user);
      // New users must scan QR first; returning users go straight to verify
      setStep(res.is_new_user ? "scan" : "verify");
    } catch (err: any) {
      setError(err.message || common.error);
    } finally {
      setLoading(false);
    }
  }

  async function handleVerify(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    
    const codeDigits = totpCode.replace(/\D/g, "");
    if (codeDigits.length !== 6) {
      setError(t.invalidCode);
      return;
    }

    setLoading(true);
    try {
      const formattedPhone = formatPhone(phone);
      const res = await authApi.totpVerify(formattedPhone, codeDigits);

      setAuth(res.access_token, res.refresh_token, {
        id: "",
        name: "",
        role: "CITIZEN",
        language_pref: lang,
        organization_id: null,
      }, res.is_onboarded);

      await fetchMe();

      if (res.is_onboarded) {
        router.replace("/dashboard");
      } else {
        router.replace("/onboarding");
      }
    } catch (err: any) {
      setError(err.message || common.error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-dvh flex items-center justify-center p-4 bg-background relative">
      {/* Language Toggle */}
      <button
        onClick={() => setLang(lang === "en" ? "hi" : "en")}
        className="absolute top-6 right-6 px-4 py-2 rounded-full border border-border bg-[#0A0A0A] text-sm font-medium text-text-primary hover:border-accent transition-colors"
      >
        {common.switchTo}
      </button>

      <SurfaceCard className="w-full max-w-md p-8 flex flex-col gap-6 animate-fade-up mt-8 md:mt-0">
        {/* Logo */}
        <div className="flex flex-col items-center text-center gap-2 mb-2">
          <div className="w-12 h-12 bg-accent/10 text-accent rounded-full flex items-center justify-center font-outfit font-bold text-xl mb-2 border border-accent/20">
            ₹
          </div>
          <h1 className="font-outfit text-2xl font-bold text-text-primary">
            ArthSaathi
          </h1>
          <p className="text-text-secondary text-sm">
            {step === "phone"
              ? t.subtitle
              : step === "scan"
              ? t.scanSubtitle
              : t.verifySubtitle}
          </p>
        </div>

        {/* Step 1: Phone number */}
        {step === "phone" && (
          <form onSubmit={handlePhoneSubmit} className="flex flex-col gap-4">
            <div className="flex items-center gap-3 p-3 bg-accent/5 border border-accent/20 rounded-lg">
              <ShieldCheck className="text-accent shrink-0" size={18} />
              <p className="text-xs text-text-secondary">{t.totpExplainer}</p>
            </div>
            <Input
              type="tel"
              placeholder={t.phone}
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              required
            />
            {error && <p className="text-danger text-sm font-medium">{error}</p>}
            <Button type="submit" loading={loading} className="w-full mt-2">
              {t.continue}
            </Button>
          </form>
        )}

        {/* Step 2: QR Code Scan (new users only) */}
        {step === "scan" && qrCodeUri && (
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-3 p-3 bg-accent/5 border border-accent/20 rounded-lg">
              <ScanLine className="text-accent shrink-0" size={18} />
              <p className="text-xs text-text-secondary">{t.scanInstructions}</p>
            </div>

            {/* QR Code */}
            <div className="flex justify-center">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={qrCodeUri}
                alt="TOTP QR Code"
                className="w-48 h-48 border border-border rounded-lg bg-white p-1"
              />
            </div>

            {/* Manual entry secret */}
            <details className="group">
              <summary className="text-xs text-text-secondary cursor-pointer hover:text-accent transition-colors">
                {t.manualEntry}
              </summary>
              <div className="mt-2 p-3 bg-[#0A0A0A] border border-border rounded-lg font-mono text-xs text-accent break-all select-all">
                {secret}
              </div>
            </details>

            <Button
              type="button"
              onClick={() => setStep("verify")}
              className="w-full"
            >
              {t.scannedIt}
            </Button>
          </div>
        )}

        {/* Step 3: Enter TOTP Code */}
        {step === "verify" && (
          <form onSubmit={handleVerify} className="flex flex-col gap-4">
            <div className="flex items-center gap-3 p-3 bg-accent/5 border border-accent/20 rounded-lg">
              <KeyRound className="text-accent shrink-0" size={18} />
              <p className="text-xs text-text-secondary">{t.enterCode}</p>
            </div>
            <Input
              type="text"
              inputMode="numeric"
              placeholder="000000"
              value={totpCode}
              onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
              maxLength={6}
              required
              className="text-center text-2xl font-mono tracking-[0.5em] py-4"
            />
            {error && <p className="text-danger text-sm font-medium">{error}</p>}
            <Button type="submit" loading={loading} className="w-full mt-2">
              {t.verifyAndLogin}
            </Button>
            {/* Allow re-scanning if on a new device */}
            <button
              type="button"
              onClick={async () => {
                setLoading(true);
                try {
                  const formattedPhone = formatPhone(phone);
                  const res = await authApi.totpSetup(formattedPhone, true); // force_reset=true
                  setQrCodeUri(res.qr_code_uri);
                  setSecret(res.secret);
                  setIsNewUser(true); // force it to show scan step
                  setStep("scan");
                } catch (err: any) {
                  setError(err.message || common.error);
                } finally {
                  setLoading(false);
                }
              }}
              className="text-xs text-text-secondary hover:text-accent transition-colors text-center"
            >
              {t.newDevice}
            </button>
          </form>
        )}
      </SurfaceCard>
    </div>
  );
}

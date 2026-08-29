"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { authApi } from "@/lib/api-client";
import { useAuthStore } from "@/store/useAuthStore";

export default function RegisterPage() {
  const router = useRouter();
  const { setAuth, fetchMe } = useAuthStore();

  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [occupation, setOccupation] = useState("");
  const [languagePref, setLanguagePref] = useState<"hi" | "en">("hi");
  
  const [loading, setLoading] = useState(false);
  const [globalError, setGlobalError] = useState<string | null>(null);

  const labels = {
    hi: {
      heading: "खाता बनाएं",
      sub: "ArthSaathi में आपका स्वागत है",
      name: "पूरा नाम",
      namePlaceholder: "अपना नाम दर्ज करें",
      phone: "मोबाइल नंबर",
      phonePlaceholder: "+91 98765 43210",
      password: "पासवर्ड",
      passwordPlaceholder: "कम से कम 8 अक्षर",
      occupation: "व्यवसाय (वैकल्पिक)",
      occupationPlaceholder: "उदा. किसान, ड्राइवर",
      submit: "खाता बनाएं",
      hasAccount: "पहले से खाता है?",
      login: "लॉगिन करें",
    },
    en: {
      heading: "Create an account",
      sub: "Welcome to ArthSaathi",
      name: "Full Name",
      namePlaceholder: "Enter your full name",
      phone: "Mobile number",
      phonePlaceholder: "+91 98765 43210",
      password: "Password",
      passwordPlaceholder: "At least 8 characters",
      occupation: "Occupation (Optional)",
      occupationPlaceholder: "e.g. Farmer, Driver",
      submit: "Create account",
      hasAccount: "Already have an account?",
      login: "Sign in",
    },
  }[languagePref];

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setGlobalError(null);
    setLoading(true);
    try {
      const cleanPhone = phone.replace(/\D/g, '');
      const formattedPhone = `+91${cleanPhone.slice(-10)}`;
      const res = await authApi.register({
        name,
        phone_number: formattedPhone,
        password,
        occupation: occupation || undefined,
        language_pref: languagePref,
      });
      // Set auth state; the role returned by register isn't provided directly, 
      // but new citizens are "CITIZEN" by default. We'll fetch the real profile right after.
      setAuth(res.access_token, res.refresh_token, {
        id: res.user_id,
        name,
        role: "CITIZEN",
        language_pref: languagePref,
        organization_id: null,
      });
      await fetchMe();
      router.replace("/");
    } catch (err: unknown) {
      const e = err as { message?: string; status?: number; code?: string };
      if (e.status === 409) {
        setGlobalError(languagePref === "hi" ? "यह नंबर पहले से पंजीकृत है" : "This phone number is already registered");
      } else {
        setGlobalError(e.message ?? "Something went wrong");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-shell">
      {/* Signature: breathing coin ring */}
      <div className="coin-ring" aria-hidden="true" />

      <main className="auth-card" role="main">
        {/* Brand mark */}
        <div className="brand-mark">
          <div className="brand-logotype" aria-label="ArthSaathi">
            अर्थसाथी
          </div>
          <div className="brand-subtitle">Your Financial Companion</div>
        </div>

        {/* Language toggle */}
        <div style={{ display: "flex", justifyContent: "center", marginBottom: "var(--sp-6)" }}>
          <button
            type="button"
            className="lang-badge"
            onClick={() => setLanguagePref(languagePref === "hi" ? "en" : "hi")}
            aria-label="Switch language"
          >
            {languagePref === "hi" ? "🇮🇳 हिंदी" : "🇬🇧 English"}
          </button>
        </div>

        <h1 className="auth-heading">{labels.heading}</h1>
        <p className="auth-subheading">{labels.sub}</p>

        {/* Global error */}
        {globalError && (
          <div className="global-error" role="alert" aria-live="polite">
            <span aria-hidden="true">⚠</span>
            {globalError}
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label htmlFor="register-name" className="form-label">
              {labels.name}
            </label>
            <input
              id="register-name"
              type="text"
              className="form-input"
              placeholder={labels.namePlaceholder}
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoComplete="name"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="register-phone" className="form-label">
              {labels.phone}
            </label>
            <input
              id="register-phone"
              type="tel"
              className="form-input"
              placeholder={labels.phonePlaceholder}
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              autoComplete="tel"
              inputMode="numeric"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="register-password" className="form-label">
              {labels.password}
            </label>
            <input
              id="register-password"
              type="password"
              className="form-input"
              placeholder={labels.passwordPlaceholder}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
              required
              minLength={8}
            />
          </div>

          <div className="form-group">
            <label htmlFor="register-occupation" className="form-label">
              {labels.occupation}
            </label>
            <input
              id="register-occupation"
              type="text"
              className="form-input"
              placeholder={labels.occupationPlaceholder}
              value={occupation}
              onChange={(e) => setOccupation(e.target.value)}
            />
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={loading || !name || !phone || password.length < 8}
            aria-busy={loading}
          >
            {loading ? (
              <>
                <span className="btn-spinner" aria-hidden="true" />
                <span>{languagePref === "hi" ? "खाता बन रहा है…" : "Creating account…"}</span>
              </>
            ) : (
              labels.submit
            )}
          </button>
        </form>

        <div className="auth-link-row">
          {labels.hasAccount}{" "}
          <Link href="/login" className="auth-link">
            {labels.login}
          </Link>
        </div>
      </main>
    </div>
  );
}

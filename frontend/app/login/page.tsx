"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { authApi } from "@/lib/api-client";
import { useAuthStore } from "@/store/useAuthStore";

export default function LoginPage() {
  const router = useRouter();
  const { setAuth, fetchMe } = useAuthStore();

  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [lang, setLang] = useState<"hi" | "en">("hi");

  const labels = {
    hi: {
      heading: "वापस आपका स्वागत है",
      sub: "अपने ArthSaathi खाते में लॉगिन करें",
      phone: "मोबाइल नंबर",
      phonePlaceholder: "+91 98765 43210",
      password: "पासवर्ड",
      passwordPlaceholder: "••••••••",
      submit: "लॉगिन करें",
      noAccount: "खाता नहीं है?",
      register: "अभी बनाएं",
    },
    en: {
      heading: "Welcome back",
      sub: "Sign in to your ArthSaathi account",
      phone: "Mobile number",
      phonePlaceholder: "+91 98765 43210",
      password: "Password",
      passwordPlaceholder: "••••••••",
      submit: "Sign in",
      noAccount: "Don't have an account?",
      register: "Create one",
    },
  }[lang];

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setGlobalError(null);
    setLoading(true);
    try {
      const cleanPhone = phone.replace(/\D/g, '');
      const formattedPhone = `+91${cleanPhone.slice(-10)}`;
      const res = await authApi.login({ phone_number: formattedPhone, password });
      // Fetch full user profile from /me
      setAuth(res.access_token, res.refresh_token, {
        id: "",
        name: "",
        role: res.role as "CITIZEN",
        language_pref: "hi",
        organization_id: null,
      });
      await fetchMe();
      router.replace("/");
    } catch (err: unknown) {
      const e = err as { message?: string; status?: number };
      if (e.status === 401) {
        setGlobalError(lang === "hi" ? "गलत नंबर या पासवर्ड" : "Wrong phone number or password");
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
            onClick={() => setLang(lang === "hi" ? "en" : "hi")}
            aria-label="Switch language"
          >
            {lang === "hi" ? "🇮🇳 हिंदी" : "🇬🇧 English"}
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
            <label htmlFor="login-phone" className="form-label">
              {labels.phone}
            </label>
            <input
              id="login-phone"
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
            <label htmlFor="login-password" className="form-label">
              {labels.password}
            </label>
            <input
              id="login-password"
              type="password"
              className="form-input"
              placeholder={labels.passwordPlaceholder}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
              minLength={8}
            />
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={loading || !phone || !password}
            aria-busy={loading}
          >
            {loading ? (
              <>
                <span className="btn-spinner" aria-hidden="true" />
                <span>{lang === "hi" ? "लोड हो रहा है…" : "Signing in…"}</span>
              </>
            ) : (
              labels.submit
            )}
          </button>
        </form>

        <div className="auth-link-row">
          {labels.noAccount}{" "}
          <Link href="/register" className="auth-link">
            {labels.register}
          </Link>
        </div>
      </main>
    </div>
  );
}

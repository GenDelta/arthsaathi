/**
 * API client for ArthSaathi authentication and core services.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface MeResponse {
  id: string;
  name: string;
  role: "CITIZEN" | "NGO_ADMIN" | "NGO_EDUCATOR" | "SPONSOR_VIEWER";
  language_pref: string;
  organization_id: string | null;
  is_onboarded: boolean;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = new Headers(options.headers);

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMessage = `HTTP Error ${response.status}`;
    try {
      const data = await response.json();
      errorMessage = data?.error?.message || data?.detail || errorMessage;
    } catch {
      // Ignore JSON parse error on non-JSON response
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

export interface TotpSetupResponse { qr_code_uri: string; secret: string; is_new_user: boolean; }
export interface TotpVerifyResponse { access_token: string; refresh_token: string; is_onboarded: boolean; }
export interface OnboardingChatResponse { reply: string; is_complete: boolean; current_profile: Record<string, any>; }

export const authApi = {
  async me(token: string): Promise<MeResponse> {
    return request<MeResponse>("/api/auth/me", {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
    });
  },

  /** Step 1: Upsert user by phone, get TOTP QR code for authenticator app. */
  async totpSetup(phone_number: string, force_reset: boolean = false): Promise<TotpSetupResponse> {
    return request<TotpSetupResponse>("/api/auth/totp/setup", {
      method: "POST",
      body: JSON.stringify({ phone_number, force_reset }),
    });
  },

  /** Step 2: Verify 6-digit TOTP code from authenticator app → receive JWT. */
  async totpVerify(phone_number: string, totp_code: string): Promise<TotpVerifyResponse> {
    return request<TotpVerifyResponse>("/api/auth/totp/verify", {
      method: "POST",
      body: JSON.stringify({ phone_number, totp_code }),
    });
  },
};

export const onboardingApi = {
  async chat(message: string, language: string, current_profile: Record<string, any>, token: string): Promise<OnboardingChatResponse> {
    return request<OnboardingChatResponse>("/api/onboarding/chat", {
      method: "POST",
      body: JSON.stringify({ message, language, current_profile }),
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  async complete(profile: Record<string, any>, token: string): Promise<{ success: boolean }> {
    return request<{ success: boolean }>("/api/onboarding/complete", {
      method: "POST",
      body: JSON.stringify({ profile }),
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  }
};

export interface ProfileResponse {
  id: string;
  name: string;
  phone_number: string;
  language_pref: string;
  employment_type?: string;
  occupation?: string;
  income_frequency?: string;
  average_income?: number;
  financial_pain_points?: string;
}

export const profileApi = {
  async getProfile(token: string): Promise<ProfileResponse> {
    return request<ProfileResponse>("/api/profile", {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
    });
  },
};

export interface ClauseMatchResult {
  clause_category: string;
  explanation: string;
}

export interface ScanStatusResponse {
  document_id: string;
  status: string;
  risk_level: string | null;
  risk_summary: string | null;
  error_message: string | null;
  matched_clauses: ClauseMatchResult[];
}

export const scamApi = {
  async initScan(file: File, token: string): Promise<{ document_id: string; status: string; extracted_text: string | null }> {
    const formData = new FormData();
    formData.append("file", file);
    return request("/api/scan-document", {
      method: "POST",
      body: formData,
      headers: { Authorization: `Bearer ${token}` },
    });
  },
  
  async verifyScan(document_id: string, verified_text: string, token: string): Promise<{ document_id: string; status: string }> {
    return request(`/api/scan-document/${document_id}/verify`, {
      method: "POST",
      body: JSON.stringify({ verified_text }),
      headers: { Authorization: `Bearer ${token}` },
    });
  },
  
  async getScanStatus(document_id: string, token: string): Promise<ScanStatusResponse> {
    return request(`/api/scan-document/${document_id}`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
    });
  },

  async getHistory(token: string): Promise<ScanStatusResponse[]> {
    return request(`/api/scan-document`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
    });
  }
};

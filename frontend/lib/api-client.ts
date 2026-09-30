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
  date_of_birth?: string;
  gender?: string;
  state_of_residence?: string;
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

export interface SchemeMatch {
  id: string;
  title: string;
  ministry: string;
  benefit_summary: string;
  application_steps: string;
  eligibility: string;
  confidence_score?: number;
}

export const schemesApi = {
  async match(token: string): Promise<{ schemes: SchemeMatch[] }> {
    return request<{ schemes: SchemeMatch[] }>("/api/schemes/match", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
  }
};

// ─── Transactions ──────────────────────────────────────────────────────────────

export interface Transaction {
  id: string;
  type: "INCOME" | "EXPENSE";
  category: string;
  amount: number;
  currency: string;
  description: string;
  occurred_at: string;
  created_at: string;
}

export interface TransactionSummary {
  total_income: number;
  total_expenses: number;
  net_savings: number;
  count: number;
}

export interface TransactionsResponse {
  transactions: Transaction[];
  summary: TransactionSummary;
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface TransactionFilters {
  type?: "INCOME" | "EXPENSE" | "all";
  category?: string;
  query?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}

export interface CategoryBreakdown {
  category: string;
  amount: number;
  percentage: number;
}

export interface BreakdownResponse {
  income: CategoryBreakdown[];
  expense: CategoryBreakdown[];
}

export const transactionsApi = {
  async getBreakdown(
    token: string,
    start_date?: string,
    end_date?: string
  ): Promise<BreakdownResponse> {
    const params = new URLSearchParams();
    if (start_date) params.set("start_date", start_date);
    if (end_date) params.set("end_date", end_date);
    const qs = params.toString();
    return request<BreakdownResponse>(
      `/api/transactions/breakdown${qs ? `?${qs}` : ""}`,
      {
        method: "GET",
        headers: { Authorization: `Bearer ${token}` },
      }
    );
  },

  async list(
    token: string,
    filters?: TransactionFilters
  ): Promise<TransactionsResponse> {
    const params = new URLSearchParams();
    if (filters?.type && filters.type !== "all") params.set("type", filters.type);
    if (filters?.category) params.set("category", filters.category);
    if (filters?.query) params.set("query", filters.query);
    if (filters?.start_date) params.set("start_date", filters.start_date);
    if (filters?.end_date) params.set("end_date", filters.end_date);
    if (filters?.page) params.set("page", String(filters.page));
    if (filters?.page_size) params.set("page_size", String(filters.page_size));
    const qs = params.toString();
    return request<TransactionsResponse>(
      `/api/transactions${qs ? `?${qs}` : ""}`,
      {
        method: "GET",
        headers: { Authorization: `Bearer ${token}` },
      }
    );
  },


  async uploadPdf(
    token: string,
    file: File,
    password?: string
  ): Promise<{ inserted: number; transactions: Transaction[] }> {
    const formData = new FormData();
    formData.append("file", file);
    if (password) formData.append("password", password);
    return request<{ inserted: number; transactions: Transaction[] }>(
      "/api/transactions/upload-pdf",
      {
        method: "POST",
        body: formData,
        headers: { Authorization: `Bearer ${token}` },
      }
    );
  },

  async voice(
    token: string,
    text: string
  ): Promise<{ transaction: Transaction }> {
    return request<{ transaction: Transaction }>("/api/transactions/voice", {
      method: "POST",
      body: JSON.stringify({ text }),
      headers: { Authorization: `Bearer ${token}` },
    });
  },

  async delete(
    token: string,
    id: string
  ): Promise<{ success: boolean }> {
    return request<{ success: boolean }>(`/api/transactions/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
  },
};

// ─── Guardian Nudges ───────────────────────────────────────────────────────────

export interface Nudge {
  id: string;
  type: "GUARDIAN_ALERT" | "MICRO_SAVINGS" | "INFO";
  title: string;
  message: string;
  actionLabel: string;
}

export const guardianApi = {
  async getNudges(
    token: string,
    start_date?: string,
    end_date?: string
  ): Promise<{ nudges: Nudge[] }> {
    const params = new URLSearchParams();
    if (start_date) params.set("start_date", start_date);
    if (end_date) params.set("end_date", end_date);
    const qs = params.toString();
    return request<{ nudges: Nudge[] }>(`/api/guardian/nudges${qs ? `?${qs}` : ""}`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
    });
  },

  async trackDebt(
    token: string,
    entity_name: string,
    total_amount: number
  ): Promise<{ success: boolean; id: string }> {
    return request<{ success: boolean; id: string }>("/api/guardian/track-debt", {
      method: "POST",
      body: JSON.stringify({ entity_name, total_amount }),
      headers: { Authorization: `Bearer ${token}` },
    });
  }
};

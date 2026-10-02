/**
 * API client for Scam Scanner endpoints.
 */

import { useAuthStore } from "@/store/useAuthStore";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ScanInitResponse {
  document_id: string;
  status: string;
  extracted_text: string | null;
}

export interface MatchedClause {
  clause_category: string;
  explanation: string;
}

export interface ScanStatusResponse {
  document_id: string;
  status: string;
  risk_level?: string;
  risk_summary?: string;
  error_message?: string;
  matched_clauses?: MatchedClause[];
}

function getAuthHeaders(): Record<string, string> {
  const token = useAuthStore.getState().accessToken;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const scamApi = {
  async uploadDocument(file: File): Promise<ScanInitResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/api/scan-document`, {
      method: "POST",
      headers: {
        ...getAuthHeaders(),
      },
      body: formData,
    });

    if (!response.ok) {
      let errorMessage = `HTTP Error ${response.status}`;
      try {
        const data = await response.json();
        errorMessage = data?.error?.message || data?.detail || errorMessage;
      } catch {
        // Fallback to generic message
      }
      throw new Error(errorMessage);
    }

    return response.json();
  },

  async verifyDocument(documentId: string, verifiedText: string): Promise<{ document_id: string; status: string }> {
    const response = await fetch(`${API_BASE_URL}/api/scan-document/${documentId}/verify`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify({ verified_text: verifiedText }),
    });

    if (!response.ok) {
      let errorMessage = `HTTP Error ${response.status}`;
      try {
        const data = await response.json();
        errorMessage = data?.error?.message || data?.detail || errorMessage;
      } catch {
        // Fallback to generic message
      }
      throw new Error(errorMessage);
    }

    return response.json();
  },

  async getStatus(documentId: string): Promise<ScanStatusResponse> {
    const response = await fetch(`${API_BASE_URL}/api/scan-document/${documentId}`, {
      method: "GET",
      headers: {
        ...getAuthHeaders(),
      },
    });

    if (!response.ok) {
      let errorMessage = `HTTP Error ${response.status}`;
      try {
        const data = await response.json();
        errorMessage = data?.error?.message || data?.detail || errorMessage;
      } catch {
        // Fallback to generic message
      }
      throw new Error(errorMessage);
    }

    return response.json();
  },
};

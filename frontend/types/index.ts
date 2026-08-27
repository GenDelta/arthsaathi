/**
 * Shared TypeScript types for ArthSaathi frontend.
 *
 * Types used across 3+ components are promoted here (AGENT_INSTRUCTIONS.md §3).
 * Component-local types stay co-located in their respective files.
 */

// ─── API error shape ───────────────────────────────────────────────────────────
export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
  };
}

// ─── Auth ─────────────────────────────────────────────────────────────────────
export type UserRole = 'CITIZEN' | 'NGO_ADMIN' | 'NGO_EDUCATOR' | 'SPONSOR_VIEWER';

export interface AuthUser {
  id: string;
  name: string;
  role: UserRole;
  language_pref: string;
  organization_id: string | null;
}

// ─── Transactions ─────────────────────────────────────────────────────────────
export type TransactionType = 'INCOME' | 'EXPENSE';

export type TransactionCategory =
  | 'GIG_WAGE'
  | 'AGRICULTURAL_SALE'
  | 'OTHER_INCOME'
  | 'FOOD'
  | 'TRANSPORT'
  | 'UTILITIES'
  | 'DEBT_REPAYMENT'
  | 'DISCRETIONARY'
  | 'HEALTHCARE'
  | 'OTHER_EXPENSE';

// ─── Nudges ───────────────────────────────────────────────────────────────────
export type NudgeType = 'MICRO_SAVINGS' | 'GUARDIAN_ALERT';
export type NudgeStatus = 'PENDING' | 'APPROVED' | 'DISMISSED';

// ─── Documents ────────────────────────────────────────────────────────────────
export type DocumentStatus =
  | 'PENDING_OCR'
  | 'PENDING_VERIFICATION'
  | 'ANALYZING'
  | 'ANALYZED'
  | 'FAILED';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

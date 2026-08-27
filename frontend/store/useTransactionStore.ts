/**
 * Transaction store (Zustand slice) — ARCHITECTURE.md §1.2, AGENT_INSTRUCTIONS.md §3
 *
 * Manages: transaction list, pagination state, loading flags.
 */

import { create } from 'zustand';

export interface Transaction {
  id: string;
  type: 'INCOME' | 'EXPENSE';
  category: string;
  amount: number;
  currency: string;
  description: string | null;
  occurred_at: string;
  created_at: string;
}

interface TransactionState {
  transactions: Transaction[];
  total: number;
  isLoading: boolean;

  setTransactions: (transactions: Transaction[], total: number) => void;
  prependTransaction: (transaction: Transaction) => void;
  setLoading: (loading: boolean) => void;
}

export const useTransactionStore = create<TransactionState>((set) => ({
  transactions: [],
  total: 0,
  isLoading: false,

  setTransactions: (transactions, total) => set({ transactions, total }),
  prependTransaction: (transaction) =>
    set((state) => ({
      transactions: [transaction, ...state.transactions],
      total: state.total + 1,
    })),
  setLoading: (isLoading) => set({ isLoading }),
}));

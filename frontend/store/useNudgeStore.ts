/**
 * Nudge store (Zustand slice) — ARCHITECTURE.md §1.2, AGENT_INSTRUCTIONS.md §3
 *
 * Manages: pending nudges list, approve/dismiss optimistic updates.
 */

import { create } from 'zustand';

export interface Nudge {
  nudge_id: string;
  nudge_type: 'MICRO_SAVINGS' | 'GUARDIAN_ALERT';
  message: string;
  suggested_amount: number | null;
  risk_score: number | null;
  acknowledged_status: 'PENDING' | 'APPROVED' | 'DISMISSED';
}

interface NudgeState {
  nudges: Nudge[];
  pendingNudge: Nudge | null;  // nudge returned inline with a log-transaction response

  setNudges: (nudges: Nudge[]) => void;
  setPendingNudge: (nudge: Nudge | null) => void;
  resolveNudge: (nudgeId: string, status: 'APPROVED' | 'DISMISSED') => void;
}

export const useNudgeStore = create<NudgeState>((set) => ({
  nudges: [],
  pendingNudge: null,

  setNudges: (nudges) => set({ nudges }),
  setPendingNudge: (pendingNudge) => set({ pendingNudge }),
  resolveNudge: (nudgeId, status) =>
    set((state) => ({
      nudges: state.nudges.map((n) =>
        n.nudge_id === nudgeId ? { ...n, acknowledged_status: status } : n
      ),
      pendingNudge:
        state.pendingNudge?.nudge_id === nudgeId ? null : state.pendingNudge,
    })),
}));

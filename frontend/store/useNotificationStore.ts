/**
 * Notification store (Zustand slice) — ARCHITECTURE.md §1.2, AGENT_INSTRUCTIONS.md §3
 *
 * Manages: Guardian alert notifications received over SSE stream.
 */

import { create } from 'zustand';

export interface Notification {
  nudge_id: string;
  message: string;
  received_at: string;
  dismissed: boolean;
}

interface NotificationState {
  notifications: Notification[];

  addNotification: (nudge_id: string, message: string) => void;
  dismissNotification: (nudge_id: string) => void;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],

  addNotification: (nudge_id, message) =>
    set((state) => ({
      notifications: [
        ...state.notifications,
        { nudge_id, message, received_at: new Date().toISOString(), dismissed: false },
      ],
    })),

  dismissNotification: (nudge_id) =>
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.nudge_id === nudge_id ? { ...n, dismissed: true } : n
      ),
    })),
}));

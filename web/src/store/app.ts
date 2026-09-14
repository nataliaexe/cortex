import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type ViewId =
  | 'chat'
  | 'calendar'
  | 'notes'
  | 'memory'
  | 'audit'
  | 'settings';

interface AppState {
  currentView: ViewId;
  setCurrentView: (v: ViewId) => void;

  sessionId: string | null;
  setSessionId: (id: string | null) => void;

  rightPanelOpen: boolean;
  toggleRightPanel: () => void;

  sidebarOpen: boolean;
  toggleSidebar: () => void;

  // historico de sessoes visitadas (ids)
  recentSessionIds: string[];
  addRecentSession: (id: string) => void;
  clearRecentSessions: () => void;
}

export const useApp = create<AppState>()(
  persist(
    (set) => ({
      currentView: 'chat',
      setCurrentView: (v) => set({ currentView: v }),

      sessionId: null,
      setSessionId: (id) => {
        set({ sessionId: id });
        if (id) {
          set((s) => {
            const recent = [id, ...s.recentSessionIds.filter((x) => x !== id)].slice(0, 30);
            return { recentSessionIds: recent };
          });
        }
      },

      rightPanelOpen: true,
      toggleRightPanel: () => set((s) => ({ rightPanelOpen: !s.rightPanelOpen })),

      sidebarOpen: true,
      toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),

      recentSessionIds: [],
      addRecentSession: (id) =>
        set((s) => {
          const recent = [id, ...s.recentSessionIds.filter((x) => x !== id)].slice(0, 30);
          return { recentSessionIds: recent };
        }),
      clearRecentSessions: () => set({ recentSessionIds: [] }),
    }),
    {
      name: 'cortex-app-state',
      partialize: (state) => ({
        currentView: state.currentView,
        sessionId: state.sessionId,
        rightPanelOpen: state.rightPanelOpen,
        recentSessionIds: state.recentSessionIds,
      }),
    }
  )
);

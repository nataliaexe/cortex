import { create } from 'zustand';
import type { ChatMessageDisplay } from '@/types/chat';

interface ChatStore {
  messages: ChatMessageDisplay[];
  setMessages: (m: ChatMessageDisplay[]) => void;
  appendMessage: (m: ChatMessageDisplay) => void;
  updateMessage: (id: string, updater: (m: ChatMessageDisplay) => ChatMessageDisplay) => void;
  clear: () => void;
  // flag para saber se ja carregamos a sessao do backend
  loadedForSession: string | null;
  setLoadedForSession: (id: string | null) => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  setMessages: (messages) => set({ messages }),
  appendMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),
  updateMessage: (id, updater) =>
    set((s) => ({
      messages: s.messages.map((m) => (m.id === id ? updater(m) : m)),
    })),
  clear: () => set({ messages: [], loadedForSession: null }),
  loadedForSession: null,
  setLoadedForSession: (id) => set({ loadedForSession: id }),
}));

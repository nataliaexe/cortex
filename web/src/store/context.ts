import { create } from 'zustand';
import type { ToolCallDisplay, PlanStepDisplay } from '@/types/chat';

interface LiveContext {
  provider: string | null;
  model: string | null;
  streaming: boolean;

  plan: PlanStepDisplay[];
  toolCalls: ToolCallDisplay[];
  tokensApprox: number;

  // acoes
  setProvider: (p: string | null, m: string | null) => void;
  setStreaming: (s: boolean) => void;
  setPlan: (steps: PlanStepDisplay[]) => void;
  setToolCalls: (calls: ToolCallDisplay[]) => void;
  appendToken: (n: number) => void;
  reset: () => void;
}

export const useLiveContext = create<LiveContext>((set) => ({
  provider: null,
  model: null,
  streaming: false,
  plan: [],
  toolCalls: [],
  tokensApprox: 0,

  setProvider: (provider, model) => set({ provider, model }),
  setStreaming: (streaming) => set({ streaming }),
  setPlan: (plan) => set({ plan }),
  setToolCalls: (toolCalls) => set({ toolCalls }),
  appendToken: (n) => set((s) => ({ tokensApprox: s.tokensApprox + n })),
  reset: () => set({
    provider: null, model: null, streaming: false,
    plan: [], toolCalls: [], tokensApprox: 0,
  }),
}));

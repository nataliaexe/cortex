import { create } from 'zustand';
import { Check, X, AlertTriangle, Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useEffect } from 'react';

export type ToastKind = 'success' | 'error' | 'warning' | 'info';

interface ToastItem {
  id: string;
  kind: ToastKind;
  title: string;
  description?: string;
}

interface ToastStore {
  toasts: ToastItem[];
  push: (t: Omit<ToastItem, 'id'>) => void;
  dismiss: (id: string) => void;
}

export const useToast = create<ToastStore>((set) => ({
  toasts: [],
  push: (t) => {
    const id = `${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
    set((s) => ({ toasts: [...s.toasts, { ...t, id }] }));
    // auto-dismiss depois de 4s
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((x) => x.id !== id) }));
    }, 4000);
  },
  dismiss: (id) => set((s) => ({ toasts: s.toasts.filter((x) => x.id !== id) })),
}));

const KIND_STYLE: Record<ToastKind, { bg: string; text: string; Icon: any }> = {
  success: { bg: 'bg-state-success/15 border-state-success/40', text: 'text-state-success', Icon: Check },
  error:   { bg: 'bg-state-danger/15 border-state-danger/40',   text: 'text-state-danger',   Icon: X },
  warning: { bg: 'bg-state-warning/15 border-state-warning/40', text: 'text-state-warning', Icon: AlertTriangle },
  info:    { bg: 'bg-state-info/15 border-state-info/40',       text: 'text-state-info',    Icon: Info },
};

export function ToastContainer() {
  const { toasts, dismiss } = useToast();

  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((t) => {
        const { bg, text, Icon } = KIND_STYLE[t.kind];
        return (
          <div
            key={t.id}
            className={cn(
              'pointer-events-auto flex w-80 items-start gap-2 rounded-md border bg-bg-panel p-3 shadow-lg animate-fade-in',
              bg
            )}
          >
            <Icon size={14} className={cn('mt-0.5 shrink-0', text)} />
            <div className="min-w-0 flex-1">
              <div className={cn('text-sm font-medium', text)}>{t.title}</div>
              {t.description && (
                <div className="mt-0.5 text-2xs text-fg-muted">{t.description}</div>
              )}
            </div>
            <button
              onClick={() => dismiss(t.id)}
              className="shrink-0 rounded p-0.5 text-fg-dim hover:bg-bg-hover"
            >
              <X size={12} />
            </button>
          </div>
        );
      })}
    </div>
  );
}

import { useState } from 'react';
import { ChevronDown, Languages, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

const MODES = [
  { id: 'default', label: 'Padrao', description: 'assistente geral', icon: Sparkles },
  { id: 'english', label: 'English', description: 'tutor de ingles', icon: Languages },
];

interface Props {
  value: string;
  onChange: (mode: string) => void;
}

export function ModeSelector({ value, onChange }: Props) {
  const [open, setOpen] = useState(false);
  const current = MODES.find((m) => m.id === value) || MODES[0];
  const Icon = current.icon;

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 rounded-md border border-bg-border bg-bg-elevated px-2.5 py-1 text-xs text-fg-base hover:bg-bg-hover"
        type="button"
      >
        <Icon size={12} />
        <span>{current.label}</span>
        <ChevronDown size={12} className="text-fg-dim" />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute left-0 top-full z-50 mt-1 w-56 rounded-md border border-bg-border bg-bg-panel p-1 shadow-lg">
            {MODES.map((m) => {
              const Icon = m.icon;
              const active = m.id === value;
              return (
                <button
                  key={m.id}
                  onClick={() => {
                    onChange(m.id);
                    setOpen(false);
                  }}
                  className={cn(
                    'flex w-full items-start gap-2 rounded px-2 py-1.5 text-left transition-colors',
                    active ? 'bg-accent/15' : 'hover:bg-bg-hover'
                  )}
                  type="button"
                >
                  <Icon size={14} className={cn('mt-0.5', active ? 'text-accent-soft' : 'text-fg-muted')} />
                  <div className="flex-1">
                    <div className={cn('text-xs', active ? 'text-accent-soft font-medium' : 'text-fg-base')}>
                      {m.label}
                    </div>
                    <div className="text-2xs text-fg-dim">{m.description}</div>
                  </div>
                </button>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

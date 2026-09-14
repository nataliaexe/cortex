import { useState } from 'react';
import { ChevronRight, Check, X, Loader2, ShieldX } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ToolCallDisplay } from '@/types/chat';

interface Props {
  call: ToolCallDisplay;
}

export function ToolCallBlock({ call }: Props) {
  const [open, setOpen] = useState(false);

  const statusIcon = {
    running: <Loader2 size={12} className="animate-spin text-accent-soft" />,
    ok: <Check size={12} className="text-state-success" />,
    error: <X size={12} className="text-state-danger" />,
    denied: <ShieldX size={12} className="text-state-warning" />,
  }[call.status];

  const statusLabel = {
    running: 'executando',
    ok: 'ok',
    error: 'erro',
    denied: 'negado',
  }[call.status];

  return (
    <div className="my-1.5 rounded border border-bg-border bg-bg-panel">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-2 px-2 py-1.5 text-left hover:bg-bg-hover transition-colors"
      >
        <ChevronRight
          size={12}
          className={cn(
            'text-fg-dim transition-transform',
            open && 'rotate-90'
          )}
        />
        {statusIcon}
        <span className="font-mono text-xs text-fg-base">{call.tool}</span>
        <span className="text-2xs text-fg-dim">{statusLabel}</span>
      </button>

      {open && (
        <div className="border-t border-bg-border p-2">
          {Object.keys(call.args).length > 0 && (
            <div className="mb-2">
              <div className="mb-1 text-2xs font-medium uppercase tracking-wider text-fg-dim">
                Argumentos
              </div>
              <pre className="overflow-x-auto rounded bg-bg-base p-2 font-mono text-2xs text-fg-muted">
                {JSON.stringify(call.args, null, 2)}
              </pre>
            </div>
          )}

          {call.output && (
            <div className="mb-2">
              <div className="mb-1 text-2xs font-medium uppercase tracking-wider text-fg-dim">
                Saida
              </div>
              <pre className="max-h-64 overflow-auto rounded bg-bg-base p-2 font-mono text-2xs text-fg-base whitespace-pre-wrap">
                {call.output}
              </pre>
            </div>
          )}

          {call.error && (
            <div>
              <div className="mb-1 text-2xs font-medium uppercase tracking-wider text-fg-dim">
                Erro
              </div>
              <pre className="overflow-x-auto rounded bg-bg-base p-2 font-mono text-2xs text-state-danger whitespace-pre-wrap">
                {call.error}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

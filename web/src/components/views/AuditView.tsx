import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Shield, Filter } from 'lucide-react';
import { fetchAudit, type AuditEntry } from '@/lib/api';
import { cn } from '@/lib/utils';

export function AuditView() {
  const [decision, setDecision] = useState<string>('');
  const [tool, setTool] = useState<string>('');

  const q = useQuery({
    queryKey: ['audit', decision, tool],
    queryFn: () => fetchAudit({
      limit: 200,
      decision: decision || undefined,
      tool: tool || undefined,
    }),
  });

  const decisions = ['allow', 'deny', 'dry_run'];

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b border-bg-border px-4 py-2">
        <Filter size={12} className="text-fg-dim" />
        <div className="flex items-center gap-1">
          <button
            onClick={() => setDecision('')}
            className={cn(
              'rounded px-2 py-1 text-xs',
              !decision ? 'bg-accent/15 text-accent-soft' : 'text-fg-muted hover:bg-bg-hover'
            )}
          >
            todas
          </button>
          {decisions.map((d) => (
            <button
              key={d}
              onClick={() => setDecision(d)}
              className={cn(
                'rounded px-2 py-1 text-xs',
                decision === d ? 'bg-accent/15 text-accent-soft' : 'text-fg-muted hover:bg-bg-hover'
              )}
            >
              {d}
            </button>
          ))}
        </div>
        <input
          value={tool}
          onChange={(e) => setTool(e.target.value)}
          placeholder="filtrar por tool..."
          className="input ml-auto max-w-xs"
        />
      </div>

      <div className="flex-1 overflow-y-auto">
        {q.isLoading && <div className="p-8 text-center text-sm text-fg-dim">Carregando...</div>}
        {q.data && q.data.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <Shield size={24} className="mb-2 text-fg-dim" />
            <div className="text-sm text-fg-muted">Nenhuma entrada de auditoria</div>
          </div>
        )}
        {q.data && q.data.length > 0 && (
          <div className="mx-auto max-w-4xl p-4">
            {q.data.map((e) => (
              <AuditRow key={e.id} entry={e} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function AuditRow({ entry }: { entry: AuditEntry }) {
  const [open, setOpen] = useState(false);

  const color =
    entry.decision === 'allow'
      ? 'text-state-success'
      : entry.decision === 'deny'
      ? 'text-state-danger'
      : 'text-state-warning';

  const bg =
    entry.decision === 'allow'
      ? 'bg-state-success/10'
      : entry.decision === 'deny'
      ? 'bg-state-danger/10'
      : 'bg-state-warning/10';

  return (
    <div className={cn('mb-1.5 rounded border border-bg-border', bg)}>
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-3 px-3 py-1.5 text-left text-xs hover:bg-bg-hover/40"
      >
        <span className="w-28 shrink-0 text-fg-dim">
          {new Date(entry.ts).toLocaleString('pt-BR', {
            day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit',
          })}
        </span>
        <span className="w-32 shrink-0 font-mono text-fg-base">{entry.tool}</span>
        <span className={cn('w-20 shrink-0 font-medium', color)}>{entry.decision}</span>
        <span className="flex-1 truncate text-fg-muted">{entry.reason || ''}</span>
      </button>
      {open && (
        <div className="border-t border-bg-border p-3">
          <div className="mb-2">
            <div className="mb-1 text-2xs uppercase tracking-wider text-fg-dim">Argumentos</div>
            <pre className="overflow-x-auto rounded bg-bg-base p-2 font-mono text-2xs text-fg-muted">
              {JSON.stringify(entry.args, null, 2)}
            </pre>
          </div>
          {entry.result && (
            <div>
              <div className="mb-1 text-2xs uppercase tracking-wider text-fg-dim">Resultado</div>
              <pre className="overflow-x-auto rounded bg-bg-base p-2 font-mono text-2xs text-fg-base">
                {entry.result}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

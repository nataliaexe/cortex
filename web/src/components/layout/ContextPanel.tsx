import {
  Activity,
  Cpu,
  Coins,
  Wrench,
  Loader2,
  Check,
  X,
  ShieldX,
  Circle,
  ArrowDownToLine,
  X as XIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useLiveContext } from '@/store/context';
import { useApp } from '@/store/app';

export function ContextPanel() {
  const { toggleRightPanel } = useApp();
  const live = useLiveContext();

  const toolsOk = live.toolCalls.filter((t) => t.status === 'ok').length;
  const toolsError = live.toolCalls.filter((t) => t.status === 'error').length;
  const toolsDenied = live.toolCalls.filter((t) => t.status === 'denied').length;

  return (
    <aside className="flex h-full w-72 flex-col border-l border-bg-border bg-bg-panel">
      <div className="flex h-12 shrink-0 items-center justify-between border-b border-bg-border px-3">
        <div className="flex items-center gap-2">
          <Activity size={14} className="text-fg-muted" />
          <span className="text-sm font-medium text-fg-base">Contexto</span>
          {live.streaming && (
            <Loader2 size={10} className="animate-spin text-accent-soft" />
          )}
        </div>
        <button
          onClick={toggleRightPanel}
          className="rounded p-1 text-fg-dim hover:bg-bg-hover hover:text-fg-base"
          title="Fechar painel"
        >
          <XIcon size={14} />
        </button>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto p-3">
        <Section icon={<Cpu size={10} />} title="Provider">
          {live.provider ? (
            <div className="flex items-baseline justify-between">
              <span className="text-sm text-fg-base">{live.provider}</span>
              <span className="font-mono text-2xs text-fg-dim">{live.model}</span>
            </div>
          ) : (
            <div className="text-xs text-fg-dim">aguardando</div>
          )}
        </Section>

        <Section icon={<Coins size={10} />} title="Tokens">
          {live.tokensApprox === 0 ? (
            <div className="text-xs text-fg-dim">-</div>
          ) : (
            <div className="text-sm text-fg-base">
              ~{live.tokensApprox.toLocaleString('pt-BR')}
              <span className="ml-1 text-2xs text-fg-dim">(aprox)</span>
            </div>
          )}
        </Section>

        <Section icon={<Wrench size={10} />} title="Tools">
          {live.toolCalls.length === 0 ? (
            <div className="text-xs text-fg-dim">nenhuma ainda</div>
          ) : (
            <div className="space-y-1">
              <div className="flex gap-3 text-2xs">
                <span className="flex items-center gap-1 text-state-success">
                  <Check size={10} /> {toolsOk}
                </span>
                {toolsError > 0 && (
                  <span className="flex items-center gap-1 text-state-danger">
                    <X size={10} /> {toolsError}
                  </span>
                )}
                {toolsDenied > 0 && (
                  <span className="flex items-center gap-1 text-state-warning">
                    <ShieldX size={10} /> {toolsDenied}
                  </span>
                )}
              </div>

              <div className="mt-2 space-y-1">
                {live.toolCalls.map((t) => (
                  <ToolMiniRow key={t.id} tool={t.tool} status={t.status} />
                ))}
              </div>
            </div>
          )}
        </Section>

        <Section icon={<ArrowDownToLine size={10} />} title="Plano">
          {live.plan.length === 0 ? (
            <div className="text-xs text-fg-dim">nenhum plano em execucao</div>
          ) : (
            <ul className="space-y-1.5">
              {live.plan.map((s, i) => (
                <li key={i} className="flex items-start gap-1.5 text-xs">
                  {s.done ? (
                    <Check size={10} className="mt-0.5 shrink-0 text-state-success" />
                  ) : (
                    <Circle size={10} className="mt-0.5 shrink-0 text-fg-dim" />
                  )}
                  <div className="min-w-0 flex-1">
                    <div className="text-fg-base">{s.description}</div>
                    {s.tool && (
                      <div className="font-mono text-2xs text-fg-dim">{s.tool}</div>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Section>

        <Section title="Sessao">
          <SessionInfo />
        </Section>
      </div>
    </aside>
  );
}

function Section({
  icon,
  title,
  children,
}: {
  icon?: React.ReactNode;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section>
      <h3 className="mb-2 flex items-center gap-1.5 text-2xs font-medium uppercase tracking-wider text-fg-dim">
        {icon}
        {title}
      </h3>
      <div className="panel-elevated p-2">{children}</div>
    </section>
  );
}

function ToolMiniRow({
  tool,
  status,
}: {
  tool: string;
  status: 'running' | 'ok' | 'error' | 'denied';
}) {
  const icon = {
    running: <Loader2 size={10} className="animate-spin text-accent-soft" />,
    ok: <Check size={10} className="text-state-success" />,
    error: <X size={10} className="text-state-danger" />,
    denied: <ShieldX size={10} className="text-state-warning" />,
  }[status];

  return (
    <div className="flex items-center gap-1.5 font-mono text-2xs text-fg-muted">
      {icon}
      <span className="truncate">{tool}</span>
    </div>
  );
}

function SessionInfo() {
  const { sessionId } = useApp();
  return (
    <div className="text-2xs text-fg-muted">
      {sessionId ? (
        <span className="font-mono">{sessionId.slice(0, 8)}</span>
      ) : (
        <span className="text-fg-dim">nenhuma ainda</span>
      )}
    </div>
  );
}

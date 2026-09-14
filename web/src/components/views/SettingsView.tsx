import { useQuery } from '@tanstack/react-query';
import { Check, X, Settings as SettingsIcon, Zap } from 'lucide-react';
import { fetchProviders, fetchHealth } from '@/lib/api';
import { useApp } from '@/store/app';
import { cn } from '@/lib/utils';

export function SettingsView() {
  const providersQ = useQuery({ queryKey: ['providers'], queryFn: fetchProviders });
  const healthQ = useQuery({ queryKey: ['health'], queryFn: fetchHealth });
  const { currentView } = useApp();

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-3xl space-y-6 p-6">
        {/* sobre */}
        <section>
          <h2 className="mb-3 flex items-center gap-2 text-md font-medium text-fg-base">
            <SettingsIcon size={16} />
            Sobre
          </h2>
          <div className="panel p-4 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-fg-muted">Versao</span>
              <span className="font-mono text-fg-base">{healthQ.data?.version || '-'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-fg-muted">Status</span>
              <span className={cn(
                'font-medium',
                healthQ.data?.status === 'ok' ? 'text-state-success' : 'text-state-danger'
              )}>
                {healthQ.data?.status || 'desconhecido'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-fg-muted">Providers ativos</span>
              <span className="font-mono text-fg-base">
                {healthQ.data?.providers_available?.join(', ') || '-'}
              </span>
            </div>
          </div>
        </section>

        {/* providers */}
        <section>
          <h2 className="mb-3 flex items-center gap-2 text-md font-medium text-fg-base">
            <Zap size={16} />
            Providers
          </h2>
          <div className="space-y-2">
            {providersQ.data?.map((p) => (
              <div key={p.name} className="panel p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className={cn(
                        'flex h-7 w-7 items-center justify-center rounded',
                        p.available
                          ? 'bg-state-success/15 text-state-success'
                          : 'bg-bg-hover text-fg-dim'
                      )}
                    >
                      {p.available ? <Check size={12} /> : <X size={12} />}
                    </div>
                    <div>
                      <div className="text-sm font-medium text-fg-base">{p.name}</div>
                      <div className="text-2xs text-fg-dim">{p.reason}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {p.enabled && (
                      <span className="badge-success">habilitado</span>
                    )}
                    {!p.enabled && (
                      <span className="badge-muted">desabilitado</span>
                    )}
                    {p.available && (
                      <span className="badge-info">disponivel</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* modos */}
        <section>
          <h2 className="mb-3 text-md font-medium text-fg-base">Modos de chat</h2>
          <div className="panel p-4 text-sm text-fg-muted">
            <div className="mb-2">
              Os modos permitem mudar a personalidade do Cortex. Hoje disponiveis:
            </div>
            <div className="space-y-1 text-xs">
              <div>
                <span className="font-mono text-fg-base">default</span>
                {' - '}assistente geral, direto e racional
              </div>
              <div>
                <span className="font-mono text-fg-base">english</span>
                {' - '}tutor de ingles
              </div>
            </div>
            <div className="mt-3 text-2xs text-fg-dim">
              Para usar, digite <span className="font-mono text-accent-soft">:mode english</span> no chat ou no CLI.
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

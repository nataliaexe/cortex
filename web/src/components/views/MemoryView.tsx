import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Brain, Database, Sparkles, BookOpen } from 'lucide-react';
import { fetchEpisodic, fetchSemantic, fetchMemoryStats } from '@/lib/api';
import { cn } from '@/lib/utils';

type Tab = 'stats' | 'episodic' | 'semantic';

export function MemoryView() {
  const [tab, setTab] = useState<Tab>('stats');

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-1 border-b border-bg-border px-4 py-2">
        {[
          { id: 'stats', label: 'Estatisticas', icon: Database },
          { id: 'episodic', label: 'Episodica', icon: BookOpen },
          { id: 'semantic', label: 'Semantica', icon: Sparkles },
        ].map((t) => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id as Tab)}
              className={cn(
                'flex items-center gap-1.5 rounded px-2 py-1 text-xs transition-colors',
                tab === t.id
                  ? 'bg-accent/15 text-accent-soft'
                  : 'text-fg-muted hover:bg-bg-hover hover:text-fg-base'
              )}
            >
              <Icon size={12} />
              {t.label}
            </button>
          );
        })}
      </div>

      <div className="flex-1 overflow-y-auto">
        {tab === 'stats' && <StatsTab />}
        {tab === 'episodic' && <EpisodicTab />}
        {tab === 'semantic' && <SemanticTab />}
      </div>
    </div>
  );
}

function StatsTab() {
  const q = useQuery({ queryKey: ['memory-stats'], queryFn: fetchMemoryStats });
  if (q.isLoading) return <div className="p-8 text-center text-sm text-fg-dim">Carregando...</div>;
  if (!q.data) return null;

  const labels: Record<string, string> = {
    sessions: 'Sessoes',
    messages: 'Mensagens',
    episodic: 'Memoria episodica',
    semantic: 'Memoria semantica',
    projects: 'Projetos',
    project_sources: 'Fontes indexadas',
    embeddings: 'Vetores (embeddings)',
    notes: 'Notas',
    timers: 'Timers',
    reminders: 'Lembretes',
    calendar_events: 'Eventos de calendario',
    audit: 'Entradas de auditoria',
  };

  return (
    <div className="mx-auto max-w-3xl p-4">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
        {Object.entries(q.data).map(([k, v]) => (
          <div key={k} className="panel p-3">
            <div className="text-2xs uppercase tracking-wider text-fg-dim">
              {labels[k] || k}
            </div>
            <div className="mt-1 text-xl font-semibold text-fg-base">
              {v.toLocaleString('pt-BR')}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function EpisodicTab() {
  const q = useQuery({
    queryKey: ['episodic'],
    queryFn: () => fetchEpisodic(100),
  });

  if (q.isLoading) return <div className="p-8 text-center text-sm text-fg-dim">Carregando...</div>;
  if (!q.data || q.data.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-center">
        <BookOpen size={24} className="mb-2 text-fg-dim" />
        <div className="text-sm text-fg-muted">Nenhuma memoria episodica</div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl p-4">
      {q.data.map((e) => (
        <div key={e.id} className="mb-2 rounded border border-bg-border bg-bg-panel p-3">
          <div className="flex items-start justify-between gap-2">
            <h3 className="text-sm font-medium text-fg-base">{e.summary}</h3>
            <span className="shrink-0 text-2xs text-fg-dim">
              {new Date(e.ts).toLocaleString('pt-BR', {
                day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
              })}
            </span>
          </div>
          <p className="mt-1 text-xs text-fg-muted whitespace-pre-wrap line-clamp-3">
            {e.content}
          </p>
          {e.tags && (
            <div className="mt-2 flex flex-wrap gap-1">
              {e.tags.split(',').filter(Boolean).map((t) => (
                <span key={t} className="badge-muted">{t}</span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function SemanticTab() {
  const q = useQuery({
    queryKey: ['semantic'],
    queryFn: () => fetchSemantic(200),
  });

  if (q.isLoading) return <div className="p-8 text-center text-sm text-fg-dim">Carregando...</div>;
  if (!q.data || q.data.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-center">
        <Sparkles size={24} className="mb-2 text-fg-dim" />
        <div className="text-sm text-fg-muted">Nenhuma memoria semantica</div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl p-4">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-bg-border text-left text-2xs uppercase tracking-wider text-fg-dim">
            <th className="pb-2">Chave</th>
            <th className="pb-2">Valor</th>
            <th className="pb-2 text-right">Confianca</th>
          </tr>
        </thead>
        <tbody>
          {q.data.map((e) => (
            <tr key={e.id} className="border-b border-bg-border/50">
              <td className="py-2 font-mono text-fg-base">{e.key}</td>
              <td className="py-2 text-fg-muted">{e.value}</td>
              <td className="py-2 text-right text-fg-dim">
                {(e.confidence * 100).toFixed(0)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

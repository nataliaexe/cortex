import { useQuery } from '@tanstack/react-query';
import { MessageSquare, Loader2 } from 'lucide-react';
import { fetchSessions } from '@/lib/api';
import { useApp } from '@/store/app';
import { cn } from '@/lib/utils';

export function RecentSessions() {
  const { sessionId, setSessionId, setCurrentView } = useApp();

  const q = useQuery({
    queryKey: ['sessions-recent'],
    queryFn: () => fetchSessions(),
    refetchInterval: 30_000, // revalida a cada 30s
  });

  // filtra sessoes vazias (sem titulo e sem mensagens -- o backend nao filtra)
  const sessions = (q.data || []).slice(0, 15);

  if (q.isLoading) {
    return (
      <div className="flex items-center gap-2 px-2 py-1.5 text-xs text-fg-dim">
        <Loader2 size={10} className="animate-spin" />
        carregando...
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div className="px-2 py-1.5 text-2xs text-fg-dim">
        nenhuma conversa ainda
      </div>
    );
  }

  return (
    <div className="space-y-0.5">
      {sessions.map((s) => {
        const active = s.id === sessionId;
        // titulo: usa o titulo se tiver, senao o id curto
        const label = s.title && s.title !== 'repl'
          ? s.title
          : `conversa ${s.id.slice(0, 6)}`;
        const date = new Date(s.updated_at);
        const dateLabel = date.toLocaleDateString('pt-BR', {
          day: '2-digit',
          month: '2-digit',
        });

        return (
          <button
            key={s.id}
            onClick={() => {
              setSessionId(s.id);
              setCurrentView('chat');
            }}
            className={cn(
              'group flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-xs transition-colors',
              active
                ? 'bg-accent/15 text-accent-soft'
                : 'text-fg-muted hover:bg-bg-hover hover:text-fg-base'
            )}
            title={s.id}
          >
            <MessageSquare
              size={11}
              className={cn('shrink-0', active ? 'text-accent-soft' : 'text-fg-dim')}
            />
            <span className="flex-1 truncate">{label}</span>
            <span className="shrink-0 text-2xs text-fg-dim">{dateLabel}</span>
          </button>
        );
      })}
    </div>
  );
}

import {
  MessageSquare,
  Calendar,
  StickyNote,
  Brain,
  Shield,
  Settings,
  Plus,
  Circle,
} from 'lucide-react';
import { useApp, type ViewId } from '@/store/app';
import { cn } from '@/lib/utils';
import { RecentSessions } from './RecentSessions';
import { useChatStore } from '@/store/chat';

interface NavItem {
  id: ViewId;
  label: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'chat', label: 'Chat', icon: MessageSquare },
  { id: 'calendar', label: 'Calendario', icon: Calendar },
  { id: 'notes', label: 'Notas', icon: StickyNote },
  { id: 'memory', label: 'Memoria', icon: Brain },
  { id: 'audit', label: 'Auditoria', icon: Shield },
  { id: 'settings', label: 'Configuracoes', icon: Settings },
];

export function Sidebar() {
  const { currentView, setCurrentView, sessionId, setSessionId } = useApp();

  const handleNewSession = () => {
    setSessionId(null);
    setCurrentView('chat');
    useChatStore.getState().clear();
  };

  return (
    <aside className="flex h-full w-56 flex-col overflow-hidden border-r border-bg-border bg-bg-panel">
      {/* header */}
      <div className="flex h-12 items-center justify-between border-b border-bg-border px-3">
        <div className="flex items-center gap-2">
          <div className="h-5 w-5 rounded bg-accent" />
          <span className="text-md font-semibold text-fg-base">Cortex</span>
        </div>
      </div>

      {/* acao principal */}
      <div className="p-2">
        <button
          onClick={handleNewSession}
          className="btn-outline w-full justify-start gap-2"
        >
          <Plus size={14} />
          <span>Nova conversa</span>
        </button>
      </div>

      {/* conversas recentes */}
      <div className="border-b border-bg-border">
        <div className="flex items-center justify-between px-3 py-1.5">
          <span className="text-2xs font-medium uppercase tracking-wider text-fg-dim">
            Conversas
          </span>
        </div>
        <div className="max-h-48 overflow-y-auto px-2 pb-2">
          <RecentSessions />
        </div>
      </div>

      {/* navegacao */}
      <nav className="flex-1 min-h-0 overflow-y-auto px-2 pb-2">
        <ul className="space-y-0.5">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = currentView === item.id;
            return (
              <li key={item.id}>
                <button
                  onClick={() => setCurrentView(item.id)}
                  className={cn(
                    'flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors',
                    active
                      ? 'bg-accent/15 text-accent-soft'
                      : 'text-fg-muted hover:bg-bg-hover hover:text-fg-base'
                  )}
                >
                  <Icon size={14} className={active ? 'text-accent-soft' : ''} />
                  <span>{item.label}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* status */}
      <div className="border-t border-bg-border p-3">
        <div className="flex items-center gap-2 text-2xs text-fg-muted">
          <Circle
            size={6}
            className="fill-state-success text-state-success animate-pulse-dot"
          />
          <span>Sistema ativo</span>
        </div>
      </div>
    </aside>
  );
}

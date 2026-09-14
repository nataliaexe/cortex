import { useEffect } from 'react';
import { PanelRight } from 'lucide-react';
import { Sidebar } from '@/components/layout/Sidebar';
import { ContextPanel } from '@/components/layout/ContextPanel';
import { ChatView } from '@/components/views/ChatView';
import { CalendarView } from '@/components/views/CalendarView';
import { NotesView } from '@/components/views/NotesView';
import { MemoryView } from '@/components/views/MemoryView';
import { AuditView } from '@/components/views/AuditView';
import { SettingsView } from '@/components/views/SettingsView';
import { useApp } from '@/store/app';
import { ToastContainer } from '@/components/ui/Toast';

export default function App() {
  const { currentView, rightPanelOpen, toggleRightPanel, setCurrentView } = useApp();

  // atalhos de teclado
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (!e.ctrlKey && !e.metaKey) return;
      if (e.key === 'b' || e.key === 'B') {
        e.preventDefault();
        toggleRightPanel();
      }
      const viewMap: Record<string, any> = {
        '1': 'chat', '2': 'calendar', '3': 'notes',
        '4': 'memory', '5': 'audit', '6': 'settings',
      };
      if (viewMap[e.key]) {
        e.preventDefault();
        setCurrentView(viewMap[e.key]);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [toggleRightPanel, setCurrentView]);

  const renderView = () => {
    switch (currentView) {
      case 'chat': return <ChatView />;
      case 'calendar': return <CalendarView />;
      case 'notes': return <NotesView />;
      case 'memory': return <MemoryView />;
      case 'audit': return <AuditView />;
      case 'settings': return <SettingsView />;
      default: return <ChatView />;
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-bg-base">
      <Sidebar />

      <main className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-12 shrink-0 items-center border-b border-bg-border bg-bg-panel px-4">
          <div className="text-sm font-medium capitalize text-fg-base">
            {currentView}
          </div>
          {!rightPanelOpen && (
            <button
              onClick={toggleRightPanel}
              className="ml-auto rounded p-1.5 text-fg-muted hover:bg-bg-hover hover:text-fg-base"
              title="Abrir painel de contexto"
            >
              <PanelRight size={14} />
            </button>
          )}
        </header>

        <div className="flex-1 overflow-hidden">
          {renderView()}
        </div>
      </main>

      {rightPanelOpen && <ContextPanel />}
      <ToastContainer />
    </div>
  );
}

import { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, Mic, Square } from 'lucide-react';
import { useChat } from '@/hooks/useChat';
import { useApp } from '@/store/app';
import { MessageBubble } from '@/components/chat/MessageBubble';
import { ModeSelector } from '@/components/chat/ModeSelector';

export function ChatView() {
  const [input, setInput] = useState('');
  const [mode, setMode] = useState('default');
  const { messages, isStreaming, send, stop, clear } = useChat();
  const sessionId = useApp().sessionId;
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // auto-scroll para o final quando chega nova mensagem
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // quando muda de sessao, garante scroll pro fim depois de carregar
  useEffect(() => {
    const t = setTimeout(() => {
      if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      }
    }, 100);
    return () => clearTimeout(t);
  }, [sessionId ?? 'new']);

  const handleSend = () => {
    if (!input.trim() || isStreaming) return;
    send(input, mode);
    setInput('');
  };

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // auto-resize do textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 200) + 'px';
  }, [input]);

  return (
    <div className="flex h-full flex-col">
      {/* barra superior com modo */}
      <div className="flex shrink-0 items-center justify-end gap-2 border-b border-bg-border px-4 py-1.5">
        <ModeSelector value={mode} onChange={setMode} />
      </div>

      {/* area de mensagens */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="mx-auto flex max-w-3xl flex-col items-center justify-center py-24 text-center">
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-accent/15">
              <span className="text-xl text-accent-soft">C</span>
            </div>
            <h2 className="text-lg font-medium text-fg-base">
              Como posso ajudar?
            </h2>
            <p className="mt-1 max-w-md text-sm text-fg-muted">
              Pergunte qualquer coisa. Posso controlar seu PC, gerenciar
              calendario, fazer pesquisa aprofundada e codar junto com voce.
            </p>
          </div>
        ) : (
          <>
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}
            <div className="h-4" />
          </>
        )}
      </div>

      {/* input */}
      <div className="border-t border-bg-border p-3">
        <div className="mx-auto max-w-3xl">
          <div className="flex items-end gap-2 rounded-lg border border-bg-border bg-bg-elevated p-1.5 focus-within:border-accent transition-colors">
            <button
              className="btn-ghost p-1.5"
              title="Anexar arquivo"
              type="button"
            >
              <Paperclip size={14} />
            </button>

            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Envie uma mensagem..."
              className="max-h-[200px] flex-1 resize-none bg-transparent px-2 py-1.5 text-sm text-fg-base placeholder:text-fg-dim focus:outline-none"
              rows={1}
              disabled={isStreaming}
            />

            <button
              className="btn-ghost p-1.5"
              title="Voz"
              type="button"
            >
              <Mic size={14} />
            </button>

            {isStreaming ? (
              <button
                onClick={stop}
                className="btn-outline p-1.5"
                title="Parar"
                type="button"
              >
                <Square size={14} />
              </button>
            ) : (
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className="btn-primary p-1.5 disabled:opacity-40 disabled:cursor-not-allowed"
                title="Enviar"
                type="button"
              >
                <Send size={14} />
              </button>
            )}
          </div>

          <div className="mt-1.5 flex items-center justify-between text-2xs text-fg-dim">
            <span>Enter envia, Shift+Enter quebra linha</span>
            {messages.length > 0 && (
              <button onClick={clear} className="hover:text-fg-muted transition-colors">
                limpar conversa
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

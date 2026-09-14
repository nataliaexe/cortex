import { useState, useRef, useCallback, useEffect } from 'react';
import {
  streamChat,
  fetchMessages,
  type ChatResponse,
  type ToolCall as ApiToolCall,
  type PlanStep,
  type DecisionEvent,
} from '@/lib/api';
import type {
  ChatMessageDisplay,
  ToolCallDisplay,
  PlanStepDisplay,
} from '@/types/chat';
import { useApp } from '@/store/app';
import { useChatStore } from '@/store/chat';
import { useLiveContext } from '@/store/context';

let idCounter = 0;
function nextId(prefix = 'msg'): string {
  idCounter += 1;
  return `${prefix}_${Date.now()}_${idCounter}`;
}

export function useChat() {
  const { sessionId, setSessionId } = useApp();
  const {
    messages,
    setMessages,
    appendMessage,
    updateMessage,
    clear: clearMessages,
    loadedForSession,
    setLoadedForSession,
  } = useChatStore();
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const live = useLiveContext();
  const cancelRef = useRef<(() => void) | null>(null);
  const loadedRef = useRef(false);

  // Carrega mensagens do backend quando muda de sessao
  useEffect(() => {
    if (!sessionId) {
      // nova conversa em branco
      if (messages.length > 0 && loadedForSession !== null) {
        clearMessages();
      }
      setLoadedForSession(null);
      return;
    }

    // ja carregada nesta sessao
    if (loadedForSession === sessionId && loadedRef.current) return;

    // senao, busca no backend
    let cancelled = false;
    (async () => {
      try {
        const msgs = await fetchMessages(sessionId);
        if (cancelled) return;
        const display: ChatMessageDisplay[] = msgs.map((m) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          createdAt: m.created_at,
        }));
        setMessages(display);
        setLoadedForSession(sessionId);
        loadedRef.current = true;
      } catch (e) {
        if (!cancelled) {
          console.warn('falha ao carregar mensagens:', e);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  const stop = useCallback(() => {
    if (cancelRef.current) {
      cancelRef.current();
      cancelRef.current = null;
    }
    setIsStreaming(false);
    live.setStreaming(false);
  }, [live]);

  const send = useCallback(
    (text: string, mode: string = 'default') => {
      const trimmed = text.trim();
      if (!trimmed || isStreaming) return;

      setError(null);
      live.reset();
      live.setStreaming(true);

      const userMsg: ChatMessageDisplay = {
        id: nextId('user'),
        role: 'user',
        content: trimmed,
        createdAt: new Date().toISOString(),
      };

      const assistantId = nextId('asst');
      const assistantMsg: ChatMessageDisplay = {
        id: assistantId,
        role: 'assistant',
        content: '',
        createdAt: new Date().toISOString(),
        streaming: true,
        toolCalls: [],
        plan: [],
      };

      appendMessage(userMsg);
      appendMessage(assistantMsg);
      setIsStreaming(true);

      const update = (updater: (m: ChatMessageDisplay) => ChatMessageDisplay) => {
        updateMessage(assistantId, updater);
      };

      cancelRef.current = streamChat(
        { message: trimmed, session_id: sessionId ?? undefined, mode, stream: true },
        {
          onSession: (sid) => {
            if (!sessionId) {
              setSessionId(sid);
              setLoadedForSession(sid);
              loadedRef.current = true;
            }
          },

          onPlan: (steps: PlanStep[]) => {
            const display: PlanStepDisplay[] = steps.map((s) => ({
              description: s.description,
              tool: s.tool,
              done: s.done,
            }));
            update((m) => ({ ...m, plan: display }));
            live.setPlan(display);
          },

          onDecision: (data: DecisionEvent) => {
            if (data.tool && data.decision) {
              update((m) => {
                const calls = [...(m.toolCalls || [])];
                const idx = calls.findIndex(
                  (c) => c.tool === data.tool && c.status === 'running'
                );
                if (idx >= 0) {
                  calls[idx] = {
                    ...calls[idx],
                    status: data.decision === 'deny' ? 'denied' : 'running',
                    error: data.reason,
                  };
                } else {
                  calls.push({
                    id: nextId('tc'),
                    tool: data.tool!,
                    args: {},
                    status: data.decision === 'deny' ? 'denied' : 'running',
                    error: data.reason,
                  });
                }
                live.setToolCalls(calls);
                return { ...m, toolCalls: calls };
              });
            }
          },

          onToolResult: (data: ApiToolCall) => {
            update((m) => {
              const calls = [...(m.toolCalls || [])];
              const idx = calls.findIndex(
                (c) => c.tool === data.tool && c.status === 'running'
              );
              const updated: ToolCallDisplay = {
                id: idx >= 0 ? calls[idx].id : nextId('tc'),
                tool: data.tool,
                args: data.args || {},
                status: data.ok ? 'ok' : 'error',
                output: data.output,
                error: data.error ?? undefined,
              };
              if (idx >= 0) calls[idx] = updated;
              else calls.push(updated);
              live.setToolCalls(calls);
              return { ...m, toolCalls: calls };
            });
          },

          onToken: (text: string) => {
            update((m) => ({ ...m, content: m.content + text }));
            live.appendToken(Math.ceil(text.length / 4));
          },

          onDone: (data: ChatResponse) => {
            const calls = (data.tool_calls || []).map((tc) => ({
              id: nextId('tc'),
              tool: tc.tool,
              args: tc.args || {},
              status: (tc.ok ? 'ok' : 'error') as ToolCallDisplay['status'],
              output: tc.output,
              error: tc.error ?? undefined,
            }));
            update((m) => ({
              ...m,
              content: data.text,
              streaming: false,
              provider: data.provider,
              model: data.model,
              wasMultiIntent: data.was_multi_intent,
              toolCalls: calls,
            }));
            live.setProvider(data.provider, data.model);
            live.setToolCalls(calls);
            setIsStreaming(false);
            live.setStreaming(false);
            cancelRef.current = null;
          },

          onError: (msg) => {
            update((m) => ({ ...m, streaming: false, error: msg }));
            setError(msg);
            setIsStreaming(false);
            live.setStreaming(false);
            cancelRef.current = null;
          },
        }
      );
    },
    [isStreaming, sessionId, setSessionId, live, appendMessage, updateMessage, setLoadedForSession]
  );

  const clear = useCallback(() => {
    stop();
    clearMessages();
    setError(null);
    setSessionId(null);
    live.reset();
  }, [stop, setSessionId, live, clearMessages]);

  return { messages, isStreaming, error, send, stop, clear };
}

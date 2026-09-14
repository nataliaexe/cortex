import { User, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ChatMessageDisplay } from '@/types/chat';
import { ToolCallBlock } from './ToolCallBlock';
import { PlanBlock } from './PlanBlock';

interface Props {
  message: ChatMessageDisplay;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user';

  // usuario: alinhado a direita, bolha compacta
  if (isUser) {
    return (
      <div className="animate-fade-in py-2">
        <div className="mx-auto flex max-w-3xl justify-end px-4">
          <div className="max-w-[70%]">
            <div className="rounded-2xl rounded-br-md bg-accent/15 px-3.5 py-2 text-[14px] leading-relaxed text-fg-base">
              <div className="whitespace-pre-wrap">{message.content}</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // cortex: alinhado a esquerda, sem bolha, mais espaco
  return (
    <div className="animate-fade-in py-3">
      <div className="mx-auto flex max-w-3xl gap-3 px-4">
        {/* avatar */}
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded bg-accent/15 text-accent-soft">
          <Sparkles size={14} />
        </div>

        {/* conteudo */}
        <div className="min-w-0 flex-1">
          {/* role + metadados */}
          <div className="mb-1.5 flex items-center gap-2 text-[11px] text-fg-dim">
            <span className="font-medium">Cortex</span>
            {message.provider && (
              <span className="font-mono">
                {message.provider}:{message.model}
              </span>
            )}
            {message.wasMultiIntent && (
              <span className="badge-info">multi</span>
            )}
          </div>

          {/* plano */}
          {message.plan && message.plan.length > 0 && (
            <PlanBlock steps={message.plan} />
          )}

          {/* tool calls */}
          {message.toolCalls && message.toolCalls.length > 0 && (
            <div className="my-2 space-y-1">
              {message.toolCalls.map((tc) => (
                <ToolCallBlock key={tc.id} call={tc} />
              ))}
            </div>
          )}

          {/* texto */}
          {message.content && (
            <div className="whitespace-pre-wrap text-[14px] leading-relaxed text-fg-base">
              {message.content}
            </div>
          )}

          {/* cursor de streaming */}
          {message.streaming && !message.content && (
            <div className="text-[13px] text-fg-dim">pensando...</div>
          )}
          {message.streaming && message.content && (
            <span className="ml-0.5 inline-block h-3.5 w-1 animate-pulse-dot bg-accent-soft align-middle" />
          )}

          {/* erro */}
          {message.error && (
            <div className="mt-2 rounded border border-state-danger/30 bg-state-danger/10 p-2 text-[12px] text-state-danger">
              {message.error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

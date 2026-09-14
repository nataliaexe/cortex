import { Check, Circle } from 'lucide-react';
import type { PlanStepDisplay } from '@/types/chat';

interface Props {
  steps: PlanStepDisplay[];
}

export function PlanBlock({ steps }: Props) {
  if (steps.length === 0) return null;
  return (
    <div className="my-2 rounded border border-bg-border bg-bg-panel p-2">
      <div className="mb-1.5 text-2xs font-medium uppercase tracking-wider text-fg-dim">
        Plano
      </div>
      <ul className="space-y-1">
        {steps.map((s, i) => (
          <li key={i} className="flex items-start gap-2 text-xs">
            {s.done ? (
              <Check size={12} className="mt-0.5 shrink-0 text-state-success" />
            ) : (
              <Circle size={12} className="mt-0.5 shrink-0 text-fg-dim" />
            )}
            <span className="text-fg-base">{s.description}</span>
            {s.tool && (
              <span className="ml-auto shrink-0 font-mono text-2xs text-fg-dim">
                {s.tool}
              </span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

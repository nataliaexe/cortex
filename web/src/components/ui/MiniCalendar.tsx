import { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Props {
  value: string; // 'YYYY-MM-DD'
  onChange: (date: string) => void;
}

const MONTHS = [
  'Janeiro', 'Fevereiro', 'Marco', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
];
const WEEKDAYS = ['D', 'S', 'T', 'Q', 'Q', 'S', 'S'];

function todayISO(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

export function MiniCalendar({ value, onChange }: Props) {
  const initial = value ? new Date(value + 'T00:00:00') : new Date();
  const [viewYear, setViewYear] = useState(initial.getFullYear());
  const [viewMonth, setViewMonth] = useState(initial.getMonth());

  const firstDay = new Date(viewYear, viewMonth, 1);
  const lastDay = new Date(viewYear, viewMonth + 1, 0);
  const daysInMonth = lastDay.getDate();
  const startWeekday = firstDay.getDay(); // 0=domingo

  const cells: (string | null)[] = [];
  for (let i = 0; i < startWeekday; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) {
    const iso = `${viewYear}-${String(viewMonth + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    cells.push(iso);
  }
  // preenche o resto da ultima semana com null
  while (cells.length % 7 !== 0) cells.push(null);

  const prevMonth = () => {
    if (viewMonth === 0) {
      setViewMonth(11);
      setViewYear(viewYear - 1);
    } else setViewMonth(viewMonth - 1);
  };
  const nextMonth = () => {
    if (viewMonth === 11) {
      setViewMonth(0);
      setViewYear(viewYear + 1);
    } else setViewMonth(viewMonth + 1);
  };

  const today = todayISO();

  return (
    <div className="w-[260px] select-none rounded border border-bg-border bg-bg-panel p-3">
      {/* header */}
      <div className="mb-2 flex items-center justify-between">
        <button
          onClick={prevMonth}
          className="rounded p-1 text-fg-muted hover:bg-bg-hover hover:text-fg-base"
          type="button"
        >
          <ChevronLeft size={14} />
        </button>
        <div className="text-sm font-medium text-fg-base">
          {MONTHS[viewMonth]} {viewYear}
        </div>
        <button
          onClick={nextMonth}
          className="rounded p-1 text-fg-muted hover:bg-bg-hover hover:text-fg-base"
          type="button"
        >
          <ChevronRight size={14} />
        </button>
      </div>

      {/* weekday header */}
      <div className="mb-1 grid grid-cols-7 gap-0.5">
        {WEEKDAYS.map((w, i) => (
          <div key={i} className="text-center text-2xs font-medium text-fg-dim">
            {w}
          </div>
        ))}
      </div>

      {/* days */}
      <div className="grid grid-cols-7 gap-0.5">
        {cells.map((iso, i) => {
          if (iso === null) return <div key={i} />;
          const selected = iso === value;
          const isToday = iso === today;
          return (
            <button
              key={i}
              onClick={() => onChange(iso)}
              type="button"
              className={cn(
                'flex h-8 items-center justify-center rounded text-xs transition-colors',
                selected
                  ? 'bg-accent text-white font-medium'
                  : isToday
                  ? 'bg-bg-hover text-accent-soft font-medium'
                  : 'text-fg-base hover:bg-bg-hover'
              )}
            >
              {Number(iso.slice(8, 10))}
            </button>
          );
        })}
      </div>

      {/* quick actions */}
      <div className="mt-2 flex gap-1 border-t border-bg-border pt-2">
        <button
          onClick={() => onChange(todayISO())}
          className="flex-1 rounded bg-bg-hover px-2 py-1 text-2xs text-fg-muted hover:bg-bg-elevated hover:text-fg-base"
          type="button"
        >
          Hoje
        </button>
        <button
          onClick={() => {
            const t = new Date();
            t.setDate(t.getDate() + 1);
            onChange(`${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, '0')}-${String(t.getDate()).padStart(2, '0')}`);
          }}
          className="flex-1 rounded bg-bg-hover px-2 py-1 text-2xs text-fg-muted hover:bg-bg-elevated hover:text-fg-base"
          type="button"
        >
          Amanha
        </button>
      </div>
    </div>
  );
}

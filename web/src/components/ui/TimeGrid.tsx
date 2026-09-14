import { useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';

interface Props {
  value: string; // 'HH:MM'
  onChange: (time: string) => void;
}

const HOURS = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0'));
const MINUTES = Array.from({ length: 60 }, (_, i) => String(i).padStart(2, '0'));

/**
 * Seletor de hora estilo alarme: duas colunas rolaveis (hora e minuto),
 * com o item selecionado destacado no centro. Scroll snap para a selecao.
 */
export function TimeGrid({ value, onChange }: Props) {
  const [hh = '00', mm = '00'] = value.split(':');

  const hoursRef = useRef<HTMLDivElement>(null);
  const minutesRef = useRef<HTMLDivElement>(null);

  const ITEM_HEIGHT = 40; // altura de cada item

  // scroll para o item selecionado quando muda externamente
  useEffect(() => {
    const el = hoursRef.current;
    if (!el) return;
    const idx = Number(hh);
    el.scrollTo({ top: idx * ITEM_HEIGHT, behavior: 'smooth' });
  }, [hh]);

  useEffect(() => {
    const el = minutesRef.current;
    if (!el) return;
    const idx = Number(mm);
    el.scrollTo({ top: idx * ITEM_HEIGHT, behavior: 'smooth' });
  }, [mm]);

  // detecta item mais proximo do centro ao parar de rolar
  const handleHourScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const el = e.currentTarget;
    const idx = Math.round(el.scrollTop / ITEM_HEIGHT);
    const clamped = Math.max(0, Math.min(23, idx));
    const newH = String(clamped).padStart(2, '0');
    if (newH !== hh) onChange(`${newH}:${mm}`);
  };

  const handleMinuteScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const el = e.currentTarget;
    const idx = Math.round(el.scrollTop / ITEM_HEIGHT);
    const clamped = Math.max(0, Math.min(59, idx));
    const newM = String(clamped).padStart(2, '0');
    if (newM !== mm) onChange(`${hh}:${newM}`);
  };

  const snapTo = (which: 'h' | 'm', direction: 1 | -1) => {
    if (which === 'h') {
      const cur = Number(hh);
      const next = (cur + direction + 24) % 24;
      onChange(`${String(next).padStart(2, '0')}:${mm}`);
    } else {
      const cur = Number(mm);
      const next = (cur + direction + 60) % 60;
      onChange(`${hh}:${String(next).padStart(2, '0')}`);
    }
  };

  return (
    <div className="rounded border border-bg-border bg-bg-panel">
      {/* display grande */}
      <div className="border-b border-bg-border px-3 py-3 text-center">
        <span className="font-mono text-2xl font-medium text-accent-soft">
          {hh}:{mm}
        </span>
      </div>

      {/* seletor de roda */}
      <div className="relative flex justify-center">
        {/* indicador central */}
        <div
          className="pointer-events-none absolute left-0 right-0 top-1/2 z-10 -translate-y-1/2 border-y border-accent/50"
          style={{ height: ITEM_HEIGHT }}
        />

        {/* gradientes de topo/base (fade) */}
        <div className="pointer-events-none absolute inset-x-0 top-0 z-20 h-16 bg-gradient-to-b from-bg-panel to-transparent" />
        <div className="pointer-events-none absolute inset-x-0 bottom-0 z-20 h-16 bg-gradient-to-t from-bg-panel to-transparent" />

        {/* horas */}
        <div className="relative flex flex-col items-center border-r border-bg-border px-4">
          <button
            onClick={() => snapTo('h', -1)}
            type="button"
            className="mb-1 text-fg-dim hover:text-fg-base"
            tabIndex={-1}
          >
            <svg width="12" height="8" viewBox="0 0 12 8" fill="none">
              <path d="M1 7L6 1L11 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </button>

          <div
            ref={hoursRef}
            onScroll={handleHourScroll}
            className="no-scrollbar h-[240px] overflow-y-auto"
            style={{
              scrollSnapType: 'y mandatory',
              scrollBehavior: 'smooth',
            }}
          >
            <div style={{ height: 100 }} />
            {HOURS.map((h) => {
              const selected = h === hh;
              return (
                <div
                  key={h}
                  className={cn(
                    'flex cursor-pointer items-center justify-center font-mono transition-colors',
                    selected
                      ? 'text-xl font-medium text-accent-soft'
                      : 'text-md text-fg-dim hover:text-fg-muted'
                  )}
                  style={{ height: ITEM_HEIGHT, scrollSnapAlign: 'center' }}
                  onClick={() => onChange(`${h}:${mm}`)}
                >
                  {h}
                </div>
              );
            })}
            <div style={{ height: 100 }} />
          </div>

          <button
            onClick={() => snapTo('h', 1)}
            type="button"
            className="mt-1 text-fg-dim hover:text-fg-base"
            tabIndex={-1}
          >
            <svg width="12" height="8" viewBox="0 0 12 8" fill="none">
              <path d="M1 1L6 7L11 1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        {/* minutos */}
        <div className="relative flex flex-col items-center border-l border-bg-border px-4">
          <button
            onClick={() => snapTo('m', -1)}
            type="button"
            className="mb-1 text-fg-dim hover:text-fg-base"
            tabIndex={-1}
          >
            <svg width="12" height="8" viewBox="0 0 12 8" fill="none">
              <path d="M1 7L6 1L11 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </button>

          <div
            ref={minutesRef}
            onScroll={handleMinuteScroll}
            className="no-scrollbar h-[240px] overflow-y-auto"
            style={{
              scrollSnapType: 'y mandatory',
              scrollBehavior: 'smooth',
            }}
          >
            <div style={{ height: 100 }} />
            {MINUTES.map((m) => {
              const selected = m === mm;
              return (
                <div
                  key={m}
                  className={cn(
                    'flex cursor-pointer items-center justify-center font-mono transition-colors',
                    selected
                      ? 'text-xl font-medium text-accent-soft'
                      : 'text-md text-fg-dim hover:text-fg-muted'
                  )}
                  style={{ height: ITEM_HEIGHT, scrollSnapAlign: 'center' }}
                  onClick={() => onChange(`${hh}:${m}`)}
                >
                  {m}
                </div>
              );
            })}
            <div style={{ height: 100 }} />
          </div>

          <button
            onClick={() => snapTo('m', 1)}
            type="button"
            className="mt-1 text-fg-dim hover:text-fg-base"
            tabIndex={-1}
          >
            <svg width="12" height="8" viewBox="0 0 12 8" fill="none">
              <path d="M1 1L6 7L11 1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

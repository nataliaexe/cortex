import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Calendar, Plus, RefreshCw, Trash2, Clock, MapPin, X, AlertTriangle, Repeat, XCircle } from 'lucide-react';
import {
  fetchCalendarEvents,
  createCalendarEvent,
  deleteCalendarEvent,
  syncCalendar,
  type CalendarEvent,
  type OverlapWarning,
} from '@/lib/api';
import { cn } from '@/lib/utils';
import { MiniCalendar } from '@/components/ui/MiniCalendar';
import { useToast } from '@/components/ui/Toast';
import { TimeGrid } from '@/components/ui/TimeGrid';

type Range = 'hoje' | 'amanha' | 'semana' | 'mes';

export function CalendarView() {
  const [range, setRange] = useState<Range>('semana');
  const [showForm, setShowForm] = useState(false);
  const qc = useQueryClient();

  const eventsQ = useQuery({
    queryKey: ['calendar', range],
    queryFn: () => fetchCalendarEvents(range),
  });

  const syncM = useMutation({
    mutationFn: () => syncCalendar(30),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['calendar'] });
      toast.push({
        kind: 'success',
        title: `${data.total} eventos sincronizados`,
        description: `${data.inserted} novos, ${data.updated} atualizados`,
      });
    },
    onError: (e: Error) => toast.push({ kind: 'error', title: 'Erro ao sincronizar', description: e.message }),
  });

  const toast = useToast();
  const deleteM = useMutation({
    mutationFn: (id: string) => deleteCalendarEvent(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['calendar'] });
      toast.push({ kind: 'success', title: 'Evento removido' });
    },
    onError: (e: Error) => toast.push({ kind: 'error', title: 'Erro ao remover', description: e.message }),
  });

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-bg-border px-4 py-2">
        <div className="flex items-center gap-1">
          {(['hoje', 'amanha', 'semana', 'mes'] as Range[]).map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={cn(
                'rounded px-2 py-1 text-xs transition-colors',
                range === r
                  ? 'bg-accent/15 text-accent-soft'
                  : 'text-fg-muted hover:bg-bg-hover hover:text-fg-base'
              )}
            >
              {r}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => syncM.mutate()}
            disabled={syncM.isPending}
            className="btn-ghost text-xs"
          >
            <RefreshCw size={12} className={syncM.isPending ? 'animate-spin' : ''} />
            <span>Sincronizar</span>
          </button>
          <button onClick={() => setShowForm(!showForm)} className="btn-primary text-xs">
            {showForm ? <X size={12} /> : <Plus size={12} />}
            <span>{showForm ? 'Fechar' : 'Novo evento'}</span>
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* form lateral (quando aberto) */}
        {showForm && (
          <div className="w-[520px] shrink-0 overflow-y-auto border-r border-bg-border bg-bg-panel">
            <NewEventForm
              onClose={() => setShowForm(false)}
              onCreated={() => {
                qc.invalidateQueries({ queryKey: ['calendar'] });
                setShowForm(false);
              }}
            />
          </div>
        )}

        {/* lista */}
        <div className="flex-1 overflow-y-auto">
          {eventsQ.isLoading && (
            <div className="p-8 text-center text-sm text-fg-dim">Carregando...</div>
          )}
          {eventsQ.data && eventsQ.data.length === 0 && (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <Calendar size={24} className="mb-2 text-fg-dim" />
              <div className="text-sm text-fg-muted">Nenhum evento em {range}</div>
              <div className="mt-1 text-2xs text-fg-dim">
                Crie um novo ou sincronize com o Google
              </div>
            </div>
          )}
          {eventsQ.data && eventsQ.data.length > 0 && (
            <div className="mx-auto max-w-3xl p-4">
              {eventsQ.data.map((ev, i) => (
                <EventCard
                  key={`${ev.id}_${ev.start_at}_${i}`}
                  event={ev}
                  onDelete={() => deleteM.mutate(ev.id)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function EventCard({ event, onDelete }: { event: CalendarEvent; onDelete: () => void }) {
  const [confirming, setConfirming] = useState(false);
  const start = new Date(event.start_at);
  const end = new Date(event.end_at);
  const dayLabel = start.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', weekday: 'short' }).replace('.', '');
  const timeLabel = `${start.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })} - ${end.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`;

  const recurrenceLabel = {
    daily: 'diario',
    weekdays: 'seg-sex',
    weekly: 'semanal',
    custom: 'custom',
  }[event.recurrence] || null;

  return (
    <div className="group mb-2 rounded border border-bg-border bg-bg-panel p-3 transition-colors hover:border-accent/40">
      <div className="flex items-start gap-3">
        <div className="flex w-16 shrink-0 flex-col items-center rounded bg-bg-elevated py-1.5 text-center">
          <span className="text-2xs uppercase text-fg-dim">{dayLabel}</span>
          <span className="text-md font-medium text-fg-base">
            {start.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-medium text-fg-base">{event.title}</h3>
            {event.source === 'google' && <span className="badge-info">Google</span>}
            {recurrenceLabel && (
              <span className="badge-muted flex items-center gap-1">
                <Repeat size={8} />
                {recurrenceLabel}
              </span>
            )}
          </div>

          <div className="mt-1 flex items-center gap-3 text-2xs text-fg-muted">
            <span className="flex items-center gap-1">
              <Clock size={10} />
              {timeLabel}
            </span>
            {event.location && (
              <span className="flex items-center gap-1">
                <MapPin size={10} />
                {event.location}
              </span>
            )}
          </div>

          {event.description && (
            <p className="mt-1 text-2xs text-fg-dim line-clamp-2">{event.description}</p>
          )}
        </div>

        <div className="opacity-0 transition-opacity group-hover:opacity-100">
          {confirming ? (
            <div className="flex items-center gap-1">
              <button
                onClick={onDelete}
                className="rounded bg-state-danger/20 px-2 py-0.5 text-2xs text-state-danger hover:bg-state-danger/30"
              >
                Confirmar
              </button>
              <button
                onClick={() => setConfirming(false)}
                className="rounded px-2 py-0.5 text-2xs text-fg-dim hover:bg-bg-hover"
              >
                Cancelar
              </button>
            </div>
          ) : (
            <button
              onClick={() => setConfirming(true)}
              className="rounded p-1 text-fg-dim hover:bg-bg-hover hover:text-state-danger"
              title="Remover"
            >
              <Trash2 size={12} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------- FORM ----------------

const DURATIONS = [
  { label: '15min', value: 15 },
  { label: '30min', value: 30 },
  { label: '1h', value: 60 },
  { label: '1h30', value: 90 },
  { label: '2h', value: 120 },
  { label: '3h', value: 180 },
  { label: '4h', value: 240 },
];

const RECURRENCES = [
  { label: 'Unica', value: 'none' },
  { label: 'Diaria', value: 'daily' },
  { label: 'Seg-Sex', value: 'weekdays' },
  { label: 'Semanal', value: 'weekly' },
  { label: 'Custom', value: 'custom' },
];

const WEEKDAY_LABELS = ['D', 'S', 'T', 'Q', 'Q', 'S', 'S'];

function todayISO(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function NewEventForm({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [title, setTitle] = useState('');
  const [date, setDate] = useState(todayISO());
  const [time, setTime] = useState('09:00');
  const [duration, setDuration] = useState(60);
  const [location, setLocation] = useState('');
  const [description, setDescription] = useState('');
  const [recurrence, setRecurrence] = useState('none');
  const [customDays, setCustomDays] = useState<number[]>([]);
  const [recurrenceUntil, setRecurrenceUntil] = useState('');
  const [overlaps, setOverlaps] = useState<OverlapWarning[]>([]);

  const m = useMutation({
    mutationFn: () =>
      createCalendarEvent({
        title,
        start: `${date} ${time}`,
        duration_minutes: duration,
        location: location || undefined,
        description: description || undefined,
        recurrence,
        recurrence_days: recurrence === 'custom' ? customDays : undefined,
        recurrence_until: recurrence !== 'none' && recurrenceUntil ? recurrenceUntil : undefined,
      }),
    onSuccess: (data) => {
      if (data.overlaps && data.overlaps.length > 0) {
        setOverlaps(data.overlaps);
        return;
      }
      onCreated();
    },
    // erro ja aparece inline, mas o toast tambem avisa
  });

  const toggleDay = (day: number) => {
    setCustomDays((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day].sort()
    );
  };

  const canSubmit =
    title.trim().length > 0 &&
    (recurrence !== 'custom' || customDays.length > 0);

  // resumo
  const summary = useMemo(() => {
    const d = new Date(date + 'T00:00:00');
    const dLabel = d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', weekday: 'long' });
    return `${dLabel} as ${time}, ${duration}min${
      recurrence !== 'none' ? ` (${RECURRENCES.find((r) => r.value === recurrence)?.label})` : ''
    }`;
  }, [date, time, duration, recurrence]);

  return (
    <div className="p-4">
      <h2 className="mb-4 text-md font-medium text-fg-base">Novo evento</h2>

      <div className="space-y-4">
        <div>
          <label className="mb-1 block text-2xs uppercase tracking-wider text-fg-dim">
            Titulo
          </label>
          <input
            className="input"
            placeholder="Reuniao com equipe"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            autoFocus
          />
        </div>

        <div>
          <label className="mb-1 block text-2xs uppercase tracking-wider text-fg-dim">
            Data
          </label>
          <MiniCalendar value={date} onChange={setDate} />
        </div>

        <div>
          <label className="mb-1 block text-2xs uppercase tracking-wider text-fg-dim">
            Hora
          </label>
          <TimeGrid value={time} onChange={setTime} />
        </div>

        <div>
          <label className="mb-1 block text-2xs uppercase tracking-wider text-fg-dim">
            Duracao
          </label>
          <div className="flex flex-wrap gap-1">
            {DURATIONS.map((d) => (
              <button
                key={d.value}
                onClick={() => setDuration(d.value)}
                type="button"
                className={cn(
                  'rounded border px-2.5 py-1 text-xs transition-colors',
                  duration === d.value
                    ? 'border-accent bg-accent/15 text-accent-soft'
                    : 'border-bg-border text-fg-muted hover:bg-bg-hover hover:text-fg-base'
                )}
              >
                {d.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="mb-1 block text-2xs uppercase tracking-wider text-fg-dim">
            Recorrencia
          </label>
          <div className="flex flex-wrap gap-1">
            {RECURRENCES.map((r) => (
              <button
                key={r.value}
                onClick={() => setRecurrence(r.value)}
                type="button"
                className={cn(
                  'rounded border px-2.5 py-1 text-xs transition-colors',
                  recurrence === r.value
                    ? 'border-accent bg-accent/15 text-accent-soft'
                    : 'border-bg-border text-fg-muted hover:bg-bg-hover hover:text-fg-base'
                )}
              >
                {r.label}
              </button>
            ))}
          </div>

          {recurrence === 'custom' && (
            <div className="mt-2 flex gap-1">
              {WEEKDAY_LABELS.map((label, i) => {
                const active = customDays.includes(i);
                return (
                  <button
                    key={i}
                    onClick={() => toggleDay(i)}
                    type="button"
                    className={cn(
                      'flex h-8 w-8 items-center justify-center rounded border text-xs transition-colors',
                      active
                        ? 'border-accent bg-accent/15 text-accent-soft'
                        : 'border-bg-border text-fg-muted hover:bg-bg-hover'
                    )}
                  >
                    {label}
                  </button>
                );
              })}
            </div>
          )}

          {recurrence !== 'none' && (
            <div className="mt-2">
              <label className="mb-1 block text-2xs uppercase tracking-wider text-fg-dim">
                Repetir ate (opcional)
              </label>
              <input
                type="date"
                className="input"
                value={recurrenceUntil}
                onChange={(e) => setRecurrenceUntil(e.target.value)}
              />
            </div>
          )}
        </div>

        <div>
          <label className="mb-1 block text-2xs uppercase tracking-wider text-fg-dim">
            Local (opcional)
          </label>
          <input
            className="input"
            placeholder="Online, escritorio..."
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          />
        </div>

        <div>
          <label className="mb-1 block text-2xs uppercase tracking-wider text-fg-dim">
            Descricao (opcional)
          </label>
          <textarea
            className="input min-h-[60px] resize-y"
            placeholder="Detalhes do evento"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>

        {/* sobreposicoes */}
        {overlaps.length > 0 && (
          <div className="rounded border border-state-warning/40 bg-state-warning/10 p-3">
            <div className="mb-2 flex items-center gap-1.5 text-xs font-medium text-state-warning">
              <AlertTriangle size={12} />
              Conflito com {overlaps.length} evento{overlaps.length > 1 ? 's' : ''}
            </div>
            {overlaps.map((o) => (
              <div key={o.with_id} className="text-2xs text-state-warning/80">
                {o.with_title} ({new Date(o.with_start).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })} - {new Date(o.with_end).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })})
              </div>
            ))}
            <div className="mt-3 flex gap-2">
              <button
                onClick={onCreated}
                className="btn-outline text-2xs"
                type="button"
              >
                Manter mesmo assim
              </button>
              <button
                onClick={() => setOverlaps([])}
                className="btn-ghost text-2xs"
                type="button"
              >
                Voltar e ajustar
              </button>
            </div>
          </div>
        )}

        <div className="rounded border border-bg-border bg-bg-elevated p-2 text-2xs text-fg-muted">
          {summary}
        </div>

        {m.isError && (
          <div className="flex items-start gap-1.5 rounded border border-state-danger/30 bg-state-danger/10 p-2 text-2xs text-state-danger">
            <XCircle size={12} className="mt-0.5 shrink-0" />
            <span>{(m.error as Error).message}</span>
          </div>
        )}

        <div className="flex items-center justify-end gap-2 border-t border-bg-border pt-3">
          <button onClick={onClose} className="btn-ghost text-xs" type="button">
            Cancelar
          </button>
          <button
            onClick={() => m.mutate()}
            disabled={!canSubmit || m.isPending || overlaps.length > 0}
            className="btn-primary text-xs disabled:opacity-40"
            type="button"
          >
            {m.isPending ? 'Criando...' : 'Criar evento'}
          </button>
        </div>
      </div>
    </div>
  );
}
